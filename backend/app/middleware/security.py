"""
Security middleware — OWASP Top 10 mitigations.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Добавляет HTTP security headers на каждый ответ."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        h = response.headers
        h["X-Frame-Options"]        = "SAMEORIGIN"
        h["X-Content-Type-Options"] = "nosniff"
        h["X-XSS-Protection"]       = "1; mode=block"
        h["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        h["Permissions-Policy"]     = "camera=(), microphone=(), geolocation=()"
        # Удаляем сигнатуру сервера безопасно (del не бросает KeyError для MutableHeaders)
        if "Server" in h:
            del h["Server"]
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Добавляет X-Request-ID для трассировки в логах."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        response   = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
