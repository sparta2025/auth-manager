"""
Password policy validation.
Rules come from Settings so admin can change them without redeploy
(stored in DB Settings table or env vars for now).
"""
import re
from fastapi import HTTPException, status
from app.core.config import settings


def validate_password(password: str) -> None:
    """Raise HTTP 400 if password doesn't meet policy."""
    errors = []

    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Минимум {settings.PASSWORD_MIN_LENGTH} символов.")

    if not re.search(r"[A-Za-z]", password):
        errors.append("Нужна хотя бы одна буква.")

    if not re.search(r"\d", password):
        errors.append("Нужна хотя бы одна цифра.")

    if settings.PASSWORD_REQUIRE_UPPER and not re.search(r"[A-Z]", password):
        errors.append("Нужна хотя бы одна заглавная буква.")

    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Нужен хотя бы один спецсимвол (!@#$%^&* и др.).")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль не соответствует политике: " + " ".join(errors),
        )


def get_policy() -> dict:
    """Return current policy for frontend display."""
    return {
        "min_length":       settings.PASSWORD_MIN_LENGTH,
        "require_digit":    True,
        "require_letter":   True,
        "require_upper":    settings.PASSWORD_REQUIRE_UPPER,
        "require_special":  settings.PASSWORD_REQUIRE_SPECIAL,
        "expire_days":      settings.PASSWORD_EXPIRE_DAYS,
    }
