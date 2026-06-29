"""Admin API — v3: users, roles, permissions, notifications, audit log."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.password_policy import validate_password
from app.core.security import hash_password
from app.models.models import AuditLog, Notification, User
from app.repositories.permission_repo import PermissionRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.admin import (
    AdminCreateUserRequest, AdminSetPasswordRequest, AdminUpdateUserRequest,
    AssignRolesRequest, AuditLogResponse, NotificationResponse,
    PermissionCreate, PermissionResponse, PermissionUpdate,
    RoleCreate, RoleResponse, RoleUpdate, UserRoleResponse,
)
from app.schemas.auth import UserResponse
from app.services.audit_service import AuditService
from app.services.email_service import send_admin_notification

router = APIRouter(prefix="/admin", tags=["Администрирование"])


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse], summary="Список пользователей")
def list_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (User.email.ilike(like)) |
            (User.first_name.ilike(like)) |
            (User.last_name.ilike(like))
        )
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    return q.order_by(User.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/users", response_model=UserResponse, status_code=201,
             summary="Создать пользователя")
def create_user(payload: AdminCreateUserRequest,
                admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    from app.core.security import hash_password
    from app.models.models import Role, UserRole

    existing = UserRepository(db).get_by_email(payload.email)
    if existing:
        raise HTTPException(409, detail="Пользователь с таким email уже существует.")
    validate_password(payload.password)
    user = UserRepository(db).create(
        first_name=payload.first_name, last_name=payload.last_name,
        middle_name=payload.middle_name, email=payload.email,
        recovery_email=None, password_hash=hash_password(payload.password),
    )
    for role_id in payload.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(422, detail=f"Роль '{role_id}' не найдена.")
        db.add(UserRole(user_id=user.id, role_id=role_id))
    AuditService(db).log("admin.user_created", user_id=admin.id,
                         entity_type="user", entity_id=user.id,
                         detail=f"Admin {admin.email} created user {user.email}")
    db.commit()
    return user


@router.get("/users/{user_id}", response_model=UserResponse, summary="Профиль пользователя")
def get_user(user_id: str, _: User = Depends(require_admin),
             db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    return user


@router.put("/users/{user_id}", response_model=UserResponse,
            summary="Редактировать профиль пользователя")
def update_user(user_id: str, payload: AdminUpdateUserRequest,
                admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    repo.update(user,
                first_name=payload.first_name,
                last_name=payload.last_name,
                middle_name=payload.middle_name,
                recovery_email=str(payload.recovery_email) if payload.recovery_email else None)
    AuditService(db).log("admin.user_updated", user_id=admin.id,
                         entity_type="user", entity_id=user_id,
                         detail=f"Admin {admin.email} updated user {user.email}")
    db.commit()
    return user


@router.patch("/users/{user_id}/activate", response_model=UserResponse,
              summary="Активировать пользователя")
def activate_user(user_id: str, admin: User = Depends(require_admin),
                  db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    user.is_active = True
    user.deleted_at = None
    AuditService(db).log("admin.user_activated", user_id=admin.id,
                         entity_type="user", entity_id=user_id)
    db.commit()
    return user


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse,
              summary="Деактивировать пользователя")
def deactivate_user(user_id: str, admin: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    TokenRepository(db).delete_all_for_user(user_id)
    AuditService(db).log("admin.user_deactivated", user_id=admin.id,
                         entity_type="user", entity_id=user_id)
    db.commit()
    return user


@router.delete("/users/{user_id}", status_code=204, summary="Удалить пользователя (hard delete)")
def delete_user(user_id: str, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    if user.id == admin.id:
        raise HTTPException(400, detail="Нельзя удалить собственный аккаунт.")
    AuditService(db).log("admin.user_deleted", user_id=admin.id,
                         entity_type="user", entity_id=user_id,
                         detail=f"Hard-deleted user {user.email}")
    db.delete(user)
    db.commit()


@router.post("/users/{user_id}/set-password", status_code=204,
             summary="Установить пароль пользователю")
def admin_set_password(user_id: str, payload: AdminSetPasswordRequest,
                       admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    validate_password(payload.new_password)
    user.password_hash = hash_password(payload.new_password)
    TokenRepository(db).delete_all_for_user(user_id)
    AuditService(db).log("admin.password_set", user_id=admin.id,
                         entity_type="user", entity_id=user_id)
    db.commit()


@router.post("/users/{user_id}/logout-all", status_code=204,
             summary="Завершить все сессии пользователя")
def logout_all_sessions(user_id: str, admin: User = Depends(require_admin),
                        db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    TokenRepository(db).delete_all_for_user(user_id)
    AuditService(db).log("admin.sessions_revoked", user_id=admin.id,
                         entity_type="user", entity_id=user_id)
    db.commit()


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles", response_model=list[RoleResponse], summary="Список ролей")
def list_roles(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return RoleRepository(db).get_all()


@router.post("/roles", response_model=RoleResponse, status_code=201,
             summary="Создать роль")
def create_role(payload: RoleCreate, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    if repo.get_by_name(payload.name):
        raise HTTPException(409, detail="Название роли уже существует.")
    role = repo.create(name=payload.name, description=payload.description,
                       is_system=payload.is_system)
    AuditService(db).log("admin.role_created", user_id=admin.id,
                         entity_type="role", entity_id=role.id, detail=role.name)
    db.commit()
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="Обновить роль")
def update_role(role_id: str, payload: RoleUpdate, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    role = repo.get_by_id(role_id)
    if not role:
        raise HTTPException(404, detail="Роль не найдена.")
    if payload.name and payload.name != role.name and repo.get_by_name(payload.name):
        raise HTTPException(409, detail="Название роли уже существует.")
    role = repo.update(role, name=payload.name, description=payload.description)
    AuditService(db).log("admin.role_updated", user_id=admin.id,
                         entity_type="role", entity_id=role_id)
    db.commit()
    return role


@router.delete("/roles/{role_id}", status_code=204, summary="Удалить роль")
def delete_role(role_id: str, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    role = repo.get_by_id(role_id)
    if not role:
        raise HTTPException(404, detail="Роль не найдена.")
    if role.is_system:
        raise HTTPException(400, detail="Нельзя удалить системную роль.")
    AuditService(db).log("admin.role_deleted", user_id=admin.id,
                         entity_type="role", entity_id=role_id, detail=role.name)
    repo.delete(role)
    db.commit()


# ── Permissions ───────────────────────────────────────────────────────────────

@router.get("/permissions", response_model=list[PermissionResponse],
            summary="Список разрешений")
def list_permissions(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return PermissionRepository(db).get_all()


@router.post("/permissions", response_model=PermissionResponse, status_code=201,
             summary="Создать разрешение")
def create_permission(payload: PermissionCreate, admin: User = Depends(require_admin),
                      db: Session = Depends(get_db)):
    repo = PermissionRepository(db)
    if repo.get_by_code(payload.code):
        raise HTTPException(409, detail="Код разрешения уже существует.")
    perm = repo.create(code=payload.code, resource=payload.resource,
                       action=payload.action, description=payload.description)
    AuditService(db).log("admin.permission_created", user_id=admin.id,
                         entity_type="permission", entity_id=perm.id, detail=perm.code)
    db.commit()
    return perm


@router.put("/permissions/{permission_id}", response_model=PermissionResponse,
            summary="Обновить разрешение")
def update_permission(permission_id: str, payload: PermissionUpdate,
                      admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    repo = PermissionRepository(db)
    perm = repo.get_by_id(permission_id)
    if not perm:
        raise HTTPException(404, detail="Разрешение не найдено.")
    perm = repo.update(perm, description=payload.description)
    AuditService(db).log("admin.permission_updated", user_id=admin.id,
                         entity_type="permission", entity_id=permission_id)
    db.commit()
    return perm


@router.delete("/permissions/{permission_id}", status_code=204,
               summary="Удалить разрешение")
def delete_permission(permission_id: str, admin: User = Depends(require_admin),
                      db: Session = Depends(get_db)):
    repo = PermissionRepository(db)
    perm = repo.get_by_id(permission_id)
    if not perm:
        raise HTTPException(404, detail="Разрешение не найдено.")
    AuditService(db).log("admin.permission_deleted", user_id=admin.id,
                         entity_type="permission", entity_id=permission_id, detail=perm.code)
    repo.delete(perm)
    db.commit()


# ── Role assignments ──────────────────────────────────────────────────────────

@router.get("/users/{user_id}/roles", response_model=UserRoleResponse,
            summary="Роли пользователя")
def get_user_roles(user_id: str, _: User = Depends(require_admin),
                   db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    roles = RoleRepository(db).get_roles_for_user(user_id)
    return UserRoleResponse(user_id=user_id, roles=roles)


@router.post("/users/{user_id}/roles", response_model=UserRoleResponse,
             summary="Назначить роли пользователю")
def assign_roles(user_id: str, payload: AssignRolesRequest,
                 admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="Пользователь не найден.")
    for role_id in payload.role_ids:
        if not role_repo.get_by_id(role_id):
            raise HTTPException(422, detail=f"Роль '{role_id}' не найдена.")
    role_repo.assign_roles(user_id=user_id, role_ids=payload.role_ids)
    AuditService(db).log("admin.roles_assigned", user_id=admin.id,
                         entity_type="user", entity_id=user_id,
                         detail=f"role_ids={payload.role_ids}")
    db.commit()
    roles = role_repo.get_roles_for_user(user_id)
    return UserRoleResponse(user_id=user_id, roles=roles)


# ── Role ↔ Permission assignments ────────────────────────────────────────────

@router.get("/roles/{role_id}/permissions", summary="Разрешения роли")
def get_role_permissions(role_id: str, _: User = Depends(require_admin),
                         db: Session = Depends(get_db)):
    from app.models.models import RolePermission, Permission as Perm
    rows = (db.query(Perm)
            .join(RolePermission, RolePermission.permission_id == Perm.id)
            .filter(RolePermission.role_id == role_id).all())
    return [{"id": p.id, "code": p.code, "resource": p.resource,
             "action": p.action, "description": p.description} for p in rows]


@router.post("/roles/{role_id}/permissions", status_code=204,
             summary="Назначить разрешения роли")
def assign_permissions_to_role(role_id: str,
                                payload: dict,
                                admin: User = Depends(require_admin),
                                db: Session = Depends(get_db)):
    from app.models.models import RolePermission
    perm_ids: list[str] = payload.get("permission_ids", [])
    # Replace all permissions for this role
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    for pid in perm_ids:
        if not PermissionRepository(db).get_by_id(pid):
            raise HTTPException(422, detail=f"Разрешение '{pid}' не найдено.")
        db.add(RolePermission(role_id=role_id, permission_id=pid))
    AuditService(db).log("admin.role_permissions_updated", user_id=admin.id,
                         entity_type="role", entity_id=role_id)
    db.commit()


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=list[NotificationResponse],
            summary="Уведомления администратора")
def list_notifications(unread_only: bool = Query(False),
                       _: User = Depends(require_admin),
                       db: Session = Depends(get_db)):
    q = db.query(Notification)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    items = q.order_by(Notification.created_at.desc()).limit(100).all()
    return [NotificationResponse(
        id=n.id, event=n.event, title=n.title, body=n.body,
        link=n.link, is_read=n.is_read, user_id=n.user_id,
        created_at=n.created_at.isoformat(),
    ) for n in items]


@router.get("/notifications/unread-count", summary="Количество непрочитанных")
def unread_count(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    count = db.query(Notification).filter(Notification.is_read == False).count()
    return {"count": count}


@router.patch("/notifications/{notification_id}/read", status_code=204,
              summary="Отметить уведомление прочитанным")
def mark_read(notification_id: str, _: User = Depends(require_admin),
              db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        raise HTTPException(404, detail="Уведомление не найдено.")
    n.is_read = True
    db.commit()


@router.patch("/notifications/read-all", status_code=204,
              summary="Отметить все прочитанными")
def mark_all_read(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log", response_model=list[AuditLogResponse],
            summary="Журнал аудита")
def audit_log(
    user_id:    str | None = Query(None),
    action:     str | None = Query(None),
    date_from:  str | None = Query(None),
    date_to:    str | None = Query(None),
    limit:      int         = Query(100, ge=1, le=500),
    offset:     int         = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)
    items = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    # Enrich with user email
    user_emails: dict[str, str] = {}
    result = []
    for item in items:
        if item.user_id and item.user_id not in user_emails:
            u = UserRepository(db).get_by_id(item.user_id)
            user_emails[item.user_id] = u.email if u else "?"
        result.append(AuditLogResponse(
            id=item.id, user_id=item.user_id, action=item.action,
            entity_type=item.entity_type, entity_id=item.entity_id,
            detail=item.detail, ip_address=item.ip_address,
            created_at=item.created_at.isoformat(),
            user_email=user_emails.get(item.user_id or "", None),
        ))
    return result
