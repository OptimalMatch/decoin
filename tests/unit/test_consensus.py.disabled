"""
Unit tests for Consensus mechanisms
"""
import pytest
import time
from unittest.mock import MagicMock, patch
import sys
sys.path.insert(0, 'src')

from consensus import (
    ConsensusManager, ProofOfWork, ProofOfStake, 
    HybridConsensus, ValidatorNode
)
from blockchain import Blockchain, Block, Transaction, TransactionType


class TestProofOfWork:
    """Test Proof of Work consensus"""
    
    def test_pow_initialization(self):
        """Test PoW initialization"""
        blockchain = Blockchain()
        pow = ProofOfWork(blockchain)
        
        assert pow.blockchain == blockchain
        assert pow.difficulty == blockchain.difficulty
    
    def test_mine_block(self):
        """Test PoW block mining"""
        blockchain = Blockchain()
        pow = ProofOfWork(blockchain)
        
        # Create a block
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10,
            timestamp=time.time()
        )
        blockchain.add_transaction(tx)
        block = blockchain.create_block("miner1")
        
        # Mine the block
        mined_block = pow.mine_block(block)
        
        assert mined_block.calculate_hash().startswith("0" * pow.difficulty)
        assert mined_block.nonce > 0
    
    def test_validate_proof(self):
        """Test PoW validation"""
        blockchain = Blockchain()
        pow = ProofOfWork(blockchain)
        
        block = blockchain.create_block("miner1")
        
        # Should be invalid before mining
        assert pow.validate_proof(block) == False
        
        # Mine and validate
        mined_block = pow.mine_block(block)
        assert pow.validate_proof(mined_block) == True
        
        # Tamper with block
        mined_block.nonce += 1
        assert pow.validate_proof(mined_block) == False
    
    def test_calculate_reward(self):
        """Test mining reward calculation"""
        blockchain = Blockchain()
        pow = ProofOfWork(blockchain)
        
        block = blockchain.create_block("miner1")
        reward = pow.calculate_reward(block)
        
        assert reward["miner1"] == 50.0  # Base reward


class TestProofOfStake:
    """Test Proof of Stake consensus"""
    
    def test_pos_initialization(self):
        """Test PoS initialization"""
        blockchain = Blockchain()
        pos = ProofOfStake(blockchain)
        
        assert pos.blockchain == blockchain
        assert len(pos.validators) == 0
        assert pos.minimum_stake == 100
    
    def test_add_validator(self):
        """Test adding validators"""
        blockchain = Blockchain()
        pos = ProofOfStake(blockchain)
        
        pos.add_validator("validator1", 1000)
        assert "validator1" in pos.validators
        assert pos.validators["validator1"] == 1000
        
        # Test minimum stake requirement
        pos.add_validator("validator2", 50)
        assert "validator2" not in pos.validators
    
    def test_select_validator(self):
        """Test validator selection based on stake"""
        blockchain = Blockchain()
        pos = ProofOfStake(blockchain)
        
        # Add validators with different stakes
        pos.add_validator("validator1", 1000)
        pos.add_validator("validator2", 2000)
        pos.add_validator("validator3", 500)
        
        # Selection should be weighted by stake
        selections = {}
        for _ in range(1000):
            validator = pos.select_validator()
            selections[validator] = selections.get(validator, 0) + 1
        
        # validator2 should be selected most often (highest stake)
        assert selections["validator2"] > selections["validator1"]
        assert selections["validator1"] > selections["validator3"]
    
    def test_validate_block(self):
        """Test PoS block validation"""
        blockchain = Blockchain()
        pos = ProofOfStake(blockchain)
        
        pos.add_validator("validator1", 1000)
        
        block = blockchain.create_block("validator1")
        
        # Valid validator
        assert pos.validate_block(block, "validator1") == True
        
        # Invalid validator
        assert pos.validate_block(block, "invalid_validator") == False
    
    def test_calculate_reward(self):
        """Test staking reward calculation"""
        blockchain = Blockchain()
        pos = ProofOfStake(blockchain)
        
        pos.add_validator("validator1", 1000)
        block = blockchain.create_block("validator1")
        
        reward = pos.calculate_reward(block)
        assert "validator1" in reward
        assert reward["validator1"] > 0


class TestHybridConsensus:
    """Test Hybrid PoW/PoS consensus"""
    
    def test_hybrid_initialization(self):
        """Test hybrid consensus initialization"""
        blockchain = Blockchain()
        hybrid = HybridConsensus(blockchain, pow_weight=0.6, pos_weight=0.4)
        
        assert hybrid.pow_weight == 0.6
        assert hybrid.pos_weight == 0.4
        assert hybrid.pow_weight + hybrid.pos_weight == 1.0
    
    def test_select_consensus_method(self):
        """Test consensus method selection"""
        blockchain = Blockchain()
        hybrid = HybridConsensus(blockchain, pow_weight=0.7, pos_weight=0.3)
        
        # Add validators for PoS
        hybrid.pos.add_validator("validator1", 1000)
        
        # Test selection distribution
        methods = {"pow": 0, "pos": 0}
        for _ in range(1000):
            method = hybrid.select_consensus_method()
            methods[method] += 1
        
        # Should roughly match weights
        pow_ratio = methods["pow"] / 1000
        assert 0.6 < pow_ratio < 0.8  # Allow some variance
    
    def test_mine_block_hybrid(self):
        """Test hybrid mining"""
        blockchain = Blockchain()
        hybrid = HybridConsensus(blockchain)
        
        hybrid.pos.add_validator("validator1", 1000)
        
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10,
            timestamp=time.time()
        )
        blockchain.add_transaction(tx)
        
        # Mine with hybrid consensus
        block, method = hybrid.mine_block("miner1")
        
        assert block is not None
        assert method in ["pow", "pos"]
        
        if method == "pow":
            assert block.calculate_hash().startswith("0" * blockchain.difficulty)
        else:
            assert block.validator in hybrid.pos.validators


class TestConsensusManager:
    """Test ConsensusManager"""
    
    def test_manager_initialization(self):
        """Test consensus manager initialization"""
        blockchain = Blockchain()
        manager = ConsensusManager(blockchain)
        
        assert manager.blockchain == blockchain
        assert isinstance(manager.consensus, HybridConsensus)
    
    def test_switch_consensus(self):
        """Test switching consensus mechanisms"""
        blockchain = Blockchain()
        manager = ConsensusManager(blockchain)
        
        # Switch to PoW
        manager.switch_consensus("pow")
        assert isinstance(manager.consensus, ProofOfWork)
        
        # Switch to PoS
        manager.switch_consensus("pos")
        assert isinstance(manager.consensus, ProofOfStake)
        
        # Switch to Hybrid
        manager.switch_consensus("hybrid")
        assert isinstance(manager.consensus, HybridConsensus)
    
    def test_add_validator_through_manager(self):
        """Test adding validators through manager"""
        blockchain = Blockchain()
        manager = ConsensusManager(blockchain)
        
        manager.add_validator("validator1", 1500)
        
        # Should be added to underlying consensus
        assert "validator1" in manager.consensus.pos.validators
        assert manager.consensus.pos.validators["validator1"] == 1500
    
    def test_mine_block_through_manager(self):
        """Test mining through consensus manager"""
        blockchain = Blockchain()
        manager = ConsensusManager(blockchain)
        
        # Add transaction
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=20,
            timestamp=time.time()
        )
        blockchain.add_transaction(tx)
        
        # Mine block
        block = manager.mine_block("miner1")
        
        assert block is not None
        assert len(block.transactions) == 1
        assert block.transactions[0] == tx


class TestValidatorNode:
    """Test ValidatorNode functionality"""
    
    def test_validator_node_creation(self):
        """Test validator node initialization"""
        validator = ValidatorNode(
            address="validator1",
            stake=1000,
            reputation=0.95
        )
        
        assert validator.address == "validator1"
        assert validator.stake == 1000
        assert validator.reputation == 0.95
        assert validator.blocks_validated == 0
        assert validator.is_active == True
    
    def test_validator_update_stake(self):
        """Test updating validator stake"""
        validator = ValidatorNode("validator1", 1000)
        
        validator.update_stake(500)
        assert validator.stake == 1500
        
        validator.update_stake(-200)
        assert validator.stake == 1300
    
    def test_validator_update_reputation(self):
        """Test updating validator reputation"""
        validator = ValidatorNode("validator1", 1000, reputation=0.9)
        
        # Good behavior increases reputation
        validator.update_reputation(0.05)
        assert validator.reputation == 0.95
        
        # Bad behavior decreases reputation
        validator.update_reputation(-0.1)
        assert validator.reputation == 0.85
        
        # Reputation should be capped at 1.0
        validator.update_reputation(0.5)
        assert validator.reputation == 1.0
        
        # Reputation should not go below 0
        validator.update_reputation(-2.0)
        assert validator.reputation == 0.0
    
    def test_validator_deactivation(self):
        """Test validator deactivation"""
        validator = ValidatorNode("validator1", 1000)
        
        assert validator.is_active == True
        
        # Deactivate due to low stake
        validator.stake = 50
        validator.check_eligibility(minimum_stake=100)
        assert validator.is_active == False
        
        # Reactivate with sufficient stake
        validator.stake = 200
        validator.check_eligibility(minimum_stake=100)
        assert validator.is_active == True