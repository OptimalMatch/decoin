"""The node accepts transactions signed by the browser wallet.

Uses the shared cross-language vectors (frontend/test/vectors.json). Because the
JS wallet is proven to reproduce these byte-for-byte (frontend/test/wallet.test.mjs),
a signature the node accepts here is one the frontend can produce.
"""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from api_fastapi import DeCoinAPI
from node import DeCoinNode
from blockchain import Transaction, TransactionType
from wallet import verify_signature, address_from_public_key_hex

VECTORS = pathlib.Path(__file__).parents[2] / "frontend" / "test" / "vectors.json"
pytestmark = pytest.mark.skipif(not VECTORS.exists(), reason="frontend vectors not generated")


def _load():
    return json.loads(VECTORS.read_text())


def _tx(v):
    return Transaction(
        tx_type=TransactionType.STANDARD, sender=v["address"], recipient=v["recipient"],
        amount=v["amount"], timestamp=v["timestamp"], nonce=v["nonce"],
        metadata=dict(v["metadata"]), signature=v["signature"], public_key=v["public_key"],
    )


def test_vectors_verify_and_bind_to_their_address():
    for v in _load():
        assert address_from_public_key_hex(v["public_key"]) == v["address"]
        tx = _tx(v)
        assert verify_signature(v["public_key"], v["signature"], tx.signing_bytes()) is True
        assert tx.is_signature_valid() is True


def test_api_accepts_a_frontend_signed_transaction():
    v = _load()[0]
    node = DeCoinNode()
    node.blockchain.require_signatures = True
    client = TestClient(DeCoinAPI(node).app)
    body = {
        "sender": v["address"], "recipient": v["recipient"], "amount": v["amount"],
        "transaction_type": "standard", "metadata": v["metadata"],
        "nonce": v["nonce"], "timestamp": v["timestamp"],
        "signature": v["signature"], "public_key": v["public_key"],
    }
    r = client.post("/transaction", json=body)
    assert r.status_code == 200
