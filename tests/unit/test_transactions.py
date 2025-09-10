"""
Unit tests for Transaction classes
"""
import pytest
import time
import hashlib
import json
from datetime import datetime, timedelta

from transactions import (
    Transaction, TransactionType, TransactionBuilder,
    MultiSigTransaction, TimeLockTransaction,
    DataStorageTransaction, SmartContractTransaction
)


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
        
        # Hash should be deterministic
        expected_data = f"{tx.tx_type}{tx.sender}{tx.recipient}{tx.amount}{tx.timestamp}{tx.metadata}"
        expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
        
        assert tx.tx_hash == expected_hash
    
    def test_transaction_validation(self):
        """Test transaction validation"""
        # Valid transaction
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=10,
            timestamp=time.time()
        )
        assert tx.validate() == True
        
        # Invalid: negative amount
        tx_invalid = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="bob",
            amount=-10,
            timestamp=time.time()
        )
        assert tx_invalid.validate() == False
        
        # Invalid: same sender and recipient
        tx_invalid2 = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="alice",
            recipient="alice",
            amount=10,
            timestamp=time.time()
        )
        assert tx_invalid2.validate() == False
    
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
    
    def test_create_standard_transaction(self, transaction_builder):
        """Test creating a standard transaction"""
        tx = transaction_builder.create_standard_transaction(
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
    
    def test_create_multisig_transaction(self, transaction_builder):
        """Test creating a multi-signature transaction"""
        tx = transaction_builder.create_multisig_transaction(
            senders=["alice", "bob", "charlie"],
            recipient="dave",
            amount=100,
            required_signatures=2,
            fee=0.2
        )
        
        assert isinstance(tx, MultiSigTransaction)
        assert tx.tx_type == TransactionType.MULTISIG
        assert tx.senders == ["alice", "bob", "charlie"]
        assert tx.recipient == "dave"
        assert tx.amount == 100
        assert tx.required_signatures == 2
        assert tx.metadata["fee"] == 0.2
    
    def test_create_time_locked_transaction(self, transaction_builder):
        """Test creating a time-locked transaction"""
        unlock_time = time.time() + 3600  # 1 hour from now
        
        tx = transaction_builder.create_time_locked_transaction(
            sender="alice",
            recipient="bob",
            amount=75,
            unlock_time=unlock_time,
            fee=0.15
        )
        
        assert isinstance(tx, TimeLockTransaction)
        assert tx.tx_type == TransactionType.TIMELOCKED
        assert tx.sender == "alice"
        assert tx.recipient == "bob"
        assert tx.amount == 75
        assert tx.unlock_time == unlock_time
        assert tx.metadata["fee"] == 0.15
    
    def test_create_data_storage_transaction(self, transaction_builder):
        """Test creating a data storage transaction"""
        data = {"document": "important data", "version": 1}
        
        tx = transaction_builder.create_data_storage_transaction(
            sender="alice",
            data=data,
            fee=0.5
        )
        
        assert isinstance(tx, DataStorageTransaction)
        assert tx.tx_type == TransactionType.DATA
        assert tx.sender == "alice"
        assert tx.data == data
        assert tx.data_hash == hashlib.sha256(json.dumps(data).encode()).hexdigest()
        assert tx.metadata["fee"] == 0.5
    
    def test_create_contract_transaction(self, transaction_builder):
        """Test creating a smart contract transaction"""
        contract_code = "contract Token { function transfer() {} }"
        initial_state = {"total_supply": 1000000}
        
        tx = transaction_builder.create_contract_transaction(
            sender="alice",
            contract_code=contract_code,
            initial_state=initial_state,
            fee=1.0
        )
        
        assert isinstance(tx, SmartContractTransaction)
        assert tx.tx_type == TransactionType.CONTRACT
        assert tx.sender == "alice"
        assert tx.contract_code == contract_code
        assert tx.state == initial_state
        assert tx.metadata["fee"] == 1.0
        assert "contract_id" in tx.metadata


class TestMultiSigTransaction:
    """Test MultiSigTransaction functionality"""
    
    def test_multisig_creation(self):
        """Test multi-signature transaction creation"""
        tx = MultiSigTransaction(
            tx_type=TransactionType.MULTISIG,
            senders=["alice", "bob", "charlie"],
            recipient="dave",
            amount=100,
            required_signatures=2,
            timestamp=time.time()
        )
        
        assert tx.senders == ["alice", "bob", "charlie"]
        assert tx.required_signatures == 2
        assert len(tx.signatures) == 0
    
    def test_add_signature(self):
        """Test adding signatures to multisig transaction"""
        tx = MultiSigTransaction(
            tx_type=TransactionType.MULTISIG,
            senders=["alice", "bob", "charlie"],
            recipient="dave",
            amount=100,
            required_signatures=2,
            timestamp=time.time()
        )
        
        tx.add_signature("alice", "signature_alice")
        assert len(tx.signatures) == 1
        assert tx.signatures["alice"] == "signature_alice"
        
        tx.add_signature("bob", "signature_bob")
        assert len(tx.signatures) == 2
    
    def test_is_valid_signature_count(self):
        """Test signature validation for multisig"""
        tx = MultiSigTransaction(
            tx_type=TransactionType.MULTISIG,
            senders=["alice", "bob", "charlie"],
            recipient="dave",
            amount=100,
            required_signatures=2,
            timestamp=time.time()
        )
        
        # Not enough signatures
        assert tx.is_valid() == False
        
        # Add signatures
        tx.add_signature("alice", "sig1")
        assert tx.is_valid() == False
        
        tx.add_signature("bob", "sig2")
        assert tx.is_valid() == True
        
        # Extra signature is fine
        tx.add_signature("charlie", "sig3")
        assert tx.is_valid() == True


class TestTimeLockTransaction:
    """Test TimeLockTransaction functionality"""
    
    def test_timelock_creation(self):
        """Test time-locked transaction creation"""
        unlock_time = time.time() + 3600
        
        tx = TimeLockTransaction(
            tx_type=TransactionType.TIMELOCKED,
            sender="alice",
            recipient="bob",
            amount=50,
            unlock_time=unlock_time,
            timestamp=time.time()
        )
        
        assert tx.unlock_time == unlock_time
        assert tx.is_locked() == True
    
    def test_is_locked(self, monkeypatch):
        """Test time lock checking"""
        current_time = 1000000
        unlock_time = current_time + 3600
        
        # Mock time.time()
        monkeypatch.setattr(time, "time", lambda: current_time)
        
        tx = TimeLockTransaction(
            tx_type=TransactionType.TIMELOCKED,
            sender="alice",
            recipient="bob",
            amount=50,
            unlock_time=unlock_time,
            timestamp=current_time
        )
        
        # Should be locked initially
        assert tx.is_locked() == True
        
        # Move time forward past unlock time
        monkeypatch.setattr(time, "time", lambda: unlock_time + 1)
        assert tx.is_locked() == False
    
    def test_validate_locked(self, monkeypatch):
        """Test validation of locked transaction"""
        current_time = 1000000
        unlock_time = current_time + 3600
        
        monkeypatch.setattr(time, "time", lambda: current_time)
        
        tx = TimeLockTransaction(
            tx_type=TransactionType.TIMELOCKED,
            sender="alice",
            recipient="bob",
            amount=50,
            unlock_time=unlock_time,
            timestamp=current_time
        )
        
        # Should be valid even when locked
        assert tx.validate() == True


class TestDataStorageTransaction:
    """Test DataStorageTransaction functionality"""
    
    def test_data_storage_creation(self):
        """Test data storage transaction creation"""
        data = {"key": "value", "number": 123}
        
        tx = DataStorageTransaction(
            tx_type=TransactionType.DATA,
            sender="alice",
            data=data,
            timestamp=time.time()
        )
        
        assert tx.data == data
        assert tx.data_hash == hashlib.sha256(json.dumps(data).encode()).hexdigest()
        assert tx.recipient == "network"
        assert tx.amount == 0
    
    def test_data_hash_verification(self):
        """Test data hash is computed correctly"""
        data = {"document": "test", "version": 1}
        
        tx = DataStorageTransaction(
            tx_type=TransactionType.DATA,
            sender="alice",
            data=data,
            timestamp=time.time()
        )
        
        expected_hash = hashlib.sha256(json.dumps(data).encode()).hexdigest()
        assert tx.data_hash == expected_hash
        
        # Modifying data should change hash
        data2 = {"document": "test", "version": 2}
        tx2 = DataStorageTransaction(
            tx_type=TransactionType.DATA,
            sender="alice",
            data=data2,
            timestamp=time.time()
        )
        
        assert tx2.data_hash != tx.data_hash


class TestSmartContractTransaction:
    """Test SmartContractTransaction functionality"""
    
    def test_contract_creation(self):
        """Test smart contract transaction creation"""
        code = "contract Token { }"
        state = {"balance": 1000}
        
        tx = SmartContractTransaction(
            tx_type=TransactionType.CONTRACT,
            sender="alice",
            contract_code=code,
            state=state,
            timestamp=time.time()
        )
        
        assert tx.contract_code == code
        assert tx.state == state
        assert tx.recipient == "contract"
        assert tx.amount == 0
        assert "contract_id" in tx.metadata
    
    def test_execute_contract(self):
        """Test contract execution placeholder"""
        tx = SmartContractTransaction(
            tx_type=TransactionType.CONTRACT,
            sender="alice",
            contract_code="contract Test {}",
            state={"value": 100},
            timestamp=time.time()
        )
        
        # Execute should return state (placeholder implementation)
        result = tx.execute("method", {})
        assert result == tx.state
    
    def test_contract_id_generation(self):
        """Test that contract ID is unique"""
        tx1 = SmartContractTransaction(
            tx_type=TransactionType.CONTRACT,
            sender="alice",
            contract_code="contract A {}",
            state={},
            timestamp=time.time()
        )
        
        tx2 = SmartContractTransaction(
            tx_type=TransactionType.CONTRACT,
            sender="alice",
            contract_code="contract B {}",
            state={},
            timestamp=time.time()
        )
        
        assert tx1.metadata["contract_id"] != tx2.metadata["contract_id"]