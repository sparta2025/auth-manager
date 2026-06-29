from app.core.logging_config import get_logger
log = get_logger(__name__)

"""Auth service — v3 with password reset, change password, sessions, audit."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.password_policy import validate_password
from app.core.security import generate_token, hash_password, verify_password
from app.models.models import AccessToken, PasswordReset, User
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest,
    RegisterRequest, ResetPasswordRequest, UpdateProfileRequest,
)
from app.services.audit_service import AuditService
from app.services.email_service import (
    send_admin_notification, send_password_changed, send_password_reset,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._users  = UserRepository(db)
        self._tokens = TokenRepository(db)
        self._audit  = AuditService(db)

    # ── Registration ──────────────────────────────────────────────────────────
    def register(self, payload: RegisterRequest, ip: str | None = None) -> User:
        if self._users.get_by_email(payload.email):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email уже зарегистрирован.")
        validate_password(payload.password)
        user = self._users.create(
            first_name=payload.first_name,
            last_name=payload.last_name,
            middle_name=payload.middle_name,
            email=payload.email,
            recovery_email=str(payload.recovery_email) if payload.recovery_email else None,
            password_hash=hash_password(payload.password),
        )
        # Assign default "user" role
        from app.models.models import Role, UserRole
        default_role = self._db.query(Role).filter(Role.name == "user").first()
        if default_role:
            self._db.add(UserRole(user_id=user.id, role_id=default_role.id))

        self._audit.log("user.registered", user_id=user.id, entity_type="user", entity_id=user.id, ip_address=ip)
        self._audit.notify_admin(
            event="registered",
            title=f"Новый пользователь: {user.email}",
            body=f"{user.first_name} {user.last_name} зарегистрировался в системе.",
            user_id=user.id,
            link=f"/admin/users/{user.id}",
        )
        self._db.commit()
        log.info('user.registered', extra={'user_id': user.id, 'email': user.email})
        # Send email notification to admin (outside transaction)
        send_admin_notification("Регистрация", user.email, user.id,
                                f"{user.first_name} {user.last_name} зарегистрировался.")
        return user

    # ── Login ─────────────────────────────────────────────────────────────────
    def login(self, payload: LoginRequest, request: Request | None = None) -> AccessToken:
        user = self._users.get_by_email(payload.email)
        _DUMMY = "$2b$12$QoOk.vbM2fkO6bp7S7Lh8u8KDkUMBeF2LK2XBRQz7JOkPx0LKtYXK"
        ok = verify_password(payload.password, user.password_hash if user else _DUMMY)
        if not user or not ok:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль.")
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован.")

        ip = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None

        expires_at = _now() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
        token_record = self._tokens.create(
            user_id=user.id, token=generate_token(),
            expires_at=expires_at, ip_address=ip, user_agent=ua,
        )
        user.last_login_at = _now()
        self._audit.log("user.login", user_id=user.id, ip_address=ip)
        self._db.commit()
        log.info('user.login', extra={'user_id': user.id, 'ip': ip})
        return token_record

    # ── Logout ────────────────────────────────────────────────────────────────
    def logout(self, token_record: AccessToken) -> None:
        self._audit.log("user.logout", user_id=token_record.user_id)
        self._tokens.delete(token_record)
        self._db.commit()

    # ── Profile update ────────────────────────────────────────────────────────
    def update_profile(self, user: User, payload: UpdateProfileRequest,
                       ip: str | None = None) -> User:
        changed = []
        if payload.first_name and payload.first_name != user.first_name:
            changed.append(f"имя: {user.first_name} → {payload.first_name}")
        if payload.last_name and payload.last_name != user.last_name:
            changed.append(f"фамилия: {user.last_name} → {payload.last_name}")
        if payload.recovery_email is not None:
            re_str = str(payload.recovery_email)
            if re_str != user.recovery_email:
                changed.append(f"recovery_email изменён")

        updated = self._users.update(
            user,
            first_name=payload.first_name,
            last_name=payload.last_name,
            middle_name=payload.middle_name,
            recovery_email=str(payload.recovery_email) if payload.recovery_email else None,
        )
        if changed:
            detail = "; ".join(changed)
            self._audit.log("user.profile_updated", user_id=user.id, detail=detail, ip_address=ip)
            self._audit.notify_admin(
                event="profile_updated",
                title=f"Изменён профиль: {user.email}",
                body=detail,
                user_id=user.id,
                link=f"/admin/users/{user.id}",
            )
            self._db.commit()
            send_admin_notification("Изменение профиля", user.email, user.id, detail)
        else:
            self._db.commit()
        return updated

    # ── Change password (user knows current) ─────────────────────────────────
    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Неверный текущий пароль.")
        validate_password(payload.new_password)
        user.password_hash = hash_password(payload.new_password)
        self._audit.log("user.password_changed", user_id=user.id)
        self._db.commit()
        send_password_changed(user.email)

    # ── Forgot password ───────────────────────────────────────────────────────
    def forgot_password(self, payload: ForgotPasswordRequest) -> None:
        user = self._users.get_by_email(payload.email)
        if not user:
            return  # Don't reveal whether email exists

        token = generate_token()
        expires_at = _now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
        reset = PasswordReset(user_id=user.id, token=token, expires_at=expires_at)
        self._db.add(reset)
        self._audit.log("user.password_reset_requested", user_id=user.id)
        self._db.commit()

        # Send to recovery_email if set, else to primary email
        target = user.recovery_email or user.email
        is_admin = any(r.role.name == "administrator" for r in user.user_roles)
        send_password_reset(target, token, is_admin=is_admin)

    # ── Reset password (via token) ────────────────────────────────────────────
    def reset_password(self, payload: ResetPasswordRequest) -> None:
        reset = (
            self._db.query(PasswordReset)
            .filter(PasswordReset.token == payload.token, PasswordReset.used == False)
            .first()
        )
        if not reset or reset.expires_at < _now():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Токен недействителен или истёк.")

        user = self._users.get_by_id(reset.user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")

        validate_password(payload.new_password)
        user.password_hash = hash_password(payload.new_password)
        reset.used = True
        # Invalidate all sessions
        self._tokens.delete_all_for_user(user.id)
        self._audit.log("user.password_reset_completed", user_id=user.id)
        self._db.commit()
        send_password_changed(user.email)

    # ── Soft-delete (self) ────────────────────────────────────────────────────
    def deactivate_account(self, user: User, token_record: AccessToken,
                           ip: str | None = None) -> None:
        user.is_active = False
        user.deleted_at = _now()
        self._tokens.delete_all_for_user(user.id)
        self._audit.log("user.self_deactivated", user_id=user.id, ip_address=ip)
        self._audit.notify_admin(
            event="deactivated",
            title=f"Пользователь деактивировал аккаунт: {user.email}",
            body=f"{user.first_name} {user.last_name} самостоятельно деактивировал аккаунт.",
            user_id=user.id,
            link=f"/admin/users/{user.id}",
        )
        self._db.commit()
        send_admin_notification("Самодеактивация", user.email, user.id,
                                f"{user.first_name} {user.last_name} деактивировал аккаунт.")
