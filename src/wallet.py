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
from typing import Optional

from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

ADDRESS_PREFIX = "DEC"


def address_from_public_key(public_key_bytes: bytes) -> str:
    """RIPEMD160(SHA256(pubkey)), hex, with the DEC prefix. The address is a
    commitment to the public key, which is why a signature can prove ownership
    of the address without the address ever revealing the key."""
    sha = hashlib.sha256(public_key_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).hexdigest()
    return ADDRESS_PREFIX + ripe


def address_from_public_key_hex(public_key_hex: str) -> str:
    return address_from_public_key(bytes.fromhex(public_key_hex))


def verify_signature(public_key_hex: str, signature_hex: str, message: bytes) -> bool:
    """True only if `signature_hex` is a valid secp256k1 signature over `message`
    for `public_key_hex`. Any malformed input is a verification failure, never an
    exception the caller has to guard."""
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        return vk.verify(bytes.fromhex(signature_hex), message)
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
        and return the signature as hex."""
        return self._signing_key.sign(message).hex()
