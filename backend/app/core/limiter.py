"""
Rate limiting via slowapi.

Ключ rate limiter — IP адрес. В тестах TestClient использует "testclient" как IP,
поэтому при множестве тестов лимит исчерпывается.
Решение: в тестах подменяем лимиты через env-переменную TESTING=1.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

_TESTING = os.getenv("TESTING", "0") == "1"

def _unlimited_key(request):
    """В тестах каждый запрос получает уникальный ключ — лимит никогда не достигается."""
    import uuid
    return str(uuid.uuid4())

limiter = Limiter(
    key_func=_unlimited_key if _TESTING else get_remote_address,
    default_limits=[] if _TESTING else ["200/minute"],
)
