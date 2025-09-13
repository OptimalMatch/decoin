#!/bin/bash

# DeCoin Blockchain Network Stress Test Script
# This script performs comprehensive stress testing on the 8-node blockchain network

set -e

# Configuration
NODES=(11080 11081 11082 11084 11085 11086 11083 11087)
NODE_NAMES=("Node1" "Node2" "Node3" "Node4" "Node5" "Node6" "Validator1" "Validator2")
TEST_DURATION=300  # Test duration in seconds (5 minutes)
BATCH_SIZE=10      # Number of transactions per batch
BATCH_DELAY=2      # Delay between batches in seconds
CONCURRENT_USERS=5 # Number of concurrent test users

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TOTAL_TRANSACTIONS=0
SUCCESSFUL_TRANSACTIONS=0
FAILED_TRANSACTIONS=0
START_TIME=$(date +%s)
TEST_LOG="stress_test_$(date +%Y%m%d_%H%M%S).log"
declare -a PIDS

# Function to print colored output
print_status() {
    echo -e "${2}[$(date +'%H:%M:%S')] ${1}${NC}" | tee -a "$TEST_LOG"
}

# Function to check if all nodes are healthy
check_nodes_health() {
    print_status "Checking node health..." "$BLUE"
    local all_healthy=true

    for i in "${!NODES[@]}"; do
        local port=${NODES[$i]}
        local name=${NODE_NAMES[$i]}

        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_status "✓ $name (port $port) is healthy" "$GREEN"
        else
            print_status "✗ $name (port $port) is not responding" "$RED"
            all_healthy=false
        fi
    done

    if [ "$all_healthy" = false ]; then
        print_status "Not all nodes are healthy. Exiting..." "$RED"
        exit 1
    fi
}

# Function to get blockchain statistics
get_blockchain_stats() {
    local port=$1
    local stats=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null)

    if [ -n "$stats" ]; then
        local blocks=$(echo "$stats" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['blocks']))" 2>/dev/null || echo "0")
        local mempool=$(curl -s "http://localhost:$port/mempool" 2>/dev/null | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        echo "Blocks: $blocks, Mempool: $mempool"
    else
        echo "Unable to fetch stats"
    fi
}

# Function to create a transaction
create_transaction() {
    local port=$1
    local recipient=$2
    local tx_num=$3

    local response=$(curl -s -m 2 -X POST "http://localhost:$port/faucet/$recipient" 2>/dev/null)

    if [ -n "$response" ] && echo "$response" | grep -q "success.*true"; then
        return 0
    else
        echo "Failed transaction to port $port: $response" >> "$TEST_LOG"
        return 1
    fi
}

# Function to run concurrent transaction batches
run_transaction_batch() {
    batch_num=$1
    user_id=$2
    node_index=$((batch_num % ${#NODES[@]}))
    port=${NODES[$node_index]}

    echo "[$(date +'%H:%M:%S')] User $user_id: Sending batch $batch_num to port $port" >> "$TEST_LOG"

    for i in $(seq 1 $BATCH_SIZE); do
        recipient="USER_${user_id}_BATCH_${batch_num}_TX_${i}"

        if create_transaction "$port" "$recipient" "$i"; then
            echo "$user_id:$batch_num:$i:SUCCESS" >> /tmp/stress_test_results.tmp
            echo -n "."
        else
            echo "$user_id:$batch_num:$i:FAILED" >> /tmp/stress_test_results.tmp
            echo -n "x"
        fi

        # Small delay between transactions
        sleep 0.1
    done
    echo ""
}

# Function to monitor network performance
monitor_network() {
    while true; do
        clear
        print_status "=== NETWORK STATUS ===" "$YELLOW"

        for i in "${!NODES[@]}"; do
            local port=${NODES[$i]}
            local name=${NODE_NAMES[$i]}
            local stats=$(get_blockchain_stats "$port")
            printf "%-12s (:%5d): %s\n" "$name" "$port" "$stats"
        done

        # Count transactions from temp file
        if [ -f /tmp/stress_test_results.tmp ]; then
            SUCCESSFUL_TRANSACTIONS=$(grep -c "SUCCESS" /tmp/stress_test_results.tmp 2>/dev/null || echo 0)
            FAILED_TRANSACTIONS=$(grep -c "FAILED" /tmp/stress_test_results.tmp 2>/dev/null || echo 0)
            # Ensure values are not empty
            SUCCESSFUL_TRANSACTIONS=${SUCCESSFUL_TRANSACTIONS:-0}
            FAILED_TRANSACTIONS=${FAILED_TRANSACTIONS:-0}
            TOTAL_TRANSACTIONS=$((SUCCESSFUL_TRANSACTIONS + FAILED_TRANSACTIONS))
        else
            SUCCESSFUL_TRANSACTIONS=0
            FAILED_TRANSACTIONS=0
            TOTAL_TRANSACTIONS=0
        fi

        echo ""
        print_status "=== TEST STATISTICS ===" "$YELLOW"
        local current_time=$(date +%s)
        local elapsed=$((current_time - START_TIME))
        local tps=0
        if [ $elapsed -gt 0 ] && [ $SUCCESSFUL_TRANSACTIONS -gt 0 ]; then
            tps=$((SUCCESSFUL_TRANSACTIONS / elapsed))
        fi

        echo "Test Duration: ${elapsed}s / ${TEST_DURATION}s"
        echo "Total Transactions: $TOTAL_TRANSACTIONS"
        echo "Successful: $SUCCESSFUL_TRANSACTIONS"
        echo "Failed: $FAILED_TRANSACTIONS"
        if [ $TOTAL_TRANSACTIONS -gt 0 ]; then
            local success_rate=$((SUCCESSFUL_TRANSACTIONS * 100 / TOTAL_TRANSACTIONS))
            echo "Success Rate: ${success_rate}%"
        else
            echo "Success Rate: 0%"
        fi
        echo "TPS (Transactions/Second): $tps"

        sleep 5

        # Check if test duration exceeded
        if [ $elapsed -ge $TEST_DURATION ]; then
            break
        fi
    done
}

# Function to perform stress test
run_stress_test() {
    print_status "Starting stress test for $TEST_DURATION seconds..." "$GREEN"
    print_status "Creating $CONCURRENT_USERS concurrent users..." "$BLUE"

    # Clean up temp file
    rm -f /tmp/stress_test_results.tmp
    touch /tmp/stress_test_results.tmp

    # Start monitoring in background
    monitor_network &
    MONITOR_PID=$!

    # Run concurrent users
    for user in $(seq 1 $CONCURRENT_USERS); do
        echo "Starting user $user..." >> "$TEST_LOG"
        (
            batch=1
            while true; do
                current_time=$(date +%s)
                elapsed=$((current_time - START_TIME))

                if [ $elapsed -ge $TEST_DURATION ]; then
                    echo "User $user stopping after $elapsed seconds" >> "$TEST_LOG"
                    break
                fi

                run_transaction_batch $batch $user
                sleep $BATCH_DELAY
                batch=$((batch + 1))
            done
        ) &
        PIDS+=($!)
    done

    # Wait for all background jobs
    for pid in ${PIDS[@]}; do
        wait $pid
    done

    # Kill monitor
    kill $MONITOR_PID 2>/dev/null || true
}

# Function to analyze results
analyze_results() {
    print_status "\n=== FINAL RESULTS ===" "$GREEN"

    local elapsed=$(($(date +%s) - START_TIME))

    # Re-count from temp file for accurate final results
    if [ -f /tmp/stress_test_results.tmp ]; then
        SUCCESSFUL_TRANSACTIONS=$(grep -c "SUCCESS" /tmp/stress_test_results.tmp 2>/dev/null || echo 0)
        FAILED_TRANSACTIONS=$(grep -c "FAILED" /tmp/stress_test_results.tmp 2>/dev/null || echo 0)
        SUCCESSFUL_TRANSACTIONS=${SUCCESSFUL_TRANSACTIONS:-0}
        FAILED_TRANSACTIONS=${FAILED_TRANSACTIONS:-0}
        TOTAL_TRANSACTIONS=$((SUCCESSFUL_TRANSACTIONS + FAILED_TRANSACTIONS))
    fi

    echo "Test Duration: ${elapsed} seconds"
    echo "Total Transactions Attempted: $TOTAL_TRANSACTIONS"
    echo "Successful Transactions: $SUCCESSFUL_TRANSACTIONS"
    echo "Failed Transactions: $FAILED_TRANSACTIONS"

    if [ $TOTAL_TRANSACTIONS -gt 0 ]; then
        local success_rate=$(echo "scale=2; $SUCCESSFUL_TRANSACTIONS * 100 / $TOTAL_TRANSACTIONS" | bc)
        local tps=$(echo "scale=2; $SUCCESSFUL_TRANSACTIONS / $elapsed" | bc)

        echo "Success Rate: ${success_rate}%"
        echo "Average TPS: $tps"
    fi

    # Get final blockchain state
    print_status "\n=== FINAL BLOCKCHAIN STATE ===" "$BLUE"
    for i in "${!NODES[@]}"; do
        local port=${NODES[$i]}
        local name=${NODE_NAMES[$i]}
        local stats=$(get_blockchain_stats "$port")
        printf "%-12s: %s\n" "$name" "$stats"
    done

    # Check for consensus
    print_status "\n=== CONSENSUS CHECK ===" "$BLUE"
    local first_height=""
    local consensus=true

    for i in "${!NODES[@]}"; do
        local port=${NODES[$i]}
        local height=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
            python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")

        if [ -z "$first_height" ]; then
            first_height=$height
        elif [ "$height" != "$first_height" ]; then
            consensus=false
        fi
    done

    if [ "$consensus" = true ]; then
        print_status "✓ All nodes have reached consensus (height: $first_height)" "$GREEN"
    else
        print_status "✗ Nodes have different blockchain heights - consensus issue!" "$RED"
    fi
}

# Function to generate load patterns
generate_load_patterns() {
    local pattern=$1

    case $pattern in
        "burst")
            print_status "Generating BURST load pattern..." "$YELLOW"
            # Send many transactions at once
            for i in $(seq 1 100); do
                local node_port=${NODES[$((i % ${#NODES[@]}))]}
                create_transaction "$node_port" "BURST_USER_$i" "$i" &
            done
            wait
            ;;

        "sustained")
            print_status "Generating SUSTAINED load pattern..." "$YELLOW"
            # Send transactions at a steady rate
            for i in $(seq 1 100); do
                local node_port=${NODES[$((i % ${#NODES[@]}))]}
                create_transaction "$node_port" "SUSTAINED_USER_$i" "$i"
                sleep 0.5
            done
            ;;

        "random")
            print_status "Generating RANDOM load pattern..." "$YELLOW"
            # Random delays between transactions
            for i in $(seq 1 50); do
                local node_port=${NODES[$((RANDOM % ${#NODES[@]}))]}
                create_transaction "$node_port" "RANDOM_USER_$i" "$i"
                sleep $((RANDOM % 3))
            done
            ;;
    esac
}

# Main execution
main() {
    print_status "=== DeCoin Blockchain Stress Test ===" "$GREEN"
    print_status "Test Configuration:" "$BLUE"
    echo "  - Network Size: ${#NODES[@]} nodes"
    echo "  - Test Duration: $TEST_DURATION seconds"
    echo "  - Concurrent Users: $CONCURRENT_USERS"
    echo "  - Batch Size: $BATCH_SIZE transactions"
    echo "  - Batch Delay: $BATCH_DELAY seconds"
    echo "  - Log File: $TEST_LOG"
    echo ""

    # Clean up previous temp files
    rm -f /tmp/stress_test_results.tmp

    # Check if Docker containers are running
    print_status "Checking Docker containers..." "$BLUE"
    if ! docker ps | grep -q decoin; then
        print_status "DeCoin containers are not running. Please start them first." "$RED"
        exit 1
    fi

    # Check node health
    check_nodes_health

    # Get initial state
    print_status "\n=== INITIAL BLOCKCHAIN STATE ===" "$BLUE"
    for i in "${!NODES[@]}"; do
        local port=${NODES[$i]}
        local name=${NODE_NAMES[$i]}
        local stats=$(get_blockchain_stats "$port")
        printf "%-12s: %s\n" "$name" "$stats"
    done

    # Parse command line arguments
    if [ "$1" == "pattern" ]; then
        # Run specific load patterns
        generate_load_patterns "${2:-burst}"
        sleep 10
        generate_load_patterns "sustained"
        sleep 10
        generate_load_patterns "random"
    else
        # Run standard stress test
        run_stress_test
    fi

    # Wait for transactions to be mined
    print_status "\nWaiting for transactions to be mined..." "$YELLOW"
    sleep 30

    # Analyze results
    analyze_results

    print_status "\n=== STRESS TEST COMPLETED ===" "$GREEN"
    print_status "Results saved to: $TEST_LOG" "$BLUE"
}

# Handle script termination
trap 'print_status "\nTest interrupted by user" "$RED"; analyze_results; exit 1' INT TERM

# Run main function
main "$@"