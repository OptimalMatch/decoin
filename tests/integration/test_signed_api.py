"""API accepts a client-signed transaction and rejects forgeries.

This exercises the migration path toward signatures-required: POST /transaction
now takes a transaction the client signed locally (timestamp + signature +
public_key), which the server reconstructs exactly and verifies.
"""
import time
import pytest
from fastapi.testclient import TestClient

from api_fastapi import DeCoinAPI
from node import DeCoinNode
from blockchain import Transaction, TransactionType
from wallet import Wallet


def _enforcing_client():
    node = DeCoinNode()
    node.blockchain.require_signatures = True
    return TestClient(DeCoinAPI(node).app)


def _body(tx: Transaction):
    return {
        "sender": tx.sender,
        "recipient": tx.recipient,
        "amount": tx.amount,
        "transaction_type": tx.tx_type.value,
        "metadata": tx.metadata,
        "timestamp": tx.timestamp,
        "signature": tx.signature,
        "public_key": tx.public_key,
    }


# amount is a float on purpose: the JSON round-trip coerces it to float, so the
# client must sign the same float or the reconstructed signing bytes differ
# ("5" vs "5.0"). This fragility is itself an argument for integer money — see
# the float-money repair.
def _signed_standard(wallet: Wallet, recipient="DECbob", amount=5.0):
    tx = Transaction(
        tx_type=TransactionType.STANDARD,
        sender=wallet.address, recipient=recipient, amount=amount,
        timestamp=time.time(), metadata={"fee": 0.001},
    )
    tx.sign_with(wallet)
    return tx


class TestSignedSubmission:
    def test_valid_signed_transaction_is_accepted(self):
        client = _enforcing_client()
        tx = _signed_standard(Wallet.generate())
        r = client.post("/transaction", json=_body(tx))
        assert r.status_code == 200

    def test_unsigned_transaction_is_rejected_under_enforcement(self):
        client = _enforcing_client()
        body = _body(_signed_standard(Wallet.generate()))
        body["signature"] = None
        body["public_key"] = None
        r = client.post("/transaction", json=body)
        assert r.status_code == 400

    def test_amount_tampered_after_signing_is_rejected(self):
        client = _enforcing_client()
        body = _body(_signed_standard(Wallet.generate()))
        body["amount"] = 5000  # changed after the signature was made
        r = client.post("/transaction", json=body)
        assert r.status_code == 400

    def test_signature_from_a_different_key_is_rejected(self):
        client = _enforcing_client()
        alice, mallory = Wallet.generate(), Wallet.generate()
        tx = Transaction(
            tx_type=TransactionType.STANDARD,
            sender=alice.address, recipient="DECbob", amount=5,
            timestamp=time.time(), metadata={"fee": 0.001},
        )
        tx.sign_with(mallory)  # signs alice's spend with the wrong key
        r = client.post("/transaction", json=_body(tx))
        assert r.status_code == 400
