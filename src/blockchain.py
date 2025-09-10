import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class TransactionType(Enum):
    STANDARD = "standard"
    SMART_CONTRACT = "smart_contract"
    MULTI_SIG = "multi_sig"
    TIME_LOCKED = "time_locked"
    ATOMIC_SWAP = "atomic_swap"
    DATA_STORAGE = "data_storage"

@dataclass
class Transaction:
    tx_type: TransactionType
    sender: str
    recipient: str
    amount: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None
    tx_hash: Optional[str] = None
    
    def __post_init__(self):
        if not self.tx_hash:
            self.tx_hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        tx_data = {
            'type': self.tx_type.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tx_hash': self.tx_hash,
            'type': self.tx_type.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'signature': self.signature
        }

@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    difficulty: int = 4
    merkle_root: Optional[str] = None
    validator: Optional[str] = None
    stake_weight: float = 0.0
    work_weight: float = 0.0
    block_hash: Optional[str] = None
    
    def __post_init__(self):
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()
        if not self.block_hash:
            self.block_hash = self.calculate_hash()
    
    def calculate_merkle_root(self) -> str:
        if not self.transactions:
            return hashlib.sha256(b'').hexdigest()
        
        hashes = [tx.tx_hash for tx in self.transactions]
        
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            hashes = new_hashes
        
        return hashes[0]
    
    def calculate_hash(self) -> str:
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'validator': self.validator,
            'stake_weight': self.stake_weight,
            'work_weight': self.work_weight
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        target = '0' * difficulty
        while not self.block_hash.startswith(target):
            self.nonce += 1
            self.block_hash = self.calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'merkle_root': self.merkle_root,
            'validator': self.validator,
            'stake_weight': self.stake_weight,
            'work_weight': self.work_weight,
            'block_hash': self.block_hash
        }

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = 4
        self.block_time = 30
        self.max_block_size = 4 * 1024 * 1024
        self.create_genesis_block()
    
    def create_genesis_block(self) -> None:
        genesis_tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="genesis",
            recipient="genesis",
            amount=0,
            timestamp=time.time(),
            metadata={"message": "DeCoin Genesis Block"}
        )
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0"
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        if not self.validate_transaction(transaction):
            return False
        
        self.pending_transactions.append(transaction)
        return True
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        if transaction.amount < 0:
            return False
        
        if len(json.dumps(transaction.metadata)) > 1024:
            return False
        
        if transaction.tx_type == TransactionType.TIME_LOCKED:
            if 'unlock_time' not in transaction.metadata:
                return False
            if transaction.metadata['unlock_time'] <= time.time():
                return False
        
        return True
    
    def create_block(self, validator: str, stake_weight: float = 0.7) -> Block:
        if not self.pending_transactions:
            return None
        
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions[:100],
            previous_hash=self.get_latest_block().block_hash,
            validator=validator,
            stake_weight=stake_weight,
            work_weight=1 - stake_weight,
            difficulty=self.difficulty
        )
        
        return block
    
    def add_block(self, block: Block) -> bool:
        if not self.validate_block(block):
            return False
        
        self.chain.append(block)
        self.pending_transactions = [
            tx for tx in self.pending_transactions 
            if tx not in block.transactions
        ]
        return True
    
    def validate_block(self, block: Block) -> bool:
        if block.index != len(self.chain):
            return False
        
        if block.previous_hash != self.get_latest_block().block_hash:
            return False
        
        if block.merkle_root != block.calculate_merkle_root():
            return False
        
        if not block.block_hash.startswith('0' * self.difficulty):
            return False
        
        for tx in block.transactions:
            if not self.validate_transaction(tx):
                return False
        
        return True
    
    def validate_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.previous_hash != previous_block.block_hash:
                return False
            
            if current_block.block_hash != current_block.calculate_hash():
                return False
            
            if not current_block.block_hash.startswith('0' * self.difficulty):
                return False
        
        return True
    
    def get_balance(self, address: str) -> float:
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.recipient == address:
                    balance += tx.amount
        return balance
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'difficulty': self.difficulty,
            'block_time': self.block_time
        }