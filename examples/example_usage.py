#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from blockchain import Blockchain, Transaction, TransactionType
from transactions import TransactionBuilder
from consensus import HybridConsensus
from wallet import Wallet
import time


def signed_transfer(wallet, recipient, amount, fee=0.001):
    """Build a standard transaction and sign it with the sender's key."""
    tx = Transaction(
        tx_type=TransactionType.STANDARD,
        sender=wallet.address, recipient=recipient, amount=amount,
        timestamp=time.time(), metadata={"fee": fee},
    )
    tx.sign_with(wallet)
    return tx

def demo_standard_transactions():
    print("=== Standard Transaction Demo ===")
    
    blockchain = Blockchain()
    builder = TransactionBuilder()
    
    tx1 = builder.create_standard_transaction(
        sender="alice",
        recipient="bob",
        amount=10.5,
        fee=0.001,
        metadata={"note": "Payment for services"}
    )
    
    print(f"Transaction created: {tx1.tx_hash}")
    print(f"  From: {tx1.sender}")
    print(f"  To: {tx1.recipient}")
    print(f"  Amount: {tx1.amount}")
    print(f"  Metadata: {tx1.metadata}")
    
    blockchain.add_transaction(tx1)
    print(f"Pending transactions: {len(blockchain.pending_transactions)}")

def demo_multisig_transaction():
    print("\n=== Multi-Signature Transaction Demo ===")
    
    builder = TransactionBuilder()
    
    tx = builder.create_multisig_transaction(
        senders=["alice", "bob", "charlie"],
        recipient="dave",
        amount=100,
        required_signatures=2,
        fee=0.002
    )
    
    print(f"MultiSig Transaction: {tx.tx_hash}")
    print(f"  Senders: {tx.metadata['senders']}")
    print(f"  Required signatures: {tx.metadata['required_signatures']}")
    print(f"  Amount: {tx.amount}")

def demo_time_locked_transaction():
    print("\n=== Time-Locked Transaction Demo ===")
    
    builder = TransactionBuilder()
    
    unlock_time = time.time() + 3600
    
    tx = builder.create_time_locked_transaction(
        sender="alice",
        recipient="bob",
        amount=50,
        unlock_time=unlock_time,
        fee=0.001
    )
    
    print(f"Time-Locked Transaction: {tx.tx_hash}")
    print(f"  Locked until: {tx.metadata['locked_until']}")
    print(f"  Amount: {tx.amount}")

def demo_data_storage():
    print("\n=== Data Storage Transaction Demo ===")
    
    builder = TransactionBuilder()
    
    data = {
        "document_hash": "abc123def456",
        "timestamp": time.time(),
        "author": "alice",
        "title": "Important Document",
        "metadata": {
            "version": "1.0",
            "tags": ["legal", "contract"]
        }
    }
    
    tx = builder.create_data_storage_transaction(
        sender="alice",
        data=data,
        fee=0.005
    )
    
    print(f"Data Storage Transaction: {tx.tx_hash}")
    print(f"  Data hash: {tx.metadata['data_hash']}")
    print(f"  Data size: {tx.metadata['data_size']} bytes")

def demo_smart_contract():
    print("\n=== Smart Contract Demo ===")
    
    builder = TransactionBuilder()
    
    contract_code = '''
def transfer(amount, recipient):
    if contract.state['balance'] >= amount:
        contract.state['balance'] -= amount
        contract.state['transfers'].append({
            'to': recipient,
            'amount': amount,
            'timestamp': timestamp
        })
        return True
    return False

def get_balance():
    return contract.state['balance']
'''
    
    initial_state = {
        'balance': 1000,
        'transfers': []
    }
    
    tx = builder.create_smart_contract_transaction(
        sender="alice",
        contract_code=contract_code,
        initial_state=initial_state,
        initial_balance=100,
        fee=0.01
    )
    
    print(f"Smart Contract Transaction: {tx.tx_hash}")
    print(f"  Contract ID: {tx.metadata['contract_id']}")
    print(f"  Initial balance: {tx.amount}")

def demo_mining():
    print("\n=== Mining Demo ===")
    
    blockchain = Blockchain()
    consensus = HybridConsensus(blockchain)
    
    consensus.register_validator("validator1", 5000)
    consensus.register_validator("validator2", 3000)
    consensus.register_validator("validator3", 2000)
    
    builder = TransactionBuilder()
    # Each user is a real wallet now (signatures are required). Fund them from
    # "system" first — a spend the sender cannot cover invalidates the block.
    users = [Wallet.generate() for _ in range(11)]
    for w in users[:10]:
        blockchain.add_transaction(builder.create_standard_transaction(
            sender="system", recipient=w.address, amount=1000, fee=0
        ))
    # Signed transfers between users.
    for i in range(10):
        blockchain.add_transaction(signed_transfer(users[i], users[i + 1].address, i * 10))

    selected = consensus.select_validator()
    print(f"Selected validator: {selected}")
    
    if selected:
        block = blockchain.create_block(selected)
        print(f"Mining block {block.index}...")
        
        success = consensus.mine_block_hybrid(block, selected, timeout=10)
        
        if success:
            print(f"Block mined successfully!")
            print(f"  Hash: {block.block_hash}")
            print(f"  Nonce: {block.nonce}")
            print(f"  Transactions: {len(block.transactions)}")
            
            if blockchain.add_block(block):
                print("Block added to chain")
                
                rewards = consensus.calculate_rewards(block)
                print(f"Rewards distributed: {rewards}")

def demo_blockchain_validation():
    print("\n=== Blockchain Validation Demo ===")
    
    blockchain = Blockchain()
    builder = TransactionBuilder()
    
    # Fund the senders once so every transfer below is covered.
    users = [Wallet.generate() for _ in range(6)]
    for w in users:
        blockchain.add_transaction(builder.create_standard_transaction(
            sender="system", recipient=w.address, amount=1000, fee=0
        ))

    for i in range(3):
        for j in range(5):
            blockchain.add_transaction(signed_transfer(users[j], users[j + 1].address, 10))

        block = blockchain.create_block(f"validator{i}")
        block.mine_block(blockchain.difficulty)
        blockchain.add_block(block)
    
    print(f"Blockchain height: {len(blockchain.chain)}")
    print(f"Is chain valid: {blockchain.validate_chain()}")
    
    for i, block in enumerate(blockchain.chain):
        print(f"Block {i}: {block.block_hash[:16]}... ({len(block.transactions)} txs)")

if __name__ == "__main__":
    demo_standard_transactions()
    demo_multisig_transaction()
    demo_time_locked_transaction()
    demo_data_storage()
    demo_smart_contract()
    demo_mining()
    demo_blockchain_validation()