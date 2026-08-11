"""
Unit tests for Transaction classes
"""
import pytest
import time
import hashlib
import json
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'src')

from blockchain import Transaction, TransactionType
from transactions import TransactionBuilder, SmartContract, ScriptOpcode


class TestTransaction:
    """Test basic Transaction functionality"""
    
    def test_transaction_creation(self):
        """Test creating a standard transaction"""
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10.5,
            timestamp=1234567890,
            metadata={"note": "test"}
        )
        
        assert tx.tx_type == TransactionType.STANDARD
        assert tx.sender == "alice"
        assert tx.recipient == "bob"
        assert tx.amount == 10.5
        assert tx.timestamp == 1234567890
        assert tx.metadata["note"] == "test"
        assert tx.tx_hash is not None
    
    def test_transaction_hash_generation(self):
        """Test that transaction hash is generated correctly"""
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10,
            timestamp=1234567890
        )
        
        # Hash should be deterministic - check it exists
        assert tx.tx_hash is not None
        assert len(tx.tx_hash) == 64  # SHA-256 produces 64 hex chars
    
    def test_transaction_validation(self):
        """Test transaction validation"""
        from blockchain import Blockchain
        from wallet import Wallet
        blockchain = Blockchain()
        alice = Wallet.generate()

        # Valid transaction (signed)
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address,
            recipient="DECbob",
            amount=10,
            timestamp=time.time(),
            metadata={"fee": 0.001}
        )
        tx.sign_with(alice)
        assert blockchain.validate_transaction(tx) == True

        # Invalid transaction (negative amount) — rejected before the signature check
        invalid_tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address,
            recipient="DECbob",
            amount=-10,
            timestamp=time.time()
        )
        assert blockchain.validate_transaction(invalid_tx) == False

        # Zero amount is allowed (contract creation, etc), still must be signed
        zero_tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address,
            recipient="DECbob",
            amount=0,
            timestamp=time.time(),
            metadata={"fee": 0.001}
        )
        zero_tx.sign_with(alice)
        assert blockchain.validate_transaction(zero_tx) == True
    
    def test_transaction_to_dict(self):
        """Test transaction serialization"""
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10.5,
            timestamp=1234567890,
            metadata={"note": "payment"}
        )
        
        tx_dict = tx.to_dict()
        
        assert tx_dict["type"] == "standard"
        assert tx_dict["sender"] == "alice"
        assert tx_dict["recipient"] == "bob"
        assert tx_dict["amount"] == 10.5
        assert tx_dict["timestamp"] == 1234567890
        assert tx_dict["metadata"]["note"] == "payment"
        assert tx_dict["tx_hash"] == tx.tx_hash


class TestTransactionBuilder:
    """Test TransactionBuilder functionality"""
    
    def test_create_standard_transaction(self):
        """Test creating a standard transaction"""
        builder = TransactionBuilder()
        tx = builder.create_standard_transaction(
            sender="alice",
            recipient="bob",
            amount=50,
            fee=0.1,
            metadata={"note": "payment"}
        )
        
        assert isinstance(tx, Transaction)
        assert tx.tx_type == TransactionType.STANDARD
        assert tx.sender == "alice"
        assert tx.recipient == "bob"
        assert tx.amount == 50
        assert tx.metadata["fee"] == 0.1
        assert tx.metadata["note"] == "payment"
    
    def test_create_multisig_transaction(self):
        """Test creating a multi-signature transaction"""
        builder = TransactionBuilder()
        tx = builder.create_multisig_transaction(
            senders=["alice", "bob", "charlie"],
            recipient="dave",
            amount=100,
            required_signatures=2,
            fee=0.2
        )
        
        assert isinstance(tx, Transaction)
        assert tx.tx_type == TransactionType.MULTI_SIG
        assert tx.metadata["senders"] == ["alice", "bob", "charlie"]
        assert tx.recipient == "dave"
        assert tx.amount == 100
        assert tx.metadata["required_signatures"] == 2
        assert tx.metadata["fee"] == 0.2
    
    def test_create_time_locked_transaction(self):
        """Test creating a time-locked transaction"""
        builder = TransactionBuilder()
        unlock_time = time.time() + 3600  # 1 hour from now
        
        tx = builder.create_time_locked_transaction(
            sender="alice",
            recipient="bob",
            amount=75,
            unlock_time=unlock_time,
            fee=0.15
        )
        
        assert isinstance(tx, Transaction)
        assert tx.tx_type == TransactionType.TIME_LOCKED
        assert tx.sender == "alice"
        assert tx.recipient == "bob"
        assert tx.amount == 75
        assert tx.metadata["unlock_time"] == unlock_time
        assert tx.metadata["fee"] == 0.15
    
    def test_create_data_storage_transaction(self):
        """Test creating a data storage transaction"""
        builder = TransactionBuilder()
        data = {"document": "important data", "version": 1}
        
        tx = builder.create_data_storage_transaction(
            sender="alice",
            data=data,
            fee=0.5
        )
        
        assert isinstance(tx, Transaction)
        assert tx.tx_type == TransactionType.DATA_STORAGE
        assert tx.sender == "alice"
        assert tx.metadata["data"] == data
        assert "data_hash" in tx.metadata
        assert tx.metadata["fee"] == 0.5
    
    def test_create_contract_transaction(self):
        """Test creating a smart contract transaction"""
        builder = TransactionBuilder()
        contract_code = "contract Token { function transfer() {} }"
        initial_state = {"total_supply": 1000000}
        
        tx = builder.create_smart_contract_transaction(
            sender="alice",
            contract_code=contract_code,
            initial_state=initial_state,
            fee=1.0
        )
        
        assert isinstance(tx, Transaction)
        assert tx.tx_type == TransactionType.SMART_CONTRACT
        assert tx.sender == "alice"
        assert tx.metadata["contract_code"] == contract_code
        assert tx.metadata["initial_state"] == initial_state
        assert tx.metadata["fee"] == 1.0
        assert "contract_id" in tx.metadata


class TestSmartContract:
    """Test SmartContract functionality"""
    
    def test_contract_creation(self):
        """Test smart contract creation"""
        contract_code = """
def transfer(amount):
    return f"Transfer {amount} tokens"
        """
        
        contract = SmartContract(
            contract_id="contract_123",
            code=contract_code,
            state={"balance": 1000},
            creator="alice",
            creation_time=time.time()
        )
        
        assert contract.contract_id == "contract_123"
        assert contract.creator == "alice"
        assert contract.state["balance"] == 1000
        assert contract.is_active == True
    
    def test_contract_execution_is_refused(self):
        """Arbitrary contract code must NOT execute — that path was RCE."""
        contract = SmartContract(
            contract_id="test_contract",
            code="def get_value(): return 42",
            state={"balance": 100},
            creator="alice",
            creation_time=time.time()
        )

        # The node refuses to run arbitrary code rather than exec() it.
        result = contract.execute("get_value", {}, "bob")
        assert isinstance(result, dict)
        assert "error" in result
        assert result != 42

    def test_contract_code_cannot_reach_the_host(self):
        """A payload that would escape the old empty-builtins 'sandbox' must not
        run at all now."""
        malicious = "import os\nos.system('touch /tmp/decoin_rce_probe')"
        contract = SmartContract(
            contract_id="evil_contract",
            code=malicious,
            state={},
            creator="mallory",
            creation_time=time.time()
        )

        result = contract.execute("anything", {}, "mallory")
        assert isinstance(result, dict) and "error" in result
        # The code is retained on-chain as data, never executed.
        assert contract.code == malicious


class TestTransactionTypes:
    """Test different transaction types"""
    
    def test_all_transaction_types(self):
        """Test that all transaction types are defined"""
        types = [
            TransactionType.STANDARD,
            TransactionType.MULTI_SIG,
            TransactionType.TIME_LOCKED,
            TransactionType.DATA_STORAGE,
            TransactionType.SMART_CONTRACT
        ]
        
        for tx_type in types:
            assert isinstance(tx_type.value, str)
            assert len(tx_type.value) > 0
    
    def test_transaction_type_validation(self):
        """Test transaction validation for different types"""
        from blockchain import Blockchain
        from wallet import Wallet
        from signing_helpers import signed_standard, signed_multisig, signed_timelocked
        blockchain = Blockchain()
        alice, bob = Wallet.generate(), Wallet.generate()

        # Standard transaction (signed)
        std_tx = signed_standard(alice, "DECbob", 10)
        assert blockchain.validate_transaction(std_tx) == True

        # Multisig transaction (2-of-2, both signed)
        multi_tx = signed_multisig([alice, bob], "DECcharlie", 20, required=2)
        assert blockchain.validate_transaction(multi_tx) == True

        # Time-locked transaction (signed)
        time_tx = signed_timelocked(alice, "DECbob", 30, time.time() + 3600)
        assert blockchain.validate_transaction(time_tx) == True