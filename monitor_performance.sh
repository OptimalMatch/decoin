#!/bin/bash

# DeCoin Network Performance Monitor
# Real-time monitoring of blockchain network performance

set -e

# Configuration
NODES=(11080 11081 11082 11084 11085 11086 11083 11087)
NODE_NAMES=("Node1" "Node2" "Node3" "Node4" "Node5" "Node6" "Validator1" "Validator2")
REFRESH_INTERVAL=2

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Performance data storage
declare -A PREV_BLOCKS
declare -A PREV_TXS
declare -A BLOCK_TIMES

# Initialize previous values
for port in "${NODES[@]}"; do
    PREV_BLOCKS[$port]=0
    PREV_TXS[$port]=0
done

# Function to get node statistics
get_node_stats() {
    local port=$1
    local response=$(curl -s "http://localhost:$port/status" 2>/dev/null)

    if [ -n "$response" ]; then
        echo "$response"
    else
        echo "{}"
    fi
}

# Function to get blockchain info
get_blockchain_info() {
    local port=$1
    local blockchain=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null)

    if [ -n "$blockchain" ]; then
        local blocks=$(echo "$blockchain" | python3 -c "
import json, sys
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
print(len(blocks))
" 2>/dev/null || echo "0")

        local last_block_time=$(echo "$blockchain" | python3 -c "
import json, sys
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
if blocks:
    print(blocks[-1].get('timestamp', 'N/A')[:19])
else:
    print('N/A')
" 2>/dev/null || echo "N/A")

        local total_txs=$(echo "$blockchain" | python3 -c "
import json, sys
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
total = sum(len(b.get('transactions', [])) for b in blocks)
print(total)
" 2>/dev/null || echo "0")

        echo "$blocks|$last_block_time|$total_txs"
    else
        echo "0|N/A|0"
    fi
}

# Function to get mempool size
get_mempool_size() {
    local port=$1
    local size=$(curl -s "http://localhost:$port/mempool" 2>/dev/null | \
        python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "$size"
}

# Function to get peer count
get_peer_count() {
    local port=$1
    local peers=$(curl -s "http://localhost:$port/peers" 2>/dev/null | \
        python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "$peers"
}

# Function to calculate block rate
calculate_block_rate() {
    local port=$1
    local current_blocks=$2
    local prev_blocks=${PREV_BLOCKS[$port]}

    if [ "$prev_blocks" -eq 0 ]; then
        echo "0"
    else
        local new_blocks=$((current_blocks - prev_blocks))
        echo "$new_blocks"
    fi

    PREV_BLOCKS[$port]=$current_blocks
}

# Function to display header
display_header() {
    clear
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                         DeCoin Network Performance Monitor                        ${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Time: $(date +'%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
}

# Function to display node table
display_node_table() {
    echo -e "${BOLD}${GREEN}Node Status Overview${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    printf "${BOLD}%-12s %-7s %-8s %-8s %-8s %-8s %-8s %-10s${NC}\n" \
        "Node" "Port" "Status" "Blocks" "Mempool" "Peers" "Mining" "Block Rate"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local total_blocks=0
    local total_mempool=0
    local total_peers=0
    local mining_nodes=0

    for i in "${!NODES[@]}"; do
        local port=${NODES[$i]}
        local name=${NODE_NAMES[$i]}

        # Get node status
        local status_json=$(get_node_stats "$port")
        local is_mining=$(echo "$status_json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Yes' if data.get('is_mining', False) else 'No')
" 2>/dev/null || echo "No")

        # Get blockchain info
        local blockchain_info=$(get_blockchain_info "$port")
        IFS='|' read -r blocks last_time total_txs <<< "$blockchain_info"

        # Get mempool and peers
        local mempool=$(get_mempool_size "$port")
        local peers=$(get_peer_count "$port")

        # Calculate block rate
        local block_rate=$(calculate_block_rate "$port" "$blocks")

        # Update totals
        total_blocks=$((total_blocks > blocks ? total_blocks : blocks))
        total_mempool=$((total_mempool + mempool))
        total_peers=$((total_peers > peers ? total_peers : peers))
        if [ "$is_mining" == "Yes" ]; then
            ((mining_nodes++))
        fi

        # Determine status color
        local status_color="${GREEN}"
        local status_text="Online"
        if [ "$blocks" -eq 0 ]; then
            status_color="${RED}"
            status_text="Offline"
        fi

        # Determine if this is a validator
        local node_indicator=""
        if [[ "$name" == *"Validator"* ]]; then
            node_indicator="⭐"
        fi

        # Display row
        printf "%-12s %-7s ${status_color}%-8s${NC} %-8s %-8s %-8s %-8s %-10s\n" \
            "$node_indicator$name" "$port" "$status_text" "$blocks" "$mempool" "$peers" "$is_mining" "+$block_rate/interval"
    done

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    printf "${BOLD}%-12s %-7s %-8s %-8s %-8s %-8s %-8s${NC}\n" \
        "NETWORK" "" "" "$total_blocks" "$total_mempool" "$total_peers" "$mining_nodes active"
}

# Function to display consensus status
display_consensus_status() {
    echo ""
    echo -e "${BOLD}${GREEN}Consensus Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local heights=()
    for port in "${NODES[@]}"; do
        local blockchain_info=$(get_blockchain_info "$port")
        IFS='|' read -r blocks _ _ <<< "$blockchain_info"
        heights+=($blocks)
    done

    # Find max height
    local max_height=0
    for h in "${heights[@]}"; do
        if [ "$h" -gt "$max_height" ]; then
            max_height=$h
        fi
    done

    # Check consensus
    local consensus=true
    for h in "${heights[@]}"; do
        if [ "$h" -ne "$max_height" ]; then
            consensus=false
            break
        fi
    done

    if [ "$consensus" = true ]; then
        echo -e "${GREEN}✓ Network in consensus at height $max_height${NC}"
    else
        echo -e "${RED}✗ Network out of consensus - heights vary${NC}"
        echo -e "${YELLOW}  Heights: ${heights[*]}${NC}"
    fi
}

# Function to display recent activity
display_recent_activity() {
    echo ""
    echo -e "${BOLD}${GREEN}Recent Network Activity${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Get latest block info from first responsive node
    for port in "${NODES[@]}"; do
        local blockchain=$(curl -s "http://localhost:$port/blockchain" 2>/dev/null)
        if [ -n "$blockchain" ]; then
            local last_block_info=$(echo "$blockchain" | python3 -c "
import json, sys
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
if blocks and len(blocks) > 1:
    last = blocks[-1]
    print(f\"Latest Block: #{last.get('index', 'N/A')} | Transactions: {len(last.get('transactions', []))} | Hash: {last.get('hash', 'N/A')[:16]}...\")
" 2>/dev/null || echo "No recent blocks")
            echo "$last_block_info"
            break
        fi
    done
}

# Function to display performance metrics
display_performance_metrics() {
    echo ""
    echo -e "${BOLD}${GREEN}Performance Metrics${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Calculate network TPS (approximate)
    local total_tx_change=0
    for port in "${NODES[@]}"; do
        local blockchain_info=$(get_blockchain_info "$port")
        IFS='|' read -r _ _ total_txs <<< "$blockchain_info"

        local prev_txs=${PREV_TXS[$port]:-0}
        if [ "$prev_txs" -ne 0 ]; then
            local tx_change=$((total_txs - prev_txs))
            total_tx_change=$((total_tx_change + tx_change))
        fi
        PREV_TXS[$port]=$total_txs
    done

    # Average TPS across all nodes
    local avg_tps=0
    if [ "${#NODES[@]}" -gt 0 ]; then
        avg_tps=$((total_tx_change / ${#NODES[@]} / REFRESH_INTERVAL))
    fi

    echo "Average TPS: $avg_tps transactions/second"
}

# Main monitoring loop
monitor_loop() {
    while true; do
        display_header
        display_node_table
        display_consensus_status
        display_recent_activity
        display_performance_metrics

        echo ""
        echo -e "${CYAN}Press Ctrl+C to exit | Refreshing every ${REFRESH_INTERVAL}s...${NC}"

        sleep $REFRESH_INTERVAL
    done
}

# Main function
main() {
    # Check if Docker containers are running
    if ! docker ps | grep -q decoin; then
        echo -e "${RED}DeCoin containers are not running. Please start them first.${NC}"
        exit 1
    fi

    # Trap Ctrl+C
    trap 'echo -e "\n${YELLOW}Monitoring stopped by user${NC}"; exit 0' INT TERM

    # Start monitoring
    monitor_loop
}

# Run main function
main