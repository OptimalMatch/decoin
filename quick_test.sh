#!/bin/bash

# Quick test script for DeCoin network
# Runs a short stress test to verify everything is working

set -e

# Configuration
TEST_DURATION=30  # 30 seconds quick test
NODES=(11080 11081 11082 11084 11085 11086 11083 11087)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== DeCoin Quick Test ===${NC}"
echo "This will run a 30-second test of the network"
echo ""

# Check if containers are running
echo -e "${YELLOW}Checking Docker containers...${NC}"
if ! docker ps | grep -q decoin; then
    echo "Starting containers..."
    docker compose up -d
    echo "Waiting for nodes to start..."
    sleep 15
fi

# Check node health
echo -e "${YELLOW}Checking node health...${NC}"
healthy_nodes=0
for port in "${NODES[@]}"; do
    if curl -s -m 2 "http://localhost:$port/health" > /dev/null 2>&1; then
        healthy_nodes=$((healthy_nodes + 1))
        echo -e "${GREEN}✓${NC} Node on port $port is healthy"
    else
        echo "✗ Node on port $port is not responding"
    fi
done

echo ""
echo "Healthy nodes: $healthy_nodes/${#NODES[@]}"

if [ $healthy_nodes -lt 4 ]; then
    echo "Not enough healthy nodes. Exiting..."
    exit 1
fi

# Get initial state
echo ""
echo -e "${YELLOW}Initial blockchain state:${NC}"
for port in 11080 11084 11087; do
    blocks=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
        python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")
    echo "Node on port $port: $blocks blocks"
done

# Create some test transactions
echo ""
echo -e "${YELLOW}Creating test transactions...${NC}"
for i in $(seq 1 20); do
    port_index=$((i % ${#NODES[@]}))
    port=${NODES[$port_index]}
    curl -s -m 2 -X POST "http://localhost:$port/faucet/QUICKTEST_$i" > /dev/null 2>&1 && echo -n "."
done
echo " Done!"

# Wait for mining
echo ""
echo -e "${YELLOW}Waiting for transactions to be mined (15 seconds)...${NC}"
sleep 15

# Check final state
echo ""
echo -e "${YELLOW}Final blockchain state:${NC}"
max_blocks=0
min_blocks=999999
for port in "${NODES[@]}"; do
    blocks=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null | \
        python3 -c "import json,sys; print(len(json.load(sys.stdin)['blocks']))" 2>/dev/null || echo "0")

    if [ $blocks -gt $max_blocks ]; then
        max_blocks=$blocks
    fi
    if [ $blocks -lt $min_blocks ]; then
        min_blocks=$blocks
    fi
done

echo "Minimum blocks: $min_blocks"
echo "Maximum blocks: $max_blocks"

if [ $max_blocks -eq $min_blocks ]; then
    echo -e "${GREEN}✓ All nodes are in consensus!${NC}"
else
    echo "⚠ Nodes have different block heights (this is normal if mining is in progress)"
fi

# Check mempool
echo ""
echo -e "${YELLOW}Checking mempool status:${NC}"
total_pending=0
for port in 11080 11084 11087; do
    pending=$(curl -s "http://localhost:$port/mempool" 2>/dev/null | \
        python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "Node on port $port: $pending pending transactions"
    total_pending=$((total_pending + pending))
done

echo ""
echo -e "${GREEN}=== Quick Test Complete ===${NC}"
echo "Summary:"
echo "  - Healthy nodes: $healthy_nodes/${#NODES[@]}"
echo "  - Blockchain height: $max_blocks blocks"
echo "  - Pending transactions: $total_pending"
echo ""
echo "To run a full stress test, use: ./stress_test.sh"
echo "To monitor the network, use: ./monitor_performance.sh"