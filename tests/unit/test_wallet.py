"""Tests for the wallet / signature layer added in the book-repairs pass."""
import pytest

from wallet import (
    Wallet,
    address_from_public_key_hex,
    verify_signature,
)


class TestWallet:
    def test_generate_gives_distinct_keys_and_addresses(self):
        a, b = Wallet.generate(), Wallet.generate()
        assert a.private_key_hex != b.private_key_hex
        assert a.address != b.address
        assert a.address.startswith("DEC")

    def test_address_is_derived_from_the_public_key(self):
        w = Wallet.generate()
        assert w.address == address_from_public_key_hex(w.public_key_hex)

    def test_reload_from_private_key_is_the_same_wallet(self):
        w = Wallet.generate()
        again = Wallet.from_private_key_hex(w.private_key_hex)
        assert again.address == w.address
        assert again.public_key_hex == w.public_key_hex

    def test_sign_and_verify_roundtrip(self):
        w = Wallet.generate()
        msg = b"pay bob 10"
        sig = w.sign(msg)
        assert verify_signature(w.public_key_hex, sig, msg) is True

    def test_signature_is_rejected_for_a_different_message(self):
        w = Wallet.generate()
        sig = w.sign(b"pay bob 10")
        assert verify_signature(w.public_key_hex, sig, b"pay bob 1000") is False

    def test_signature_is_rejected_for_a_different_key(self):
        signer, attacker = Wallet.generate(), Wallet.generate()
        msg = b"pay bob 10"
        sig = signer.sign(msg)
        # A valid signature under signer's key does not verify under another key.
        assert verify_signature(attacker.public_key_hex, sig, msg) is False

    def test_malformed_inputs_are_failures_not_exceptions(self):
        w = Wallet.generate()
        assert verify_signature("not-hex", "also-bad", b"x") is False
        assert verify_signature(w.public_key_hex, "00", b"x") is False
