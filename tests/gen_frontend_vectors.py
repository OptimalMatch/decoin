"""Generate deterministic cross-language signing vectors for the browser wallet.

The frontend JS wallet must produce the SAME addresses, canonical signing bytes,
and (deterministic RFC 6979 / SHA-256) signatures the Python node verifies. This
writes fixed-key vectors to frontend/test/vectors.json, which both sides check:
frontend/test/wallet.test.mjs (JS reproduces them) and
tests/integration/test_frontend_signatures.py (the node verifies/accepts them).

Run:  python tests/gen_frontend_vectors.py
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from blockchain import Transaction, TransactionType
from wallet import Wallet

CASES = [
    ("11" * 32, "DECbob", 25, 0, {"fee": 1, "note": "hi"}, 1700000000),
    ("2a" * 32, "DECalice", 1000, 7, {"fee": 0}, 1700000123),
]


def main():
    vectors = []
    for priv, recipient, amount, nonce, metadata, ts in CASES:
        w = Wallet.from_private_key_hex(priv)
        tx = Transaction(
            tx_type=TransactionType.STANDARD, sender=w.address, recipient=recipient,
            amount=amount, timestamp=ts, nonce=nonce, metadata=metadata,
        )
        tx.sign_with(w)
        vectors.append({
            "private_key": priv, "address": w.address, "public_key": w.public_key_hex,
            "recipient": recipient, "amount": amount, "nonce": nonce,
            "metadata": metadata, "timestamp": ts,
            "signing_bytes": tx.signing_bytes().decode(), "signature": tx.signature,
        })
    out = pathlib.Path(__file__).parents[1] / "frontend" / "test" / "vectors.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vectors, indent=2) + "\n")
    print(f"wrote {len(vectors)} vectors to {out}")


if __name__ == "__main__":
    main()
