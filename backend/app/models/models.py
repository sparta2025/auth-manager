"""
ORM models — v3 with audit_log, notifications, password_resets,
recovery_email and extended User fields.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id:             Mapped[str]           = mapped_column(String(36), primary_key=True, default=_uuid)
    first_name:     Mapped[str]           = mapped_column(String(100), nullable=False)
    last_name:      Mapped[str]           = mapped_column(String(100), nullable=False)
    middle_name:    Mapped[str | None]    = mapped_column(String(100), nullable=True)
    email:          Mapped[str]           = mapped_column(String(255), unique=True, nullable=False, index=True)
    recovery_email: Mapped[str | None]    = mapped_column(String(255), nullable=True)
    password_hash:  Mapped[str]           = mapped_column(String(255), nullable=False)
    is_active:      Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    last_login_at:  Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at:     Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_url:     Mapped[str|None]      = mapped_column(String(512), nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tokens:          Mapped[list["AccessToken"]]    = relationship(back_populates="user", cascade="all, delete-orphan")
    user_roles:      Mapped[list["UserRole"]]       = relationship(back_populates="user", cascade="all, delete-orphan")
    password_resets: Mapped[list["PasswordReset"]]  = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs:      Mapped[list["AuditLog"]]       = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications:   Mapped[list["Notification"]]   = relationship(back_populates="user", cascade="all, delete-orphan")


# ── Access tokens ─────────────────────────────────────────────────────────────
class AccessToken(Base):
    __tablename__ = "access_tokens"

    id:         Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id:    Mapped[str]      = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token:      Mapped[str]      = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Optional: device/browser info for "My sessions" page
    user_agent: Mapped[str|None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str|None] = mapped_column(String(45), nullable=True)

    user: Mapped["User"] = relationship(back_populates="tokens")


# ── Roles ─────────────────────────────────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"

    id:          Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    name:        Mapped[str]      = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str|None] = mapped_column(Text, nullable=True)
    # Roles with is_system=True cannot be self-assigned at registration
    is_system:   Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)

    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    user_roles:       Mapped[list["UserRole"]]       = relationship(back_populates="role", cascade="all, delete-orphan")


# ── Permissions ───────────────────────────────────────────────────────────────
class Permission(Base):
    __tablename__ = "permissions"

    id:          Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    code:        Mapped[str]      = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource:    Mapped[str]      = mapped_column(String(100), nullable=False)
    action:      Mapped[str]      = mapped_column(String(50), nullable=False)
    description: Mapped[str|None] = mapped_column(Text, nullable=True)

    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="permission", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id:      Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id:            Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    role_id:       Mapped[str] = mapped_column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[str] = mapped_column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    role:       Mapped["Role"]       = relationship(back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_permissions")


# ── Password resets ───────────────────────────────────────────────────────────
class PasswordReset(Base):
    __tablename__ = "password_resets"

    id:         Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id:    Mapped[str]      = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token:      Mapped[str]      = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used:       Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="password_resets")


# ── Audit log ─────────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_log"

    id:          Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id:     Mapped[str|None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action:      Mapped[str]      = mapped_column(String(100), nullable=False)   # e.g. "user.login"
    entity_type: Mapped[str|None] = mapped_column(String(100), nullable=True)   # "user", "role", etc.
    entity_id:   Mapped[str|None] = mapped_column(String(36), nullable=True)
    detail:      Mapped[str|None] = mapped_column(Text, nullable=True)           # JSON or free text
    ip_address:  Mapped[str|None] = mapped_column(String(45), nullable=True)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User|None"] = relationship(back_populates="audit_logs")


# ── Notifications (for admin) ─────────────────────────────────────────────────
class Notification(Base):
    """
    Events that should be surfaced to the administrator.
    user_id = the user WHO triggered the event.
    """
    __tablename__ = "notifications"

    id:          Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id:     Mapped[str|None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event:       Mapped[str]      = mapped_column(String(100), nullable=False)   # "registered", "profile_updated", "deactivated"
    title:       Mapped[str]      = mapped_column(String(255), nullable=False)
    body:        Mapped[str|None] = mapped_column(Text, nullable=True)
    link:        Mapped[str|None] = mapped_column(String(512), nullable=True)    # /admin/users/{id}
    is_read:     Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User|None"] = relationship(back_populates="notifications")


# ── TOTP / 2FA ────────────────────────────────────────────────────────────────
class UserTOTP(Base):
    """
    Per-user TOTP secret for two-factor authentication.
    One row per user; is_enabled флаг активирует 2FA.
    """
    __tablename__ = "user_totp"

    id:         Mapped[str]      = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id:    Mapped[str]      = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"),
                                                  nullable=False, unique=True, index=True)
    secret:     Mapped[str]      = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now(), nullable=False)
