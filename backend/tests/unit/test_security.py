"""Unit tests for password hashing and token generation."""
import pytest

from app.core.security import generate_token, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MyPassword1")
        assert hashed != "MyPassword1"

    def test_verify_correct_password(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("MyPassword1", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("WrongPassword1", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Bcrypt uses a random salt so two hashes of the same password differ."""
        h1 = hash_password("MyPassword1")
        h2 = hash_password("MyPassword1")
        assert h1 != h2


class TestTokenGeneration:
    def test_token_is_64_chars(self):
        token = generate_token()
        assert len(token) == 64

    def test_token_is_hex(self):
        token = generate_token()
        int(token, 16)  # raises ValueError if not hex

    def test_tokens_are_unique(self):
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100
