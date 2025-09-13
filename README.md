# DeCoin - A Complete Cryptocurrency Implementation

[![Tests](https://github.com/yourusername/decoin/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/decoin/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

DeCoin is a fully-functional cryptocurrency system built from scratch in Python, featuring a complete blockchain implementation, multiple transaction types, hybrid consensus mechanisms, P2P networking, and a REST API with Swagger documentation.

## 🚀 Features

### Core Blockchain
- **Custom blockchain** implementation with SHA-256 hashing
- **Merkle tree** for efficient transaction verification
- **UTXO model** for balance tracking
- **Configurable difficulty** adjustment
- **Fork resolution** using longest chain rule

### Transaction Types
- **Standard** - Basic value transfer between addresses
- **MultiSig** - Requires multiple signatures for authorization
- **TimeLocked** - Time-based transaction restrictions
- **DataStorage** - On-chain data storage capability
- **SmartContract** - Programmable contract execution

### Consensus Mechanisms
- **Proof of Work (PoW)** - CPU-based mining with adjustable difficulty
- **Proof of Stake (PoS)** - Stake-based block validation
- **Hybrid Consensus** - Configurable PoW/PoS weight distribution (default: 30% PoW, 70% PoS)

### Networking & API
- **P2P Network** - WebSocket-based peer discovery and message propagation
- **REST API** - FastAPI with automatic OpenAPI/Swagger documentation
- **Real-time Updates** - WebSocket subscriptions for blockchain events
- **Multi-node Support** - Run multiple nodes in a network

### Monitoring & Performance
- **System Metrics** - CPU, memory, disk, and network monitoring
- **Blockchain Metrics** - TPS, block time, mempool size tracking
- **Health Checks** - Automatic health monitoring and alerting
- **Performance** - 166,000+ transactions/second capability

## 📋 Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for containerized deployment)
- Git

## 🛠️ Installation

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/decoin.git
cd decoin
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Installation

Simply use Docker Compose:
```bash
docker compose up -d
```

## 🚀 Quick Start

### Run a Single Node

```bash
python src/node.py --node-id node1 --port 10080 --ws-port 6001
```

### Run Multiple Nodes (Docker)

```bash
# Start the 4-node network
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop the network
docker compose down
```

### Access the API

Once running, you can access:
- **API Documentation**: http://localhost:10080/docs
- **Node Status**: http://localhost:10080/status
- **Blockchain Explorer**: http://localhost:10080/blockchain
- **Health Check**: http://localhost:10080/health

## 📖 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/status` | Node status and statistics |
| GET | `/blockchain` | Get full blockchain |
| GET | `/block/{index}` | Get specific block |
| POST | `/transaction` | Submit new transaction |
| GET | `/mempool` | Get pending transactions |
| GET | `/balance/{address}` | Get address balance |
| GET | `/peers` | List connected peers |
| POST | `/mine` | Start/stop mining |
| GET | `/health` | Health check |

### Transaction Submission

Submit a standard transaction:
```bash
curl -X POST http://localhost:10080/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "alice",
    "recipient": "bob",
    "amount": 10.5,
    "transaction_type": "standard"
  }'
```

### Mining Control

Start mining:
```bash
curl -X POST http://localhost:10080/mine \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Suites
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance benchmarks
python tests/performance/benchmark.py

# Stress testing
python tests/performance/stress_test.py
```

### Test Coverage
```bash
pytest --cov=src --cov-report=html
```

Current test status: **54/55 tests passing (98% pass rate)**

## 🐳 Docker Deployment

### Build Images
```bash
docker compose build
```

### Start Network
```bash
docker compose up -d
```

### Network Configuration

The Docker Compose setup creates a 4-node network:

| Node | API Port | WebSocket Port | Type |
|------|----------|----------------|------|
| node1 | 10080 | 6001 | Regular Node |
| node2 | 10081 | 6002 | Regular Node |
| node3 | 10082 | 6003 | Regular Node |
| validator | 10083 | 6004 | Validator Node |

### Custom Configuration

Edit `docker-compose.yml` to modify:
- Number of nodes
- Port mappings
- Environment variables
- Resource limits

## ⚙️ Configuration

### Node Configuration

Create a `config/node.json` file:
```json
{
  "node_id": "node1",
  "host": "0.0.0.0",
  "port": 10080,
  "ws_port": 6001,
  "peers": ["ws://node2:6002"],
  "mining": true,
  "validator_stake": 1000,
  "consensus": {
    "type": "hybrid",
    "pow_weight": 0.3,
    "pos_weight": 0.7
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DECOIN_NODE_ID` | Node identifier | `node1` |
| `DECOIN_PORT` | API port | `10080` |
| `DECOIN_WS_PORT` | WebSocket port | `6001` |
| `DECOIN_PEERS` | Comma-separated peer list | `""` |
| `DECOIN_MINING` | Enable mining | `true` |
| `DECOIN_DIFFICULTY` | Mining difficulty | `4` |

## 📊 Performance Benchmarks

Based on benchmark tests:

| Metric | Performance |
|--------|------------|
| Transaction Creation | 166,930 tx/sec |
| Block Mining (difficulty=3) | 3,780 blocks/min |
| Chain Validation | 31,297 validations/sec |
| Balance Lookups | 309,608 lookups/sec |
| API Response Time | < 10ms average |

## 🏗️ Architecture

```
decoin/
├── src/                        # Source code
│   ├── blockchain.py           # Core blockchain implementation
│   ├── transactions.py         # Transaction types and builder
│   ├── consensus.py            # Consensus mechanisms
│   ├── network.py              # P2P networking layer
│   ├── api_fastapi.py          # REST API implementation
│   ├── schemas.py              # Pydantic models
│   ├── node.py                 # Node entry point
│   └── monitoring.py           # Monitoring and metrics
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── performance/            # Performance tests
├── config/                     # Configuration files
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container image
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 src/ tests/

# Format code
black src/ tests/

# Type checking
mypy src/
```

### Using the Makefile

```bash
make install        # Install all dependencies
make test          # Run all tests
make test-unit     # Run unit tests only
make lint          # Run code linting
make format        # Format code
make docker-up     # Start Docker network
make docker-down   # Stop Docker network
make clean         # Clean temporary files
```

## 📚 Documentation

### API Documentation
Access the interactive API documentation at http://localhost:8080/docs when the node is running.

### Code Documentation
Generate code documentation:
```bash
sphinx-build -b html docs/ docs/_build
```

## 🔒 Security Considerations

⚠️ **This is an educational/demonstration project. Do not use in production without proper security auditing.**

Current security features:
- Transaction signature validation
- Block hash verification
- Chain integrity checks
- Input validation on all endpoints
- Safe smart contract execution sandbox

Missing for production:
- Proper key management
- Network encryption
- DDoS protection
- Rate limiting
- Audit logging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built as a comprehensive demonstration of blockchain technology
- Inspired by Bitcoin and Ethereum architectures
- Uses modern Python async/await patterns
- Leverages FastAPI for high-performance API

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review the [test examples](tests/)

## 🚦 Project Status

✅ **Production Ready Features:**
- Core blockchain functionality
- Transaction processing
- P2P networking
- REST API
- Docker deployment

🚧 **In Development:**
- Wallet implementation
- Block explorer UI
- Advanced smart contracts
- Cross-chain bridges

## 📈 Roadmap

### Phase 1 (Complete ✅)
- [x] Basic blockchain implementation
- [x] Transaction types
- [x] Consensus mechanisms
- [x] P2P networking
- [x] REST API
- [x] Docker deployment

### Phase 2 (In Progress)
- [ ] Web-based wallet
- [ ] Block explorer interface
- [ ] Enhanced smart contracts
- [ ] Mobile app support

### Phase 3 (Planned)
- [ ] Cross-chain interoperability
- [ ] DEX functionality
- [ ] Governance tokens
- [ ] Staking rewards

## Technical Specifications

- **Block Time**: 30 seconds
- **Block Size**: 4MB base
- **Transaction Throughput**: ~500 TPS real-world, 166k TPS in benchmarks
- **Consensus**: Hybrid PoS/PoW (70% stake, 30% work)
- **Metadata Size**: Up to 1KB per transaction
- **Script Support**: Extended transaction types with smart contract capability

---

**Built with ❤️ by the DeCoin Team**