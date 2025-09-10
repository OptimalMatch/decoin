# DeCoin API Documentation

## Base URL
```
http://localhost:8080
```

## Endpoints

### GET /status
Get node status information.

**Response:**
```json
{
  "node_id": "abc123...",
  "chain_height": 42,
  "pending_transactions": 5,
  "connected_peers": 3,
  "is_mining": true,
  "difficulty": 4
}
```

### GET /blockchain
Get the entire blockchain.

**Response:**
```json
{
  "chain": [...],
  "pending_transactions": [...],
  "difficulty": 4,
  "block_time": 30
}
```

### POST /transaction
Submit a new transaction.

**Request Body:**

Standard Transaction:
```json
{
  "type": "standard",
  "sender": "alice_address",
  "recipient": "bob_address",
  "amount": 10.5,
  "fee": 0.001,
  "metadata": {
    "note": "Payment for services"
  }
}
```

Multi-Signature Transaction:
```json
{
  "type": "multisig",
  "senders": ["alice", "bob", "charlie"],
  "recipient": "dave",
  "amount": 100,
  "required_signatures": 2,
  "fee": 0.002
}
```

Time-Locked Transaction:
```json
{
  "type": "time_locked",
  "sender": "alice",
  "recipient": "bob",
  "amount": 50,
  "unlock_time": 1234567890,
  "fee": 0.001
}
```

Data Storage Transaction:
```json
{
  "type": "data_storage",
  "sender": "alice",
  "data": {
    "key": "value",
    "nested": {
      "data": "structure"
    }
  },
  "fee": 0.005
}
```

**Response:**
```json
{
  "tx_hash": "abc123...",
  "status": "pending"
}
```

### GET /balance/{address}
Get balance for an address.

**Response:**
```json
{
  "address": "alice_address",
  "balance": 100.5
}
```

### GET /block/{index}
Get a specific block by index.

**Response:**
```json
{
  "index": 42,
  "timestamp": 1234567890,
  "transactions": [...],
  "previous_hash": "...",
  "block_hash": "...",
  "nonce": 12345,
  "difficulty": 4,
  "merkle_root": "...",
  "validator": "validator_address",
  "stake_weight": 0.7,
  "work_weight": 0.3
}
```

### GET /transaction/{tx_hash}
Get a specific transaction by hash.

**Response (Confirmed):**
```json
{
  "transaction": {
    "tx_hash": "abc123...",
    "type": "standard",
    "sender": "alice",
    "recipient": "bob",
    "amount": 10,
    "timestamp": 1234567890,
    "metadata": {...}
  },
  "block_index": 42,
  "confirmations": 10
}
```

**Response (Pending):**
```json
{
  "transaction": {...},
  "status": "pending"
}
```

## WebSocket API

Connect to `ws://localhost:8333` for P2P communication.

### Message Types

- `ping` / `pong`: Heartbeat
- `get_peers` / `peers`: Peer discovery
- `get_blocks` / `blocks`: Block synchronization
- `new_block`: Block propagation
- `new_transaction`: Transaction propagation
- `get_chain` / `chain`: Full chain synchronization
- `get_mempool` / `mempool`: Memory pool synchronization
- `version` / `verack`: Version handshake

## Examples

### Submit a Transaction
```bash
curl -X POST http://localhost:8080/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "type": "standard",
    "sender": "alice",
    "recipient": "bob",
    "amount": 10,
    "fee": 0.001
  }'
```

### Check Balance
```bash
curl http://localhost:8080/balance/alice
```

### Get Block
```bash
curl http://localhost:8080/block/0
```

### Get Node Status
```bash
curl http://localhost:8080/status
```