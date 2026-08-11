"""Helpers for building signed transactions in tests.

Signatures are required by default now, so tests fund/spend with real wallets and
sign. `request_body` maps the chain's transaction-type spelling to the API's.
"""
import time

from blockchain import Transaction, TransactionType
from transactions import TransactionBuilder
from wallet import Wallet, multisig_address

_CHAIN_TO_SCHEMA_TYPE = {
    "standard": "standard",
    "multi_sig": "multisig",
    "time_locked": "timelocked",
    "data_storage": "data",
    "smart_contract": "contract",
}


def signed_standard(wallet, recipient, amount, fee=0, metadata=None, nonce=0):
    md = dict(metadata or {})
    md["fee"] = int(fee)
    tx = Transaction(
        tx_type=TransactionType.STANDARD,
        sender=wallet.address, recipient=recipient, amount=int(amount),
        timestamp=time.time(), nonce=nonce, metadata=md,
    )
    tx.sign_with(wallet)
    return tx


def signed_timelocked(wallet, recipient, amount, unlock_time, fee=0, nonce=0):
    tx = Transaction(
        tx_type=TransactionType.TIME_LOCKED,
        sender=wallet.address, recipient=recipient, amount=int(amount),
        timestamp=time.time(), nonce=nonce,
        metadata={"fee": int(fee), "unlock_time": unlock_time},
    )
    tx.sign_with(wallet)
    return tx


def signed_multisig(wallets, recipient, amount, required, fee=0, nonce=0):
    tx = TransactionBuilder.create_multisig_transaction(
        senders=[w.address for w in wallets], recipient=recipient,
        amount=int(amount), required_signatures=required, fee=int(fee),
    )
    tx.nonce = nonce
    tx.tx_hash = tx.calculate_hash()  # nonce changed, refresh the stored hash
    for w in wallets[:required]:
        tx.add_multisig_signature(w)
    return tx


def request_body(tx):
    """A POST /transaction body for an already-signed transaction."""
    return {
        "sender": tx.sender,
        "recipient": tx.recipient,
        "amount": tx.amount,
        "transaction_type": _CHAIN_TO_SCHEMA_TYPE[tx.tx_type.value],
        "metadata": tx.metadata,
        "nonce": tx.nonce,
        "timestamp": tx.timestamp,
        "signature": tx.signature,
        "public_key": tx.public_key,
    }
