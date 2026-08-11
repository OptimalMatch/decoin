"""Real m-of-n multisig verification.

DeCoin's multisig "verification" counted dict entries (len(signatures) <
required), so an empty-but-padded map passed and no signature was ever checked.
These lock the repaired behaviour: the address commits to the signer set and
threshold, and enough signers must actually sign.
"""
import time
import pytest

from blockchain import Blockchain, Transaction, TransactionType
from transactions import TransactionBuilder
from wallet import Wallet, multisig_address


def _ms(signers, required=2, recipient="DECdave", amount=10, fee=0):
    return TransactionBuilder.create_multisig_transaction(
        senders=signers, recipient=recipient, amount=amount,
        required_signatures=required, fee=fee,
    )


class TestMultisig:
    def test_two_of_three_is_valid_with_two_signatures(self):
        a, b, c = Wallet.generate(), Wallet.generate(), Wallet.generate()
        tx = _ms([a.address, b.address, c.address], required=2)
        tx.add_multisig_signature(a)
        tx.add_multisig_signature(b)
        assert tx.is_multisig_valid() is True
        assert tx.is_authorized() is True

    def test_one_signature_is_not_enough(self):
        a, b, c = Wallet.generate(), Wallet.generate(), Wallet.generate()
        tx = _ms([a.address, b.address, c.address], required=2)
        tx.add_multisig_signature(a)
        assert tx.is_multisig_valid() is False

    def test_empty_signatures_map_is_rejected(self):
        # The exact old bug: no signatures attached must NOT pass.
        a, b = Wallet.generate(), Wallet.generate()
        tx = _ms([a.address, b.address], required=2)
        assert tx.is_multisig_valid() is False

    def test_a_non_signers_signature_does_not_count(self):
        a, b, c, mallory = (Wallet.generate() for _ in range(4))
        tx = _ms([a.address, b.address, c.address], required=2)
        tx.add_multisig_signature(a)
        tx.add_multisig_signature(mallory)  # not in the signer set
        assert tx.is_multisig_valid() is False  # only 1 valid signer

    def test_forged_sender_address_is_rejected(self):
        a, b = Wallet.generate(), Wallet.generate()
        tx = _ms([a.address, b.address], required=2)
        tx.add_multisig_signature(a)
        tx.add_multisig_signature(b)
        tx.sender = "DECMSdeadbeef"  # not the address the signer set derives
        assert tx.is_multisig_valid() is False

    def test_multisig_spend_enforced_end_to_end(self):
        bc = Blockchain()
        bc.require_signatures = True
        a, b, c = Wallet.generate(), Wallet.generate(), Wallet.generate()
        signers = [a.address, b.address, c.address]
        ms_addr = multisig_address(signers, 2)

        # Fund the multisig address (minter, no signature needed).
        bc.add_transaction(Transaction(
            tx_type=TransactionType.STANDARD,
            sender="system", recipient=ms_addr, amount=100, timestamp=time.time()
        ))

        tx = _ms(signers, required=2, amount=10, fee=0)
        tx.add_multisig_signature(a)
        tx.add_multisig_signature(b)
        assert bc.add_transaction(tx) is True

        block = bc.create_block("v")
        block.mine_block(bc.difficulty)
        assert bc.add_block(block) is True
        assert bc.get_balance("DECdave") == 10.0
