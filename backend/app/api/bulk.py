"""
Bulk operations and export endpoints.

POST /admin/users/bulk/deactivate  { user_ids: [...] }
POST /admin/users/bulk/activate    { user_ids: [...] }
POST /admin/users/bulk/assign-role { user_ids: [...], role_id: "..." }
GET  /admin/users/export/csv
GET  /admin/audit-log/export/csv
"""
import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.models import AuditLog, User, UserRole
from app.repositories.token_repo import TokenRepository
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Массовые операции"])


class BulkUserRequest(BaseModel):
    user_ids: list[str]


class BulkAssignRoleRequest(BaseModel):
    user_ids: list[str]
    role_id: str


@router.post("/users/bulk/deactivate", summary="Деактивировать пользователей массово")
def bulk_deactivate(payload: BulkUserRequest,
                    admin: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    updated = 0
    for uid in payload.user_ids:
        u = db.query(User).filter(User.id == uid).first()
        if u and u.id != admin.id:
            u.is_active = False
            u.deleted_at = now
            TokenRepository(db).delete_all_for_user(uid)
            updated += 1
    AuditService(db).log("admin.bulk_deactivate", user_id=admin.id,
                         detail=f"deactivated {updated} users")
    db.commit()
    return {"updated": updated}


@router.post("/users/bulk/activate", summary="Активировать пользователей массово")
def bulk_activate(payload: BulkUserRequest,
                  admin: User = Depends(require_admin),
                  db: Session = Depends(get_db)):
    updated = 0
    for uid in payload.user_ids:
        u = db.query(User).filter(User.id == uid).first()
        if u:
            u.is_active = True
            u.deleted_at = None
            updated += 1
    AuditService(db).log("admin.bulk_activate", user_id=admin.id,
                         detail=f"activated {updated} users")
    db.commit()
    return {"updated": updated}


@router.post("/users/bulk/assign-role", summary="Назначить роль группе пользователей")
def bulk_assign_role(payload: BulkAssignRoleRequest,
                     admin: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    updated = 0
    for uid in payload.user_ids:
        exists = db.query(UserRole).filter(
            UserRole.user_id == uid,
            UserRole.role_id == payload.role_id,
        ).first()
        if not exists:
            db.add(UserRole(user_id=uid, role_id=payload.role_id))
            updated += 1
    AuditService(db).log("admin.bulk_assign_role", user_id=admin.id,
                         detail=f"role {payload.role_id} assigned to {updated} users")
    db.commit()
    return {"updated": updated}


@router.get("/users/export/csv", summary="Экспорт пользователей в CSV")
def export_users_csv(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "email", "first_name", "last_name", "middle_name",
                     "is_active", "created_at", "last_login_at"])
    for u in users:
        writer.writerow([
            u.id, u.email, u.first_name, u.last_name, u.middle_name or "",
            u.is_active,
            u.created_at.isoformat() if u.created_at else "",
            u.last_login_at.isoformat() if u.last_login_at else "",
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@router.get("/audit-log/export/csv", summary="Экспорт журнала аудита в CSV")
def export_audit_csv(
    limit: int = Query(1000, ge=1, le=10000),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entries = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "user_id", "action", "entity_type",
                     "entity_id", "detail", "ip_address", "created_at"])
    for e in entries:
        writer.writerow([
            e.id, e.user_id or "", e.action, e.entity_type or "",
            e.entity_id or "", e.detail or "", e.ip_address or "",
            e.created_at.isoformat(),
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )
