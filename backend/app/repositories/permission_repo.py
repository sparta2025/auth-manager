"""Permission repository — v3."""
from sqlalchemy.orm import Session
from app.models.models import Permission, RolePermission, UserRole


class PermissionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_all(self) -> list[Permission]:
        return self._db.query(Permission).order_by(Permission.code).all()

    def get_by_id(self, permission_id: str) -> Permission | None:
        return self._db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_code(self, code: str) -> Permission | None:
        return self._db.query(Permission).filter(Permission.code == code).first()

    def create(self, *, code: str, resource: str, action: str,
               description: str | None = None) -> Permission:
        perm = Permission(code=code, resource=resource, action=action, description=description)
        self._db.add(perm)
        self._db.flush()
        return perm

    def update(self, perm: Permission, **kwargs) -> Permission:
        for key, value in kwargs.items():
            if value is not None:
                setattr(perm, key, value)
        self._db.flush()
        return perm

    def delete(self, perm: Permission) -> None:
        self._db.delete(perm)
        self._db.flush()

    def assign_to_role(self, role_id: str, permission_id: str) -> None:
        exists = (
            self._db.query(RolePermission)
            .filter(RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id)
            .first()
        )
        if not exists:
            self._db.add(RolePermission(role_id=role_id, permission_id=permission_id))
            self._db.flush()

    def get_codes_for_user(self, user_id: str) -> set[str]:
        rows = (
            self._db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        return {row.code for row in rows}
