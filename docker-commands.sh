#!/bin/bash

# DeCoin Docker Commands Helper Script

case "$1" in
  "build")
    echo "Building DeCoin Docker images..."
    docker-compose build
    ;;
  
  "up")
    echo "Starting DeCoin network..."
    docker-compose up -d
    echo "Waiting for nodes to start..."
    sleep 5
    docker-compose ps
    echo ""
    echo "DeCoin nodes are running at:"
    echo "  Node 1: http://localhost:10080"
    echo "  Node 2: http://localhost:10081"
    echo "  Node 3: http://localhost:10082"
    echo "  Validator: http://localhost:10083"
    ;;
  
  "down")
    echo "Stopping DeCoin network..."
    docker-compose down
    ;;
  
  "clean")
    echo "Stopping and removing all DeCoin containers and volumes..."
    docker-compose down -v
    ;;
  
  "logs")
    if [ -z "$2" ]; then
      docker-compose logs -f
    else
      docker-compose logs -f "$2"
    fi
    ;;
  
  "status")
    echo "DeCoin Network Status:"
    docker-compose ps
    ;;
  
  "exec")
    if [ -z "$2" ]; then
      echo "Usage: $0 exec <node-name> [command]"
      echo "Example: $0 exec node1 python examples/example_usage.py"
    else
      node=$2
      shift 2
      docker-compose exec "$node" "$@"
    fi
    ;;
  
  "test")
    echo "Running example transaction on node1..."
    docker-compose exec node1 python examples/example_usage.py
    ;;
  
  *)
    echo "DeCoin Docker Management Script"
    echo ""
    echo "Usage: $0 {build|up|down|clean|logs|status|exec|test}"
    echo ""
    echo "Commands:"
    echo "  build   - Build Docker images"
    echo "  up      - Start all nodes"
    echo "  down    - Stop all nodes"
    echo "  clean   - Stop and remove all containers and volumes"
    echo "  logs    - View logs (optional: specify node name)"
    echo "  status  - Show container status"
    echo "  exec    - Execute command in a container"
    echo "  test    - Run example transaction"
    echo ""
    echo "Examples:"
    echo "  $0 build              # Build images"
    echo "  $0 up                 # Start network"
    echo "  $0 logs node1         # View node1 logs"
    echo "  $0 exec node1 bash    # Shell into node1"
    echo "  $0 test               # Run example"
    echo "  $0 down               # Stop network"
    ;;
esac