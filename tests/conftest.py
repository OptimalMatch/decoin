"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
import sys
import os
from datetime import datetime
from typing import Generator

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from blockchain import Blockchain, Block
from transactions import Transaction, TransactionType, TransactionBuilder
from consensus import ConsensusManager
from node import DeCoinNode


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def blockchain():
    """Create a fresh blockchain instance"""
    return Blockchain()


@pytest.fixture
def transaction_builder():
    """Create a transaction builder instance"""
    return TransactionBuilder()


@pytest.fixture
def sample_transaction():
    """Create a sample transaction"""
    return Transaction(
        tx_type=TransactionType.STANDARD,
        sender="alice",
        recipient="bob",
        amount=10.5,
        timestamp=datetime.now().timestamp(),
        metadata={"note": "test payment"}
    )


@pytest.fixture
def sample_block(sample_transaction):
    """Create a sample block with transactions"""
    return Block(
        index=1,
        timestamp=datetime.now().timestamp(),
        transactions=[sample_transaction],
        previous_hash="00000000000000000000000000000000",
        difficulty=4
    )


@pytest.fixture
def consensus_manager(blockchain):
    """Create a consensus manager instance"""
    return ConsensusManager(blockchain)


@pytest.fixture
def test_node(tmp_path):
    """Create a test node with temporary config"""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "host": "127.0.0.1",
        "port": 8333,
        "validator_address": "test_validator",
        "initial_peers": [],
        "mining_enabled": False,
        "api_enabled": False,
        "api_port": 8080
    }
    
    import json
    config_file.write_text(json.dumps(config_data))
    
    return DeCoinNode(str(config_file))


@pytest.fixture
async def api_client(test_node):
    """Create an API test client"""
    from fastapi.testclient import TestClient
    from api_fastapi import DeCoinAPI
    
    api = DeCoinAPI(test_node)
    client = TestClient(api.app)
    return client


@pytest.fixture
def mock_time(monkeypatch):
    """Mock time for deterministic tests"""
    fixed_time = 1234567890.0
    
    def mock_timestamp():
        return fixed_time
    
    monkeypatch.setattr("time.time", mock_timestamp)
    return fixed_time