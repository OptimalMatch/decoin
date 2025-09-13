#!/bin/bash

# DeCoin Services Monitoring Script
# Monitors health and performance of DeCoin services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
REFRESH_INTERVAL=5  # Seconds between updates
NODES=("node1:10080" "node2:10081" "node3:10082" "validator:10083")

# Function to clear screen and move cursor to top
clear_screen() {
    clear
    tput cup 0 0
}

# Function to get service status
get_service_status() {
    local node=$1
    local port=$2
    local url="http://localhost:${port}/status"

    if response=$(curl -s -f "$url" 2>/dev/null); then
        echo "$response"
    else
        echo '{"error": "unreachable"}'
    fi
}

# Function to get container stats
get_container_stats() {
    local container=$1
    docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" "$container" 2>/dev/null | tail -1
}

# Function to display header
display_header() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                   DeCoin Services Monitor                         ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}Last Update:${NC} $(date +'%Y-%m-%d %H:%M:%S')  ${BLUE}Refresh:${NC} ${REFRESH_INTERVAL}s  ${BLUE}Press Ctrl+C to exit${NC}"
    echo
}

# Function to display node status
display_node_status() {
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}Node Status${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    printf "%-15s %-10s %-15s %-20s %-15s\n" "Node" "Status" "Block Height" "Pending Txns" "Connected Peers"
    echo "─────────────────────────────────────────────────────────────────────"

    for node_info in "${NODES[@]}"; do
        IFS=':' read -r node port <<< "$node_info"
        status_json=$(get_service_status "$node" "$port")

        if echo "$status_json" | grep -q "error"; then
            printf "%-15s ${RED}%-10s${NC} %-15s %-20s %-15s\n" \
                "$node" "OFFLINE" "-" "-" "-"
        else
            # Parse JSON response (basic parsing)
            chain_height=$(echo "$status_json" | grep -o '"chain_height":[0-9]*' | cut -d: -f2)
            pending_tx=$(echo "$status_json" | grep -o '"pending_transactions":[0-9]*' | cut -d: -f2)
            peers=$(echo "$status_json" | grep -o '"connected_peers":[0-9]*' | cut -d: -f2)
            is_mining=$(echo "$status_json" | grep -o '"is_mining":[a-z]*' | cut -d: -f2)

            # Set default values if parsing fails
            chain_height=${chain_height:-0}
            pending_tx=${pending_tx:-0}
            peers=${peers:-0}

            # Determine status color
            if [ "$is_mining" = "true" ]; then
                status="${GREEN}MINING${NC}"
            else
                status="${GREEN}ONLINE${NC}"
            fi

            printf "%-15s %-19s %-15s %-20s %-15s\n" \
                "$node" "$status" "$chain_height" "$pending_tx" "$peers"
        fi
    done
}

# Function to display container stats
display_container_stats() {
    echo
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}Resource Usage${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    printf "%-15s %-15s %-30s\n" "Container" "CPU Usage" "Memory Usage"
    echo "─────────────────────────────────────────────────────────────────────"

    for container in decoin-node1 decoin-node2 decoin-node3 decoin-validator; do
        stats=$(get_container_stats "$container")
        if [ -n "$stats" ]; then
            cpu=$(echo "$stats" | awk '{print $1}')
            mem=$(echo "$stats" | awk '{print $2" "$3" "$4}')
            printf "%-15s %-15s %-30s\n" "${container#decoin-}" "$cpu" "$mem"
        else
            printf "%-15s ${YELLOW}%-15s${NC} %-30s\n" "${container#decoin-}" "N/A" "Container not running"
        fi
    done
}

# Function to display recent logs
display_recent_logs() {
    echo
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}Recent Activity (Last 5 lines from each node)${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    for container in decoin-node1 decoin-node2 decoin-node3 decoin-validator; do
        if docker ps -q -f name="$container" 2>/dev/null | grep -q .; then
            echo -e "${BLUE}${container#decoin-}:${NC}"
            docker logs "$container" 2>/dev/null | tail -5 | sed 's/^/  /'
        fi
    done
}

# Function to check overall health
check_overall_health() {
    echo
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}Health Summary${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local healthy_count=0
    local total_count=${#NODES[@]}

    for node_info in "${NODES[@]}"; do
        IFS=':' read -r node port <<< "$node_info"
        if curl -s -f "http://localhost:${port}/health" >/dev/null 2>&1; then
            ((healthy_count++))
        fi
    done

    if [ $healthy_count -eq $total_count ]; then
        echo -e "${GREEN}✓ All services are healthy ($healthy_count/$total_count)${NC}"
    elif [ $healthy_count -gt 0 ]; then
        echo -e "${YELLOW}⚠ Partial health ($healthy_count/$total_count services responding)${NC}"
    else
        echo -e "${RED}✗ No services are responding${NC}"
    fi

    # Check Docker Compose status
    if docker-compose ps -q 2>/dev/null | grep -q . || docker compose ps -q 2>/dev/null | grep -q .; then
        container_count=$(docker-compose ps -q 2>/dev/null | wc -l || docker compose ps -q 2>/dev/null | wc -l)
        echo -e "${GREEN}✓ Docker Compose: $container_count containers running${NC}"
    else
        echo -e "${RED}✗ Docker Compose: No containers running${NC}"
    fi
}

# Function for continuous monitoring
monitor_loop() {
    while true; do
        clear_screen
        display_header
        display_node_status
        display_container_stats
        check_overall_health

        # Show abbreviated logs in continuous mode
        if [ "$1" != "--no-logs" ]; then
            echo
            echo -e "${CYAN}Tip: Use --no-logs flag to hide log output${NC}"
            display_recent_logs
        fi

        sleep $REFRESH_INTERVAL
    done
}

# Function for single status check
single_check() {
    display_header
    display_node_status
    display_container_stats
    check_overall_health

    if [ "$1" != "--no-logs" ]; then
        display_recent_logs
    fi
}

# Main execution
main() {
    # Change to script directory
    cd "$(dirname "$0")"

    # Check if services are running
    if ! docker-compose ps -q 2>/dev/null | grep -q . && ! docker compose ps -q 2>/dev/null | grep -q .; then
        echo -e "${RED}No DeCoin services are running.${NC}"
        echo "Start services with: ./start-services.sh"
        exit 1
    fi

    # Parse arguments
    case "${1:-}" in
        --once)
            single_check "$2"
            ;;
        --no-logs)
            monitor_loop "--no-logs"
            ;;
        --help|-h)
            echo "DeCoin Services Monitor"
            echo
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --once      Run once and exit"
            echo "  --no-logs   Hide log output"
            echo "  --help      Show this help message"
            echo
            echo "Default: Continuous monitoring with logs"
            ;;
        *)
            monitor_loop
            ;;
    esac
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Monitoring stopped${NC}"; exit 0' INT TERM

# Run main function
main "$@"