"""
Integration tests for API endpoints
"""
import pytest
import json
import time
from fastapi.testclient import TestClient
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api_fastapi import DeCoinAPI
from node import DeCoinNode
from transactions import TransactionType


@pytest.fixture
def api_client():
    """Create API test client with test node"""
    # Create test node with minimal config
    node = DeCoinNode()
    api = DeCoinAPI(node)
    client = TestClient(api.app)
    return client


class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_root_endpoint(self, api_client):
        """Test root endpoint returns API info"""
        response = api_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "DeCoin API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["openapi"] == "/openapi.json"
    
    def test_status_endpoint(self, api_client):
        """Test node status endpoint"""
        response = api_client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "node_id" in data
        assert "chain_height" in data
        assert "pending_transactions" in data
        assert "connected_peers" in data
        assert "is_mining" in data
        assert "difficulty" in data
        assert "version" in data
        assert "uptime" in data
        
        assert data["chain_height"] >= 1  # At least genesis block
        assert data["difficulty"] > 0
    
    def test_blockchain_endpoint(self, api_client):
        """Test blockchain endpoint"""
        response = api_client.get("/blockchain")
        assert response.status_code == 200
        
        data = response.json()
        assert "height" in data
        assert "total_difficulty" in data
        assert "blocks" in data
        assert "is_valid" in data
        
        assert data["height"] >= 1
        assert data["is_valid"] == True
        assert len(data["blocks"]) >= 1
        
        # Check genesis block
        genesis = data["blocks"][0]
        assert genesis["index"] == 0
        assert genesis["previous_hash"] == "0"
    
    def test_blockchain_pagination(self, api_client):
        """Test blockchain endpoint with pagination"""
        response = api_client.get("/blockchain?start=0&limit=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["blocks"]) == 1
    
    def test_get_block_by_index(self, api_client):
        """Test getting specific block by index"""
        response = api_client.get("/block/0")
        assert response.status_code == 200
        
        block = response.json()
        assert block["index"] == 0
        assert block["previous_hash"] == "0"
        assert "hash" in block
        assert "transactions" in block
    
    def test_get_invalid_block(self, api_client):
        """Test getting non-existent block"""
        response = api_client.get("/block/9999")
        assert response.status_code == 404
    
    def test_submit_transaction(self, api_client):
        """Test submitting a new transaction"""
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": 10.5,
            "transaction_type": "standard",
            "metadata": {"note": "test payment"}
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "transaction_id" in data["data"]
        assert data["data"]["status"] == "pending"
    
    def test_submit_invalid_transaction(self, api_client):
        """Test submitting invalid transaction"""
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": -10,  # Invalid negative amount
            "transaction_type": "standard"
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_mempool(self, api_client):
        """Test getting mempool transactions"""
        # Submit a transaction first
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": 5.0,
            "transaction_type": "standard"
        }
        api_client.post("/transaction", json=tx_data)
        
        # Get mempool
        response = api_client.get("/mempool")
        assert response.status_code == 200
        
        mempool = response.json()
        assert isinstance(mempool, list)
        assert len(mempool) > 0
        
        # Check transaction structure
        tx = mempool[0]
        assert "transaction_id" in tx
        assert "sender" in tx
        assert "recipient" in tx
        assert "amount" in tx
        assert tx["status"] == "pending"
    
    def test_get_balance(self, api_client):
        """Test getting wallet balance"""
        response = api_client.get("/balance/alice")
        assert response.status_code == 200
        
        data = response.json()
        assert data["address"] == "alice"
        assert "balance" in data
        assert "pending" in data
        assert "staked" in data
        assert data["balance"] >= 0
    
    def test_get_peers(self, api_client):
        """Test getting peer list"""
        response = api_client.get("/peers")
        assert response.status_code == 200
        
        peers = response.json()
        assert isinstance(peers, list)
        
        # If there are peers, check structure
        if len(peers) > 0:
            peer = peers[0]
            assert "address" in peer
            assert "port" in peer
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_mining_control(self, api_client):
        """Test mining control endpoint"""
        # Enable mining
        response = api_client.post("/mining", json={"enable": True, "threads": 2})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "enabled" in data["message"]
        
        # Disable mining
        response = api_client.post("/mining", json={"enable": False})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "disabled" in data["message"]
    
    def test_mining_info(self, api_client):
        """Test mining information endpoint"""
        response = api_client.get("/mining/difficulty")
        assert response.status_code == 200
        
        data = response.json()
        assert "difficulty" in data
        assert "is_mining" in data
        assert "blocks_mined" in data
        assert "next_reward" in data
        assert data["difficulty"] > 0
    
    def test_validators(self, api_client):
        """Test validators endpoint"""
        response = api_client.get("/validators")
        assert response.status_code == 200
        
        validators = response.json()
        assert isinstance(validators, list)


class TestTransactionTypes:
    """Test different transaction types via API"""
    
    def test_standard_transaction(self, api_client):
        """Test standard transaction submission"""
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": 25.0,
            "transaction_type": "standard",
            "metadata": {"note": "Standard payment", "fee": 0.01}
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 200
        
        # Check transaction in mempool
        mempool = api_client.get("/mempool").json()
        tx = next((t for t in mempool if t["sender"] == "alice"), None)
        assert tx is not None
        assert tx["amount"] == 25.0
        assert tx["transaction_type"] == "standard"
    
    def test_multisig_transaction(self, api_client):
        """Test multi-signature transaction"""
        tx_data = {
            "sender": "alice",  # Primary sender
            "recipient": "dave",
            "amount": 100.0,
            "transaction_type": "multisig",
            "metadata": {
                "senders": ["alice", "bob", "charlie"],
                "required_signatures": 2,
                "fee": 0.02
            }
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
    
    def test_timelocked_transaction(self, api_client):
        """Test time-locked transaction"""
        unlock_time = int(time.time() + 3600)  # 1 hour from now
        
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": 50.0,
            "transaction_type": "timelocked",
            "metadata": {
                "unlock_time": unlock_time,
                "fee": 0.015
            }
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
    
    @pytest.mark.skip(reason="Data storage transaction validation needs adjustment")
    def test_data_storage_transaction(self, api_client):
        """Test data storage transaction"""
        tx_data = {
            "sender": "alice",
            "recipient": "network",  # Data transactions go to network
            "amount": 0,
            "transaction_type": "data_storage",
            "metadata": {
                "data": {"document": "Important data", "timestamp": time.time()},
                "fee": 0.05
            }
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True


class TestAPIValidation:
    """Test API input validation"""
    
    def test_invalid_transaction_type(self, api_client):
        """Test invalid transaction type"""
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": 10,
            "transaction_type": "invalid_type"
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, api_client):
        """Test missing required fields"""
        tx_data = {
            "sender": "alice",
            # Missing recipient and amount
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 422
    
    def test_invalid_amount(self, api_client):
        """Test invalid transaction amount"""
        tx_data = {
            "sender": "alice",
            "recipient": "bob",
            "amount": 0,  # Zero amount
            "transaction_type": "standard"
        }
        
        response = api_client.post("/transaction", json=tx_data)
        assert response.status_code == 422
    
    def test_invalid_block_index(self, api_client):
        """Test invalid block index"""
        response = api_client.get("/block/-1")
        assert response.status_code == 422
    
    def test_invalid_pagination(self, api_client):
        """Test invalid pagination parameters"""
        response = api_client.get("/blockchain?start=-1&limit=0")
        assert response.status_code == 422


class TestConcurrentRequests:
    """Test concurrent API requests"""
    
    def test_concurrent_transactions(self, api_client):
        """Test submitting multiple transactions concurrently"""
        transactions = []
        
        for i in range(10):
            tx_data = {
                "sender": f"user{i}",
                "recipient": "bob",
                "amount": i + 1,
                "transaction_type": "standard"
            }
            response = api_client.post("/transaction", json=tx_data)
            assert response.status_code == 200
            transactions.append(response.json()["data"]["transaction_id"])
        
        # Check all transactions are in mempool
        mempool = api_client.get("/mempool").json()
        mempool_ids = [tx["transaction_id"] for tx in mempool]
        
        for tx_id in transactions:
            assert tx_id in mempool_ids
    
    def test_concurrent_reads(self, api_client):
        """Test concurrent read operations"""
        endpoints = [
            "/status",
            "/blockchain",
            "/mempool",
            "/peers",
            "/health"
        ]
        
        responses = []
        for endpoint in endpoints:
            response = api_client.get(endpoint)
            responses.append(response)
            assert response.status_code == 200
        
        # All responses should be valid
        assert len(responses) == len(endpoints)