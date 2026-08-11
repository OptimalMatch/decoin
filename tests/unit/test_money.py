"""Money is integer base units — floats are rejected."""
import time
import pytest

from blockchain import (
    Blockchain, Transaction, TransactionType,
    format_amount, BASE_UNITS_PER_COIN,
)
from wallet import Wallet


def _signed(sender, recipient, amount, fee=0, nonce=0):
    tx = Transaction(
        tx_type=TransactionType.STANDARD,
        sender=sender.address, recipient=recipient, amount=amount,
        timestamp=time.time(), nonce=nonce, metadata={"fee": fee},
    )
    tx.sign_with(sender)
    return tx


class TestIntegerMoney:
    def test_float_amount_is_rejected_at_ingress(self):
        bc = Blockchain()
        tx = _signed(Wallet.generate(), "DECbob", 10.5)
        assert bc.validate_transaction(tx) is False

    def test_bool_amount_is_rejected(self):
        bc = Blockchain()
        tx = _signed(Wallet.generate(), "DECbob", True)  # bool is an int subclass
        assert bc.validate_transaction(tx) is False

    def test_float_fee_makes_a_block_invalid(self):
        bc = Blockchain()
        bc.require_signatures = True
        alice = Wallet.generate()
        bc.add_transaction(Transaction(
            tx_type=TransactionType.STANDARD, sender="system",
            recipient=alice.address, amount=100, timestamp=time.time()))
        # A float fee slips past a naive ingress but must fail block validation.
        tx = _signed(alice, "DECbob", 10, fee=0.001)
        bc.pending_transactions.append(tx)  # force it in
        block = bc.create_block("v")
        block.mine_block(bc.difficulty)
        assert bc.validate_block(block) is False

    def test_integer_amount_is_accepted(self):
        bc = Blockchain()
        assert bc.validate_transaction(_signed(Wallet.generate(), "DECbob", 10)) is True

    def test_format_amount_is_display_only(self):
        assert format_amount(BASE_UNITS_PER_COIN) == "1.00000000"
        assert format_amount(BASE_UNITS_PER_COIN + BASE_UNITS_PER_COIN // 2) == "1.50000000"
        assert format_amount(0) == "0.00000000"
