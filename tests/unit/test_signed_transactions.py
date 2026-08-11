"""End-to-end signature enforcement.

DeCoin shipped with no transaction signatures; these tests exercise the switch
that fixes it (Blockchain.require_signatures) with real ECDSA wallets.
"""
import time
import pytest

from blockchain import Blockchain, Transaction, TransactionType
from wallet import Wallet


def _fund(bc, address, amount=100):
    """Mint to an address from the system minter (exempt from signatures)."""
    bc.add_transaction(Transaction(
        tx_type=TransactionType.STANDARD,
        sender="system", recipient=address, amount=amount, timestamp=time.time()
    ))


def _mine(bc, validator="v"):
    block = bc.create_block(validator)
    block.mine_block(bc.difficulty)
    return bc.add_block(block)


class TestSignatureEnforcement:
    def test_a_properly_signed_spend_is_accepted(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        _fund(bc, alice.address, 100)

        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address, recipient="DECbob", amount=10, timestamp=time.time()
        )
        tx.sign_with(alice)

        assert bc.add_transaction(tx) is True
        assert _mine(bc) is True
        assert bc.get_balance("DECbob") == 10

    def test_an_unsigned_spend_is_rejected_at_ingress(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        _fund(bc, alice.address, 100)

        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address, recipient="DECbob", amount=10, timestamp=time.time()
        )
        # No sign_with(): the mempool refuses it.
        assert bc.add_transaction(tx) is False

    def test_a_signature_from_the_wrong_key_is_rejected(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice, mallory = Wallet.generate(), Wallet.generate()
        _fund(bc, alice.address, 100)

        # Mallory signs a spend FROM alice's address with his own key.
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address, recipient="DECbob", amount=10, timestamp=time.time()
        )
        tx.sign_with(mallory)  # key does not hash to alice's address
        assert bc.add_transaction(tx) is False

    def test_tampering_after_signing_is_rejected(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        _fund(bc, alice.address, 100)

        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address, recipient="DECbob", amount=10, timestamp=time.time()
        )
        tx.sign_with(alice)
        tx.amount = 1000  # change the amount after signing
        assert tx.is_signature_valid() is False
        assert bc.add_transaction(tx) is False

    def test_minters_do_not_need_signatures(self):
        bc = Blockchain()
        bc.require_signatures = True
        # A system mint (the faucet path) carries no signature and is still fine.
        assert bc.add_transaction(Transaction(
            tx_type=TransactionType.STANDARD,
            sender="system", recipient="DECbob", amount=100, timestamp=time.time()
        )) is True
        assert _mine(bc) is True
        assert bc.get_balance("DECbob") == 100
