"""Replay protection via per-sender nonces.

A captured, still-valid signed transaction must not be re-usable. The nonce is
part of the signed bytes, so it cannot be changed without invalidating the
signature, and each sender's nonce must strictly increase.
"""
import time
import pytest

from blockchain import Blockchain, Transaction, TransactionType
from wallet import Wallet


def _mine(bc, validator="v"):
    block = bc.create_block(validator)
    block.mine_block(bc.difficulty)
    return bc.add_block(block)


def _fund(bc, address, amount=1000):
    bc.add_transaction(Transaction(
        tx_type=TransactionType.STANDARD,
        sender="system", recipient=address, amount=amount, timestamp=time.time()
    ))


def _signed(wallet, recipient, amount, nonce):
    tx = Transaction(
        tx_type=TransactionType.STANDARD,
        sender=wallet.address, recipient=recipient, amount=amount,
        timestamp=time.time(), nonce=nonce, metadata={"fee": 0},
    )
    tx.sign_with(wallet)
    return tx


class TestReplayProtection:
    def test_replayed_transaction_is_rejected(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        _fund(bc, alice.address, 1000)

        tx = _signed(alice, "DECbob", 10, nonce=0)
        assert bc.add_transaction(tx) is True
        assert _mine(bc) is True
        assert bc.get_balance("DECbob") == 10

        # Re-submit the exact same signed transaction: its nonce is already spent.
        assert bc.add_transaction(tx) is False

        # And a block that tries to include it again does not validate.
        replay_block = bc.create_block("v")
        replay_block.transactions.append(tx)
        replay_block.merkle_root = replay_block.calculate_merkle_root()
        replay_block.mine_block(bc.difficulty)
        assert bc.validate_block(replay_block) is False

    def test_increasing_nonces_from_one_sender_are_accepted(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        _fund(bc, alice.address, 1000)

        assert bc.add_transaction(_signed(alice, "DECbob", 10, nonce=0)) is True
        assert bc.add_transaction(_signed(alice, "DECbob", 10, nonce=1)) is True
        assert _mine(bc) is True
        assert bc.get_balance("DECbob") == 20

    def test_changing_the_nonce_after_signing_breaks_the_signature(self):
        alice = Wallet.generate()
        tx = _signed(alice, "DECbob", 10, nonce=0)
        tx.nonce = 5  # tamper: bump the nonce to dodge the replay check
        assert tx.is_signature_valid() is False

    def test_a_stale_nonce_is_rejected(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        _fund(bc, alice.address, 1000)
        assert bc.add_transaction(_signed(alice, "DECbob", 10, nonce=3)) is True
        assert _mine(bc) is True
        # A later transaction with a lower/equal nonce is refused.
        assert bc.add_transaction(_signed(alice, "DECbob", 10, nonce=3)) is False
        assert bc.add_transaction(_signed(alice, "DECbob", 10, nonce=2)) is False
