"""
Security utilities: password hashing and opaque session-token generation.

Token design decision
---------------------
We chose **opaque session tokens** (random hex strings stored in the DB)
over JWT for the following reasons:

1. **Instant revocation** — a JWT is valid until expiry; we cannot revoke it
   server-side without a blocklist.  An opaque token is simply deleted from
   `access_tokens` on logout or account deactivation, achieving true
   server-side revocation.

2. **Simplicity** — no signing keys to rotate, no clock-skew issues, no
   algorithm-confusion vulnerabilities (e.g., alg:none attacks).

3. **Privacy** — the token payload is opaque; no user data is encoded inside
   it, so nothing leaks if a token is intercepted in transit.

Password hashing
----------------
We use bcrypt directly (without passlib) to avoid compatibility issues
between passlib 1.7.x and bcrypt >= 4.x.

bcrypt >= 4.0 enforces a strict 72-byte password limit and removed the
internal __about__ attribute that passlib relied on for version detection.
Using bcrypt directly gives us a stable, forward-compatible API:
  - bcrypt.hashpw(password_bytes, salt)  → hash bytes
  - bcrypt.checkpw(password_bytes, hash_bytes) → bool
  - bcrypt.gensalt(rounds=12) → random salt bytes

Cost factor 12 (≈250ms per hash) makes brute-force attacks expensive
without being noticeable to human users during login.
"""
import hashlib
import hmac
import os

import bcrypt

from app.core.config import settings

# Bcrypt cost factor: 12 rounds is the industry-standard default.
# Increase to 13-14 on hardware that can afford ~500ms+ per hash.
_BCRYPT_ROUNDS: int = 12


def hash_password(plain: str) -> str:
    """
    Hash *plain* with bcrypt and return the result as a UTF-8 string
    suitable for VARCHAR storage.

    bcrypt.hashpw() requires bytes input and returns bytes; we decode
    to str for consistent storage / Pydantic serialization.
    """
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if *plain* matches the stored bcrypt *hashed* value.

    bcrypt.checkpw() is timing-safe: it always takes the same amount
    of time regardless of where the comparison diverges.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def generate_token() -> str:
    """
    Generate a cryptographically random opaque session token.

    Construction:
        raw   = os.urandom(32)           — 256 bits of OS entropy
        token = HMAC-SHA256(SECRET_SALT, raw)  — binds token to this server

    The HMAC step ensures that even if the token database is leaked,
    tokens cannot be replayed against a different server instance
    (different SECRET_SALT).

    Returns a 64-character lowercase hex string.
    """
    raw = os.urandom(32)
    token = hmac.new(
        settings.SECRET_SALT.encode("utf-8"),
        raw,
        hashlib.sha256,
    ).hexdigest()
    return token
