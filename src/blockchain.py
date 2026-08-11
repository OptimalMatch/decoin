import hashlib
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from parallel_validation import ParallelTransactionValidator

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
    public_key: Optional[str] = None
    tx_hash: Optional[str] = None

    def __post_init__(self):
        if not self.tx_hash:
            self.tx_hash = self.calculate_hash()

    # Metadata keys that CARRY signatures rather than being signed content. They
    # are excluded from signing_bytes so that attaching signatures (multisig)
    # does not change the very bytes those signatures commit to.
    _UNSIGNED_META_KEYS = ('signatures', 'public_keys')

    def signing_bytes(self) -> bytes:
        """The canonical content a signature commits to: everything that defines
        the transaction, but NOT the signature, public key, or tx_hash (which are
        derived from it). Signing and hashing cover exactly the same bytes."""
        meta = {k: v for k, v in self.metadata.items()
                if k not in self._UNSIGNED_META_KEYS}
        tx_data = {
            'type': self.tx_type.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'metadata': meta
        }
        return json.dumps(tx_data, sort_keys=True).encode()

    def calculate_hash(self) -> str:
        return hashlib.sha256(self.signing_bytes()).hexdigest()

    def sign_with(self, wallet) -> None:
        """Attach the wallet's public key and a signature over signing_bytes.
        The sender address must already be the wallet's address, or the signature
        will not verify (the key would not hash to the sender)."""
        self.public_key = wallet.public_key_hex
        self.signature = wallet.sign(self.signing_bytes())

    def is_signature_valid(self) -> bool:
        """True only if this transaction carries a signature and public key, the
        public key hashes to the sender address, and the signature verifies over
        the transaction's content. This is what makes an address spendable only
        by the holder of its private key."""
        from wallet import verify_signature, address_from_public_key_hex
        if not self.signature or not self.public_key:
            return False
        try:
            if address_from_public_key_hex(self.public_key) != self.sender:
                return False
        except (ValueError, TypeError):
            return False
        return verify_signature(self.public_key, self.signature, self.signing_bytes())

    def is_authorized(self) -> bool:
        """Whether this transaction is validly authorized by its owner(s):
        m-of-n for a multisig transaction, a single signature for the rest."""
        if self.tx_type == TransactionType.MULTI_SIG:
            return self.is_multisig_valid()
        return self.is_signature_valid()

    def add_multisig_signature(self, wallet) -> None:
        """One signer of an m-of-n transaction attaches their signature and key.
        All signers sign the SAME signing_bytes (which excludes the signatures),
        so signatures can be collected one at a time without changing the payload."""
        self.metadata.setdefault('signatures', {})[wallet.address] = wallet.sign(self.signing_bytes())
        self.metadata.setdefault('public_keys', {})[wallet.address] = wallet.public_key_hex

    def is_multisig_valid(self) -> bool:
        """True only if the sender address is the m-of-n address derived from the
        declared signer set and threshold, AND at least `required_signatures` of
        those signers have attached a valid signature. The old code merely counted
        dict entries, so an empty-but-padded signatures map passed."""
        from wallet import verify_signature, address_from_public_key_hex, multisig_address
        md = self.metadata
        signers = md.get('senders', [])
        required = md.get('required_signatures', 0)
        sigs = md.get('signatures', {})
        pubs = md.get('public_keys', {})
        if not signers or not isinstance(required, int) or required <= 0:
            return False
        # The address must commit to exactly this signer set and threshold.
        if self.sender != multisig_address(signers, required):
            return False
        message = self.signing_bytes()
        valid = 0
        for addr in signers:
            sig, pub = sigs.get(addr), pubs.get(addr)
            if not sig or not pub:
                continue
            try:
                if address_from_public_key_hex(pub) != addr:
                    continue
            except (ValueError, TypeError):
                continue
            if verify_signature(pub, sig, message):
                valid += 1
        return valid >= required

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tx_hash': self.tx_hash,
            'type': self.tx_type.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'signature': self.signature,
            'public_key': self.public_key
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

        # Hash each transaction's CONTENT, not its stored tx_hash. A stored hash
        # can go stale (tampering) or arrive forged over the wire; recomputing
        # here is what makes the Merkle root — and the block hash above it — a
        # real commitment to the transactions the block actually contains.
        hashes = [tx.calculate_hash() for tx in self.transactions]
        
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
        self.difficulty = 1  # Minimum difficulty for maximum block production
        self.block_time = 2  # Reduced to 2 seconds for very fast blocks
        self.max_block_size = 10 * 1024 * 1024
        self.parallel_validator = ParallelTransactionValidator(self, max_workers=4)
        # When True, every non-minter transaction must carry a valid signature
        # whose public key hashes to the sender address. DeCoin shipped with no
        # signatures at all; this is the switch that makes an address spendable
        # only by its key-holder.
        self.require_signatures = True
        self.create_genesis_block()
    
    def create_genesis_block(self) -> None:
        # Use fixed timestamp for consistent genesis block across all nodes
        GENESIS_TIMESTAMP = 1700000000.0  # Fixed timestamp: Nov 14, 2023
        genesis_tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender="genesis",
            recipient="genesis",
            amount=0,
            timestamp=GENESIS_TIMESTAMP,
            metadata={"message": "DeCoin Genesis Block"}
        )
        genesis_block = Block(
            index=0,
            timestamp=GENESIS_TIMESTAMP,
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
    
    # Senders that mint coin rather than spend it: the genesis grant, the
    # coinbase/mining reward, and the faucet. They are exempt from balance checks
    # because that is precisely how new coin enters circulation.
    MINTERS = {'genesis', 'mining_reward', 'system', 'coinbase'}

    def validate_transaction(self, transaction: Transaction) -> bool:
        # Mempool admission is a STRUCTURAL check. The consensus balance rule —
        # every spend must be covered — is enforced when a block is validated
        # (see validate_block), because a transaction can be funded by an earlier
        # transaction in the same block, which no per-transaction check can see.
        if transaction.amount < 0:
            return False
        if len(json.dumps(transaction.metadata)) > 1024:
            return False
        if (self.require_signatures
                and transaction.sender not in self.MINTERS
                and not transaction.is_authorized()):
            return False
        return True
    
    def create_block(self, validator: str, stake_weight: float = 0.7) -> Block:
        # Create coinbase transaction (mining reward)
        block_height = len(self.chain)
        halvings = block_height // 100000  # Halving every 100,000 blocks
        base_reward = 50
        block_reward = base_reward / (2 ** halvings)

        coinbase_tx = Transaction(
            sender="system",
            recipient=validator,
            amount=block_reward,
            timestamp=time.time(),
            tx_type=TransactionType.STANDARD,
            metadata={"type": "coinbase", "block_height": block_height}
        )

        # Include pending transactions plus the coinbase transaction
        # Always create a block even if there are no pending transactions (coinbase only)
        # Increased from 99 to 500 transactions per block for higher TPS
        transactions = [coinbase_tx] + self.pending_transactions[:500]

        block = Block(
            index=block_height,
            timestamp=time.time(),
            transactions=transactions,
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
    
    def _confirmed_balances(self) -> Dict[str, float]:
        """Balances from the committed chain only, as a mutable map we can
        replay a candidate block against."""
        balances: Dict[str, float] = {}
        for blk in self.chain:
            for tx in blk.transactions:
                fee = tx.metadata.get('fee', 0)
                if tx.sender not in self.MINTERS:
                    balances[tx.sender] = balances.get(tx.sender, 0) - (tx.amount + fee)
                balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
        return balances

    def _transactions_cover_their_spends(self, transactions: List[Transaction]) -> bool:
        """Validate a block's transactions IN ORDER against a running balance, so
        a transaction funded earlier in the same block is honoured — and a spend
        the sender cannot cover makes the whole block invalid. Order matters,
        which is exactly why this cannot be parallelised across transactions."""
        balances = self._confirmed_balances()
        for tx in transactions:
            if tx.amount < 0:
                return False
            fee = tx.metadata.get('fee', 0)
            if tx.sender not in self.MINTERS:
                # The spender must own the address: a valid signature whose key
                # hashes to the sender. Minters (genesis/coinbase/faucet) create
                # coin and have no key, so they are exempt.
                if self.require_signatures and not tx.is_authorized():
                    return False
                if balances.get(tx.sender, 0) < tx.amount + fee:
                    return False
                balances[tx.sender] = balances.get(tx.sender, 0) - (tx.amount + fee)
            balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
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

        # Integrity: the stored hash must match the block's actual contents.
        # Without this a tampered block — or a hash forged and sent over the
        # network — sails through, because everything above trusts block_hash.
        if block.block_hash != block.calculate_hash():
            return False

        # Consensus rule: every spend in the block must be covered.
        if not self._transactions_cover_their_spends(block.transactions):
            return False

        return True
    
    def validate_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.previous_hash != previous_block.block_hash:
                return False

            # The stored Merkle root must still match the transactions it commits
            # to, so tampering with any transaction is caught here — calculate_hash
            # trusts the stored root, this check does not.
            if current_block.merkle_root != current_block.calculate_merkle_root():
                return False

            if current_block.block_hash != current_block.calculate_hash():
                return False

            if not current_block.block_hash.startswith('0' * self.difficulty):
                return False

        return True
    
    def get_balance(self, address: str, include_pending: bool = True) -> float:
        balance = 0
        # Calculate confirmed balance from blockchain
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= (tx.amount + tx.metadata.get('fee', 0))
                if tx.recipient == address:
                    balance += tx.amount

        # Subtract pending outgoing transactions to prevent double-spending
        if include_pending:
            for tx in self.pending_transactions:
                if tx.sender == address:
                    balance -= (tx.amount + tx.metadata.get('fee', 0))

        return balance
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'difficulty': self.difficulty,
            'block_time': self.block_time
        }