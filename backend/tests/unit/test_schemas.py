"""Unit tests for input schema validation."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest


class TestRegisterRequest:
    def _valid(self, **overrides):
        data = dict(
            first_name="Ivan",
            last_name="Ivanov",
            middle_name=None,
            email="ivan@example.com",
            password="Secret123",
            password_repeat="Secret123",
        )
        data.update(overrides)
        return data

    def test_valid_payload(self):
        req = RegisterRequest(**self._valid())
        assert req.email == "ivan@example.com"

    def test_passwords_mismatch(self):
        with pytest.raises(ValidationError, match="Passwords do not match"):
            RegisterRequest(**self._valid(password_repeat="Different1"))

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**self._valid(password="Ab1", password_repeat="Ab1"))

    def test_password_no_digit(self):
        with pytest.raises(ValidationError, match="at least one digit"):
            RegisterRequest(**self._valid(password="NoDigitsHere", password_repeat="NoDigitsHere"))

    def test_password_no_letter(self):
        with pytest.raises(ValidationError, match="at least one letter"):
            RegisterRequest(**self._valid(password="12345678", password_repeat="12345678"))

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**self._valid(email="not-an-email"))

    def test_empty_first_name(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**self._valid(first_name=""))
