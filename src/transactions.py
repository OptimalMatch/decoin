import hashlib
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from blockchain import Transaction, TransactionType

class ScriptOpcode(Enum):
    OP_DUP = "OP_DUP"
    OP_HASH160 = "OP_HASH160"
    OP_EQUALVERIFY = "OP_EQUALVERIFY"
    OP_CHECKSIG = "OP_CHECKSIG"
    OP_CHECKMULTISIG = "OP_CHECKMULTISIG"
    OP_CHECKLOCKTIMEVERIFY = "OP_CHECKLOCKTIMEVERIFY"
    OP_CHECKSEQUENCEVERIFY = "OP_CHECKSEQUENCEVERIFY"
    OP_RETURN = "OP_RETURN"
    OP_IF = "OP_IF"
    OP_ELSE = "OP_ELSE"
    OP_ENDIF = "OP_ENDIF"
    OP_VERIFY = "OP_VERIFY"
    OP_EQUAL = "OP_EQUAL"
    OP_ADD = "OP_ADD"
    OP_SUB = "OP_SUB"
    OP_MUL = "OP_MUL"
    OP_DIV = "OP_DIV"
    OP_MOD = "OP_MOD"

@dataclass
class SmartContract:
    contract_id: str
    code: str
    state: Dict[str, Any]
    creator: str
    creation_time: float
    balance: float = 0
    is_active: bool = True
    
    def execute(self, function: str, params: Dict[str, Any], sender: str) -> Any:
        context = {
            'contract': self,
            'sender': sender,
            'params': params,
            'timestamp': time.time()
        }
        
        try:
            exec(self.code, {'__builtins__': {}}, context)
            if function in context:
                return context[function]()
        except Exception as e:
            return {'error': str(e)}
        
        return None

class TransactionBuilder:
    @staticmethod
    def create_standard_transaction(
        sender: str,
        recipient: str,
        amount: float,
        fee: float = 0.001,
        metadata: Optional[Dict] = None
    ) -> Transaction:
        tx_metadata = metadata or {}
        tx_metadata['fee'] = fee
        
        return Transaction(
            tx_type=TransactionType.STANDARD,
            sender=sender,
            recipient=recipient,
            amount=amount,
            timestamp=time.time(),
            metadata=tx_metadata
        )
    
    @staticmethod
    def create_multisig_transaction(
        senders: List[str],
        recipient: str,
        amount: float,
        required_signatures: int,
        fee: float = 0.002
    ) -> Transaction:
        metadata = {
            'fee': fee,
            'senders': senders,
            'required_signatures': required_signatures,
            'signatures': {}
        }
        
        return Transaction(
            tx_type=TransactionType.MULTI_SIG,
            sender=','.join(senders),
            recipient=recipient,
            amount=amount,
            timestamp=time.time(),
            metadata=metadata
        )
    
    @staticmethod
    def create_time_locked_transaction(
        sender: str,
        recipient: str,
        amount: float,
        unlock_time: float,
        fee: float = 0.001
    ) -> Transaction:
        metadata = {
            'fee': fee,
            'unlock_time': unlock_time,
            'locked_until': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unlock_time))
        }
        
        return Transaction(
            tx_type=TransactionType.TIME_LOCKED,
            sender=sender,
            recipient=recipient,
            amount=amount,
            timestamp=time.time(),
            metadata=metadata
        )
    
    @staticmethod
    def create_atomic_swap_transaction(
        party_a: str,
        party_b: str,
        amount_a: float,
        amount_b: float,
        secret_hash: str,
        timeout: int = 3600,
        fee: float = 0.003
    ) -> Transaction:
        metadata = {
            'fee': fee,
            'party_a': party_a,
            'party_b': party_b,
            'amount_a': amount_a,
            'amount_b': amount_b,
            'secret_hash': secret_hash,
            'timeout': timeout,
            'expiry': time.time() + timeout
        }
        
        return Transaction(
            tx_type=TransactionType.ATOMIC_SWAP,
            sender=party_a,
            recipient=party_b,
            amount=amount_a,
            timestamp=time.time(),
            metadata=metadata
        )
    
    @staticmethod
    def create_data_storage_transaction(
        sender: str,
        data: Dict[str, Any],
        fee: float = 0.005
    ) -> Transaction:
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
        metadata = {
            'fee': fee,
            'data': data,
            'data_hash': data_hash,
            'data_size': len(json.dumps(data))
        }
        
        return Transaction(
            tx_type=TransactionType.DATA_STORAGE,
            sender=sender,
            recipient="0x0",
            amount=0,
            timestamp=time.time(),
            metadata=metadata
        )
    
    @staticmethod
    def create_smart_contract_transaction(
        sender: str,
        contract_code: str,
        initial_state: Dict[str, Any],
        initial_balance: float = 0,
        fee: float = 0.01
    ) -> Transaction:
        contract_id = hashlib.sha256(
            (contract_code + json.dumps(initial_state) + str(time.time())).encode()
        ).hexdigest()[:16]
        
        metadata = {
            'fee': fee,
            'contract_id': contract_id,
            'contract_code': contract_code,
            'initial_state': initial_state,
            'creation_time': time.time()
        }
        
        return Transaction(
            tx_type=TransactionType.SMART_CONTRACT,
            sender=sender,
            recipient=f"contract_{contract_id}",
            amount=initial_balance,
            timestamp=time.time(),
            metadata=metadata
        )

class TransactionValidator:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.smart_contracts: Dict[str, SmartContract] = {}
    
    def validate_transaction(self, tx: Transaction) -> bool:
        validators = {
            TransactionType.STANDARD: self._validate_standard,
            TransactionType.MULTI_SIG: self._validate_multisig,
            TransactionType.TIME_LOCKED: self._validate_time_locked,
            TransactionType.ATOMIC_SWAP: self._validate_atomic_swap,
            TransactionType.DATA_STORAGE: self._validate_data_storage,
            TransactionType.SMART_CONTRACT: self._validate_smart_contract
        }
        
        validator = validators.get(tx.tx_type)
        if not validator:
            return False
        
        return validator(tx)
    
    def _validate_standard(self, tx: Transaction) -> bool:
        if tx.amount <= 0:
            return False

        # Allow system transactions (faucet, coinbase)
        if tx.sender == "system":
            return True

        sender_balance = self.blockchain.get_balance(tx.sender)
        total_amount = tx.amount + tx.metadata.get('fee', 0)

        return sender_balance >= total_amount
    
    def _validate_multisig(self, tx: Transaction) -> bool:
        metadata = tx.metadata
        required_sigs = metadata.get('required_signatures', 0)
        signatures = metadata.get('signatures', {})
        
        if len(signatures) < required_sigs:
            return False
        
        senders = metadata.get('senders', [])
        total_balance = sum(self.blockchain.get_balance(s) for s in senders)
        total_amount = tx.amount + metadata.get('fee', 0)
        
        return total_balance >= total_amount
    
    def _validate_time_locked(self, tx: Transaction) -> bool:
        unlock_time = tx.metadata.get('unlock_time', 0)
        
        if unlock_time <= time.time():
            return False
        
        sender_balance = self.blockchain.get_balance(tx.sender)
        total_amount = tx.amount + tx.metadata.get('fee', 0)
        
        return sender_balance >= total_amount
    
    def _validate_atomic_swap(self, tx: Transaction) -> bool:
        metadata = tx.metadata
        expiry = metadata.get('expiry', 0)
        
        if time.time() > expiry:
            return False
        
        party_a = metadata.get('party_a')
        party_b = metadata.get('party_b')
        amount_a = metadata.get('amount_a', 0)
        amount_b = metadata.get('amount_b', 0)
        
        balance_a = self.blockchain.get_balance(party_a)
        balance_b = self.blockchain.get_balance(party_b)
        
        return balance_a >= amount_a and balance_b >= amount_b
    
    def _validate_data_storage(self, tx: Transaction) -> bool:
        data_size = tx.metadata.get('data_size', 0)
        
        if data_size > 1024:
            return False
        
        sender_balance = self.blockchain.get_balance(tx.sender)
        fee = tx.metadata.get('fee', 0)
        
        return sender_balance >= fee
    
    def _validate_smart_contract(self, tx: Transaction) -> bool:
        contract_code = tx.metadata.get('contract_code', '')
        
        if len(contract_code) > 10000:
            return False
        
        try:
            compile(contract_code, '<string>', 'exec')
        except SyntaxError:
            return False
        
        sender_balance = self.blockchain.get_balance(tx.sender)
        total_amount = tx.amount + tx.metadata.get('fee', 0)
        
        return sender_balance >= total_amount
    
    def execute_smart_contract(self, tx: Transaction) -> Any:
        if tx.tx_type != TransactionType.SMART_CONTRACT:
            return None
        
        contract_id = tx.metadata.get('contract_id')
        
        if contract_id not in self.smart_contracts:
            contract = SmartContract(
                contract_id=contract_id,
                code=tx.metadata.get('contract_code'),
                state=tx.metadata.get('initial_state', {}),
                creator=tx.sender,
                creation_time=tx.timestamp,
                balance=tx.amount
            )
            self.smart_contracts[contract_id] = contract
            return {'status': 'created', 'contract_id': contract_id}
        
        return None

class TransactionPool:
    def __init__(self, max_size: int = 10000):
        self.transactions: List[Transaction] = []
        self.max_size = max_size
        self.transaction_index: Dict[str, Transaction] = {}
    
    def add_transaction(self, tx: Transaction) -> bool:
        if len(self.transactions) >= self.max_size:
            return False
        
        if tx.tx_hash in self.transaction_index:
            return False
        
        self.transactions.append(tx)
        self.transaction_index[tx.tx_hash] = tx
        
        self.transactions.sort(key=lambda x: x.metadata.get('fee', 0), reverse=True)
        
        return True
    
    def remove_transaction(self, tx_hash: str) -> Optional[Transaction]:
        if tx_hash not in self.transaction_index:
            return None
        
        tx = self.transaction_index[tx_hash]
        self.transactions.remove(tx)
        del self.transaction_index[tx_hash]
        
        return tx
    
    def get_transactions(self, count: int) -> List[Transaction]:
        return self.transactions[:count]
    
    def clear_transactions(self, tx_hashes: List[str]) -> None:
        for tx_hash in tx_hashes:
            self.remove_transaction(tx_hash)