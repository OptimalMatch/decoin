#!/bin/bash

# Simple stress test for DeCoin network
# This version is simpler and more reliable

set -e

# Configuration
NODES=(11080 11081 11082 11084 11085 11086 11083 11087)
NODE_NAMES=("Node1" "Node2" "Node3" "Node4" "Node5" "Node6" "Validator1" "Validator2")
DURATION=60  # Run for 60 seconds
BATCH_SIZE=5  # Transactions per batch

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Counters
SUCCESS_COUNT=0
FAIL_COUNT=0
START_TIME=$(date +%s)

echo -e "${BLUE}=== Simple DeCoin Stress Test ===${NC}"
echo "Duration: $DURATION seconds"
echo "Batch Size: $BATCH_SIZE transactions"
echo ""

# Function to send transaction
send_transaction() {
    local port=$1
    local recipient=$2

    response=$(curl -s -m 2 -X POST "http://localhost:$port/faucet/$recipient" 2>/dev/null)

    if echo "$response" | grep -q "success.*true" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to run test
run_test() {
    local batch_num=0

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - START_TIME))

        if [ $elapsed -ge $DURATION ]; then
            break
        fi

        batch_num=$((batch_num + 1))
        echo -e "${YELLOW}[$(date +'%H:%M:%S')] Batch $batch_num (Elapsed: ${elapsed}s)${NC}"

        # Send transactions to different nodes
        for i in $(seq 1 $BATCH_SIZE); do
            # Pick a random node
            node_index=$((RANDOM % ${#NODES[@]}))
            port=${NODES[$node_index]}
            recipient="TEST_B${batch_num}_T${i}_$(date +%s%N)"

            if send_transaction "$port" "$recipient"; then
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                echo -n "."
            else
                FAIL_COUNT=$((FAIL_COUNT + 1))
                echo -n "x"
            fi
        done
        echo ""

        # Show current stats
        total=$((SUCCESS_COUNT + FAIL_COUNT))
        if [ $total -gt 0 ]; then
            success_rate=$((SUCCESS_COUNT * 100 / total))
            tps=$((SUCCESS_COUNT / (elapsed + 1)))
            echo "  Stats: Success=$SUCCESS_COUNT, Failed=$FAIL_COUNT, Rate=${success_rate}%, TPS=$tps"
        fi

        # Small delay between batches
        sleep 1
    done
}

# Check node health first
echo -e "${YELLOW}Checking node health...${NC}"
healthy=0
for port in "${NODES[@]}"; do
    if curl -s -m 1 "http://localhost:$port/health" > /dev/null 2>&1; then
        healthy=$((healthy + 1))
    fi
done
echo "Healthy nodes: $healthy/${#NODES[@]}"

if [ $healthy -lt 4 ]; then
    echo -e "${RED}Not enough healthy nodes!${NC}"
    exit 1
fi

# Get initial blockchain state
echo ""
echo -e "${YELLOW}Initial blockchain state:${NC}"
for i in 0 3 6; do
    port=${NODES[$i]}
    name=${NODE_NAMES[$i]}
    blocks=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
        python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")
    echo "  $name: $blocks blocks"
done

# Run the test
echo ""
echo -e "${GREEN}Starting stress test...${NC}"
run_test

# Final results
echo ""
echo -e "${GREEN}=== Final Results ===${NC}"
total=$((SUCCESS_COUNT + FAIL_COUNT))
if [ $total -gt 0 ]; then
    success_rate=$((SUCCESS_COUNT * 100 / total))
    echo "Total Transactions: $total"
    echo "Successful: $SUCCESS_COUNT"
    echo "Failed: $FAIL_COUNT"
    echo "Success Rate: ${success_rate}%"
    echo "Average TPS: $((SUCCESS_COUNT / DURATION))"
fi

# Check final blockchain state
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