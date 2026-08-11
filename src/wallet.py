"""
Keys, addresses, and signatures for DeCoin.

DeCoin shipped without any of this: transactions carried a `signature` field that
was never set and never checked, and "addresses" were arbitrary strings, so any
address was spendable by anyone. This module is the missing cryptography — real
ECDSA over secp256k1, the same curve Bitcoin uses.

An address is derived from a public key the Bitcoin way — RIPEMD160(SHA256(pub)) —
so it commits to the key that controls it. Signing covers a transaction's
canonical content, and verification checks two things together: that the
signature is valid for the stated public key, and that the public key hashes to
the sender address. Only the holder of the private key can produce that pair.
"""
import hashlib
import json
from typing import List, Optional

from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

# Verification runs on every node for every signature in every block, so it is
# the hot path at scale. Pure-Python ecdsa verifies ~1,000/s; libsecp256k1 (the
# C library Bitcoin and Ethereum use) does tens of thousands per core. Prefer it
# when installed and fall back to pure Python so the project still clones and
# runs with no compiled dependency. SIGNING stays on `ecdsa` either way, so the
# signatures a wallet produces are byte-identical across backends and across
# languages (the browser wallet must reproduce them exactly).
try:
    from coincurve import PublicKey as _CCPublicKey
    from coincurve.ecdsa import (
        deserialize_compact as _cc_deserialize_compact,
        cdata_to_der as _cc_cdata_to_der,
        signature_normalize as _cc_signature_normalize,
    )
    _HAVE_COINCURVE = True
except ImportError:  # pragma: no cover - exercised only where coincurve is absent
    _HAVE_COINCURVE = False

ADDRESS_PREFIX = "DEC"
MULTISIG_PREFIX = "DECMS"


def _sha256d(message: bytes) -> bytes:
    return hashlib.sha256(message).digest()


def address_from_public_key(public_key_bytes: bytes) -> str:
    """RIPEMD160(SHA256(pubkey)), hex, with the DEC prefix. The address is a
    commitment to the public key, which is why a signature can prove ownership
    of the address without the address ever revealing the key."""
    sha = hashlib.sha256(public_key_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).hexdigest()
    return ADDRESS_PREFIX + ripe


def address_from_public_key_hex(public_key_hex: str) -> str:
    return address_from_public_key(bytes.fromhex(public_key_hex))


def multisig_address(signer_addresses: List[str], required: int) -> str:
    """An m-of-n address commits to WHO can sign and HOW MANY are needed, so the
    address cannot be spent by a different set of signers or a lower threshold.
    Order-independent (signers are sorted) so every party derives the same one."""
    payload = json.dumps(
        {"signers": sorted(signer_addresses), "required": int(required)},
        sort_keys=True,
    ).encode()
    ripe = hashlib.new("ripemd160", hashlib.sha256(payload).digest()).hexdigest()
    return MULTISIG_PREFIX + ripe


def verify_signature(public_key_hex: str, signature_hex: str, message: bytes) -> bool:
    """True only if `signature_hex` is a valid secp256k1 signature over `message`
    for `public_key_hex`. Any malformed input is a verification failure, never an
    exception the caller has to guard.

    Both backends verify the same signatures: a 64-byte compact (r||s) signature
    over SHA-256 of the message, for a 64-byte raw public key. The signature may
    carry a high S value (the signing rule does not normalise it); a high-S
    signature is mathematically valid, so both paths accept it — libsecp256k1
    after an explicit low-S normalisation, which changes acceptance, not validity."""
    try:
        pub = bytes.fromhex(public_key_hex)
        sig = bytes.fromhex(signature_hex)
    except (ValueError, TypeError):
        return False
    if len(pub) != 64 or len(sig) != 64:
        return False

    if _HAVE_COINCURVE:
        try:
            cdata = _cc_signature_normalize(_cc_deserialize_compact(sig))[1]
            der = _cc_cdata_to_der(cdata)
            # 0x04 == uncompressed-point prefix; ecdsa's to_string() omits it.
            return _CCPublicKey(b"\x04" + pub).verify(der, message, hasher=_sha256d)
        except Exception:
            return False

    try:
        vk = VerifyingKey.from_string(pub, curve=SECP256k1)
        return vk.verify(sig, message, hashfunc=hashlib.sha256)
    except (BadSignatureError, ValueError, TypeError):
        return False


class Wallet:
    """A keypair and the address it controls. Generate a fresh one, or reload one
    from a stored private key. The private key never leaves the wallet except as
    an explicit export the caller asks for."""

    def __init__(self, signing_key: SigningKey):
        self._signing_key = signing_key
        self._verifying_key = signing_key.get_verifying_key()

    @classmethod
    def generate(cls) -> "Wallet":
        return cls(SigningKey.generate(curve=SECP256k1))

    @classmethod
    def from_private_key_hex(cls, private_key_hex: str) -> "Wallet":
        return cls(SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1))

    @property
    def private_key_hex(self) -> str:
        return self._signing_key.to_string().hex()

    @property
    def public_key_hex(self) -> str:
        return self._verifying_key.to_string().hex()

    @property
    def address(self) -> str:
        return address_from_public_key(self._verifying_key.to_string())

    def sign(self, message: bytes) -> str:
        """Sign the canonical bytes of a transaction (see Transaction.signing_bytes)
        and return the signature as hex. Deterministic (RFC 6979) over SHA-256 —
        strong (the library's bare sign() defaults to SHA-1) and reproducible, so
        an independent implementation (e.g. the browser wallet) that follows the
        same rule produces a byte-identical signature."""
        return self._signing_key.sign_deterministic(message, hashfunc=hashlib.sha256).hex()
