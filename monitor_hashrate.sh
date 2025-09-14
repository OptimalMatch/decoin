#!/bin/bash

# Monitor network hashrate across all nodes

echo "=== DeCoin Network Hashrate Monitor ==="
echo ""

# Node ports
NODES=(11080 11081 11082 11084 11085 11086 11083 11087)
NODE_NAMES=("Node1" "Node2" "Node3" "Node4" "Node5" "Node6" "Validator1" "Validator2")

while true; do
    clear
    echo "=== Network Hashrate Statistics ==="
    echo "Time: $(date +'%H:%M:%S')"
    echo ""

    total_hashrate=0
    mining_nodes=0

    for i in "${!NODES[@]}"; do
        port=${NODES[$i]}
        name=${NODE_NAMES[$i]}

        # Get mining status
        mining_info=$(curl -s "http://localhost:$port/mining/difficulty" 2>/dev/null)

        if [ -n "$mining_info" ]; then
            is_mining=$(echo "$mining_info" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('is_mining', False))" 2>/dev/null || echo "false")
            difficulty=$(echo "$mining_info" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('difficulty', 0))" 2>/dev/null || echo "0")

            if [ "$is_mining" = "True" ]; then
                mining_nodes=$((mining_nodes + 1))
                status="MINING"
                color="\033[0;32m"  # Green
            else
                status="IDLE"
                color="\033[0;33m"  # Yellow
            fi

            printf "%-12s: ${color}%-8s\033[0m Difficulty: %d\n" "$name" "$status" "$difficulty"
        else
            printf "%-12s: \033[0;31m%-8s\033[0m\n" "$name" "OFFLINE"
        fi
    done

    echo ""
    echo "=== Summary ==="
    echo "Active Miners: $mining_nodes / ${#NODES[@]}"
    echo "Network Difficulty: $(curl -s http://localhost:11080/mining/difficulty 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('difficulty', 0))" 2>/dev/null || echo "N/A")"

    # Calculate approximate hashrate (simplified)
    blocks_last_hour=$(curl -s http://localhost:11080/blockchain 2>/dev/null | python3 -c "
import json, sys, time
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
current_time = time.time()
one_hour_ago = current_time - 3600
recent_blocks = [b for b in blocks if b.get('timestamp') and (current_time - b['timestamp']) < 3600]
print(len(recent_blocks))
" 2>/dev/null || echo "0")

    echo "Blocks mined (last hour): $blocks_last_hour"

    if [ "$blocks_last_hour" -gt 0 ]; then
        avg_block_time=$((3600 / blocks_last_hour))
        echo "Average block time: ${avg_block_time}s"
    fi

    sleep 10
done