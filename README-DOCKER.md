# DeCoin Docker Setup

This document describes how to run DeCoin using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

```bash
# Build the Docker images
./docker-commands.sh build

# Start the network (4 nodes)
./docker-commands.sh up

# Check status
./docker-commands.sh status

# View logs
./docker-commands.sh logs

# Run example transaction
./docker-commands.sh test

# Stop the network
./docker-commands.sh down
```

## Network Architecture

The Docker Compose setup creates a 4-node DeCoin network:

- **node1**: Regular node on port 8080
- **node2**: Regular node on port 8081  
- **node3**: Regular node on port 8082
- **validator**: Validator node on port 8083

All nodes are connected via a Docker bridge network and can communicate with each other.

## API Endpoints

Once running, the nodes expose REST APIs:

- Node 1: http://localhost:8080
- Node 2: http://localhost:8081
- Node 3: http://localhost:8082
- Validator: http://localhost:8083

### Example API Calls

```bash
# Check node status
curl http://localhost:8080/status

# Get blockchain info
curl http://localhost:8080/blockchain

# Submit transaction
curl -X POST http://localhost:8080/transaction \
  -H "Content-Type: application/json" \
  -d '{"from": "alice", "to": "bob", "amount": 10}'
```

## Docker Commands

### Using docker-compose directly

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f node1

# Execute command in container
docker-compose exec node1 python examples/example_usage.py

# Stop all containers
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Using helper script

```bash
./docker-commands.sh build    # Build images
./docker-commands.sh up        # Start network
./docker-commands.sh logs      # View all logs
./docker-commands.sh logs node1 # View specific node logs
./docker-commands.sh exec node1 bash # Shell into container
./docker-commands.sh test      # Run example
./docker-commands.sh down      # Stop network
./docker-commands.sh clean     # Remove everything
```

## Data Persistence

Each node stores its blockchain data in a named Docker volume:
- `node1-data`
- `node2-data`
- `node3-data`
- `validator-data`

To reset the blockchain, use:
```bash
./docker-commands.sh clean
```

## Configuration

Node configurations are stored in `config/docker/`:
- `node1.json`
- `node2.json`
- `node3.json`
- `validator.json`

Modify these files to change node settings before starting the network.

## Troubleshooting

### Containers won't start
```bash
# Check logs
docker-compose logs node1

# Rebuild images
docker-compose build --no-cache
```

### Port conflicts
If ports 8080-8083 are in use, modify the port mappings in `docker-compose.yml`.

### Network issues
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

## Development

To develop with hot-reload:

1. Mount source code as volume in `docker-compose.yml`:
```yaml
volumes:
  - ./src:/app/src
```

2. Restart containers when code changes:
```bash
docker-compose restart node1
```