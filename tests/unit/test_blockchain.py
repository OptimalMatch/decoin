"""
Unit tests for Blockchain class
"""
import pytest
from datetime import datetime
import time

from blockchain import Blockchain, Block
from transactions import Transaction, TransactionType


class TestBlockchain:
    """Test Blockchain functionality"""
    
    def test_genesis_block_creation(self, blockchain):
        """Test that genesis block is created correctly"""
        assert len(blockchain.chain) == 1
        genesis_block = blockchain.chain[0]
        
        assert genesis_block.index == 0
        assert genesis_block.previous_hash == "0"
        assert len(genesis_block.transactions) == 1
        assert genesis_block.transactions[0].sender == "genesis"
        assert genesis_block.transactions[0].recipient == "genesis"
    
    def test_add_transaction(self, blockchain, sample_transaction):
        """Test adding a transaction to pending transactions"""
        result = blockchain.add_transaction(sample_transaction)
        
        assert result == True
        assert len(blockchain.pending_transactions) == 1
        assert blockchain.pending_transactions[0] == sample_transaction
    
    def test_add_invalid_transaction(self, blockchain):
        """Test that invalid transactions are rejected"""
        invalid_tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=-10,  # Invalid negative amount
            timestamp=time.time()
        )
        
        result = blockchain.add_transaction(invalid_tx)
        assert result == False
        assert len(blockchain.pending_transactions) == 0
    
    def test_create_block(self, blockchain, sample_transaction):
        """Test block creation with transactions"""
        blockchain.add_transaction(sample_transaction)
        
        block = blockchain.create_block(
            validator="test_validator",
            stake_weight=1.0,
            work_weight=1.0
        )
        
        assert block.index == 1
        assert block.previous_hash == blockchain.chain[0].calculate_hash()
        assert len(block.transactions) == 1
        assert block.transactions[0] == sample_transaction
        assert block.validator == "test_validator"
    
    def test_add_block(self, blockchain, sample_transaction):
        """Test adding a valid block to the chain"""
        blockchain.add_transaction(sample_transaction)
        block = blockchain.create_block("test_validator")
        
        # Mine the block
        while not block.calculate_hash().startswith("0" * blockchain.difficulty):
            block.nonce += 1
        block.block_hash = block.calculate_hash()
        
        result = blockchain.add_block(block)
        
        assert result == True
        assert len(blockchain.chain) == 2
        assert blockchain.chain[1] == block
        assert len(blockchain.pending_transactions) == 0
    
    def test_validate_chain(self, blockchain):
        """Test blockchain validation"""
        assert blockchain.validate_chain() == True
        
        # Add a valid block
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10,
            timestamp=time.time()
        )
        blockchain.add_transaction(tx)
        block = blockchain.create_block("validator")
        
        # Mine it
        while not block.calculate_hash().startswith("0" * blockchain.difficulty):
            block.nonce += 1
        block.block_hash = block.calculate_hash()
        
        blockchain.add_block(block)
        assert blockchain.validate_chain() == True
        
        # Tamper with the chain
        blockchain.chain[1].transactions[0].amount = 100
        assert blockchain.validate_chain() == False
    
    def test_get_balance(self, blockchain):
        """Test balance calculation"""
        # Initial balance should be 0
        assert blockchain.get_balance("alice") == 0
        assert blockchain.get_balance("bob") == 0
        
        # Add transactions
        tx1 = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="genesis",
            recipient="alice",
            amount=100,
            timestamp=time.time()
        )
        
        tx2 = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=30,
            timestamp=time.time()
        )
        
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        
        # Create and add block
        block = blockchain.create_block("validator")
        while not block.calculate_hash().startswith("0" * blockchain.difficulty):
            block.nonce += 1
        block.block_hash = block.calculate_hash()
        blockchain.add_block(block)
        
        # Check balances
        assert blockchain.get_balance("alice") == 70  # 100 - 30
        assert blockchain.get_balance("bob") == 30
    
    def test_get_latest_block(self, blockchain):
        """Test getting the latest block"""
        latest = blockchain.get_latest_block()
        assert latest == blockchain.chain[-1]
        assert latest.index == 0  # Genesis block
    
    def test_validate_block(self, blockchain):
        """Test individual block validation"""
        # Create a valid block
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10,
            timestamp=time.time()
        )
        blockchain.add_transaction(tx)
        block = blockchain.create_block("validator")
        
        # Should be invalid before mining
        assert blockchain.validate_block(block) == False
        
        # Mine the block
        while not block.calculate_hash().startswith("0" * blockchain.difficulty):
            block.nonce += 1
        block.block_hash = block.calculate_hash()
        
        # Should be valid after mining
        assert blockchain.validate_block(block) == True
        
        # Tamper with block
        block.transactions[0].amount = 1000
        assert blockchain.validate_block(block) == False
    
    def test_to_dict(self, blockchain):
        """Test blockchain serialization to dictionary"""
        chain_dict = blockchain.to_dict()
        
        assert "chain" in chain_dict
        assert "difficulty" in chain_dict
        assert "pending_transactions" in chain_dict
        
        assert chain_dict["difficulty"] == blockchain.difficulty
        assert len(chain_dict["chain"]) == 1  # Genesis block
        assert chain_dict["chain"][0]["index"] == 0


class TestBlock:
    """Test Block functionality"""
    
    def test_block_creation(self, sample_transaction):
        """Test block initialization"""
        block = Block(
            index=1,
            timestamp=1234567890,
            transactions=[sample_transaction],
            previous_hash="00000000",
            difficulty=4
        )
        
        assert block.index == 1
        assert block.timestamp == 1234567890
        assert len(block.transactions) == 1
        assert block.previous_hash == "00000000"
        assert block.difficulty == 4
        assert block.nonce == 0
    
    def test_calculate_hash(self, sample_block):
        """Test block hash calculation"""
        hash1 = sample_block.calculate_hash()
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
        
        # Hash should be deterministic
        hash2 = sample_block.calculate_hash()
        assert hash1 == hash2
        
        # Changing nonce should change hash
        sample_block.nonce += 1
        hash3 = sample_block.calculate_hash()
        assert hash1 != hash3
    
    def test_calculate_merkle_root(self, sample_transaction):
        """Test Merkle root calculation"""
        block = Block(
            index=1,
            timestamp=1234567890,
            transactions=[sample_transaction],
            previous_hash="00000000",
            difficulty=4
        )
        
        merkle_root = block.calculate_merkle_root()
        assert isinstance(merkle_root, str)
        assert len(merkle_root) == 64
        
        # Add another transaction
        tx2 = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="charlie",
            recipient="dave",
            amount=5,
            timestamp=1234567891
        )
        
        block2 = Block(
            index=2,
            timestamp=1234567892,
            transactions=[sample_transaction, tx2],
            previous_hash="00000000",
            difficulty=4
        )
        
        merkle_root2 = block2.calculate_merkle_root()
        assert merkle_root != merkle_root2
    
    def test_mine_block(self, sample_block):
        """Test block mining"""
        difficulty = 2  # Low difficulty for testing
        sample_block.difficulty = difficulty
        
        sample_block.mine_block(difficulty)
        
        block_hash = sample_block.calculate_hash()
        assert block_hash.startswith("0" * difficulty)
        assert sample_block.block_hash == block_hash
        assert sample_block.nonce > 0
    
    def test_to_dict(self, sample_block):
        """Test block serialization"""
        block_dict = sample_block.to_dict()
        
        assert block_dict["index"] == sample_block.index
        assert block_dict["timestamp"] == sample_block.timestamp
        assert block_dict["previous_hash"] == sample_block.previous_hash
        assert block_dict["nonce"] == sample_block.nonce
        assert block_dict["difficulty"] == sample_block.difficulty
        assert len(block_dict["transactions"]) == 1
        assert block_dict["merkle_root"] == sample_block.merkle_root