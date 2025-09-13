#!/bin/bash

# Robust stress test for DeCoin network
# This version handles concurrent users properly

set -e

# Configuration
NODES=(11080 11081 11082 11084 11085 11086 11083 11087)
NODE_NAMES=("Node1" "Node2" "Node3" "Node4" "Node5" "Node6" "Validator1" "Validator2")
TEST_DURATION=${1:-60}  # Default 60 seconds, or pass as argument
CONCURRENT_USERS=3
TRANSACTIONS_PER_SECOND=2

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Files for tracking
RESULTS_FILE="/tmp/stress_results_$$.txt"
LOG_FILE="stress_test_$(date +%Y%m%d_%H%M%S).log"

# Clean up on exit
trap 'cleanup' EXIT

cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    rm -f "$RESULTS_FILE"
    # Kill any background jobs
    jobs -p | xargs -r kill 2>/dev/null || true
}

# Function to log
log() {
    echo "[$(date +'%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to send transaction
send_transaction() {
    local port=$1
    local recipient=$2
    local user=$3

    response=$(curl -s -m 2 -X POST "http://localhost:$port/faucet/$recipient" 2>/dev/null)

    if echo "$response" | grep -q "success.*true" 2>/dev/null; then
        echo "SUCCESS:$user:$(date +%s)" >> "$RESULTS_FILE"
        return 0
    else
        echo "FAILED:$user:$(date +%s)" >> "$RESULTS_FILE"
        return 1
    fi
}

# Function for user workload
user_workload() {
    local user_id=$1
    local start_time=$2
    local duration=$3

    log "User $user_id started"

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))

        if [ $elapsed -ge $duration ]; then
            log "User $user_id completed after $elapsed seconds"
            break
        fi

        # Pick a random node
        node_index=$((RANDOM % ${#NODES[@]}))
        port=${NODES[$node_index]}

        # Create unique recipient
        recipient="USER${user_id}_T$(date +%s%N)"

        # Send transaction
        send_transaction "$port" "$recipient" "$user_id" &

        # Rate limiting (simple approach without bc)
        if [ $TRANSACTIONS_PER_SECOND -eq 1 ]; then
            sleep 1
        elif [ $TRANSACTIONS_PER_SECOND -eq 2 ]; then
            sleep 0.5
        else
            sleep 0.3
        fi
    done
}

# Function to monitor progress
monitor_progress() {
    local start_time=$1
    local duration=$2

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))

        if [ $elapsed -ge $duration ]; then
            break
        fi

        # Count results
        if [ -f "$RESULTS_FILE" ]; then
            success=$(grep -c "SUCCESS" "$RESULTS_FILE" 2>/dev/null || echo 0)
            failed=$(grep -c "FAILED" "$RESULTS_FILE" 2>/dev/null || echo 0)
            total=$((success + failed))

            if [ $total -gt 0 ]; then
                rate=$((success * 100 / total))
                tps=$((total / (elapsed + 1)))
                echo -ne "\r${GREEN}Progress:${NC} Time: ${elapsed}s/$duration | Sent: $total | Success: $success | Failed: $failed | Rate: ${rate}% | TPS: $tps    "
            fi
        fi

        sleep 1
    done
    echo ""
}

# Main execution
main() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                  DeCoin Robust Stress Test                       ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Configuration:"
    echo "  • Test Duration: $TEST_DURATION seconds"
    echo "  • Concurrent Users: $CONCURRENT_USERS"
    echo "  • Target TPS per User: $TRANSACTIONS_PER_SECOND"
    echo "  • Network Nodes: ${#NODES[@]}"
    echo "  • Log File: $LOG_FILE"
    echo ""

    # Check node health
    echo -e "${YELLOW}Checking node health...${NC}"
    healthy=0
    for i in "${!NODES[@]}"; do
        port=${NODES[$i]}
        name=${NODE_NAMES[$i]}
        if curl -s -m 1 "http://localhost:$port/health" > /dev/null 2>&1; then
            healthy=$((healthy + 1))
            echo -e "  ${GREEN}✓${NC} $name (port $port)"
        else
            echo -e "  ${RED}✗${NC} $name (port $port)"
        fi
    done

    if [ $healthy -lt 4 ]; then
        echo -e "${RED}Not enough healthy nodes! Need at least 4.${NC}"
        exit 1
    fi

    echo ""
    echo "Healthy nodes: $healthy/${#NODES[@]}"

    # Get initial blockchain state
    echo ""
    echo -e "${YELLOW}Initial blockchain state:${NC}"
    for i in 0 3 6; do
        port=${NODES[$i]}
        name=${NODE_NAMES[$i]}
        blocks=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
            python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")
        mempool=$(curl -s "http://localhost:$port/mempool" 2>/dev/null | \
            python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        echo "  $name: $blocks blocks, $mempool pending"
    done

    # Clean up previous results
    rm -f "$RESULTS_FILE"
    touch "$RESULTS_FILE"

    # Start time
    START_TIME=$(date +%s)

    echo ""
    echo -e "${GREEN}Starting stress test with $CONCURRENT_USERS concurrent users...${NC}"
    echo ""

    # Start users in background
    for user in $(seq 1 $CONCURRENT_USERS); do
        user_workload "$user" "$START_TIME" "$TEST_DURATION" &
    done

    # Monitor progress
    monitor_progress "$START_TIME" "$TEST_DURATION"

    # Wait for all users to complete
    wait

    # Final statistics
    echo ""
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                        Final Results                             ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

    if [ -f "$RESULTS_FILE" ]; then
        success=$(grep -c "SUCCESS" "$RESULTS_FILE" 2>/dev/null || echo 0)
        failed=$(grep -c "FAILED" "$RESULTS_FILE" 2>/dev/null || echo 0)
        total=$((success + failed))

        if [ $total -gt 0 ]; then
            rate=$((success * 100 / total))
            actual_tps=$((total / TEST_DURATION))

            echo "Total Transactions: $total"
            echo "Successful: $success"
            echo "Failed: $failed"
            echo "Success Rate: ${rate}%"
            echo "Average TPS: $actual_tps"
            echo "Target TPS: $((CONCURRENT_USERS * TRANSACTIONS_PER_SECOND))"
        else
            echo "No transactions were processed!"
        fi
    fi

    # Final blockchain state
    echo ""
    echo -e "${YELLOW}Final blockchain state:${NC}"
    for i in 0 3 6; do
        port=${NODES[$i]}
        name=${NODE_NAMES[$i]}
        blocks=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
            python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")
        mempool=$(curl -s "http://localhost:$port/mempool" 2>/dev/null | \
            python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        echo "  $name: $blocks blocks, $mempool pending"
    done

    # Check consensus
    echo ""
    echo -e "${YELLOW}Consensus check:${NC}"
    heights=()
    for port in "${NODES[@]}"; do
        height=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
            python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")
        heights+=($height)
    done

    # Find min and max
    min=${heights[0]}
    max=${heights[0]}
    for h in "${heights[@]}"; do
        [ $h -lt $min ] && min=$h
        [ $h -gt $max ] && max=$h
    done

    if [ $((max - min)) -le 2 ]; then
        echo -e "  ${GREEN}✓ Nodes are in consensus (heights: $min-$max)${NC}"
    else
        echo -e "  ${YELLOW}⚠ Nodes have different heights (range: $min-$max)${NC}"
        echo "  Heights: ${heights[*]}"
    fi

    echo ""
    echo -e "${GREEN}Test completed! Results saved to $LOG_FILE${NC}"
}

# Run the test
main "$@"