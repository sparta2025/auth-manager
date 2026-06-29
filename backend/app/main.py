import app.core.logging_config  # noqa: F401 — инициализация логгера
"""Application entry point — v3."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.middleware.security import SecurityHeadersMiddleware, RequestIDMiddleware
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.resources import router as resources_router
from app.core.limiter import limiter

app = FastAPI(
    title="Authorization & Account Management API v3",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost",
        "http://frontend",
        "http://frontend:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security & tracing middleware (OWASP A05)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(resources_router)


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера."},
    )


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "3.0.0"}


# Refresh token router (добавляем после основных роутеров)
from app.api.auth_refresh import router as refresh_router
app.include_router(refresh_router)

from app.api.totp import router as totp_router
app.include_router(totp_router)
from app.api.avatar import router as avatar_router
app.include_router(avatar_router)
from app.api.bulk import router as bulk_router
app.include_router(bulk_router)
from app.api.ws import router as ws_router
app.include_router(ws_router)
from app.api.admin_policy import router as policy_router
app.include_router(policy_router)
