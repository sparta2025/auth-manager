from sqlalchemy.orm import Session
from app.models.models import User
from app.repositories.permission_repo import PermissionRepository


class PermissionService:
    def __init__(self, db: Session) -> None:
        self._perms = PermissionRepository(db)

    def user_has_permission(self, user: User, code: str) -> bool:
        return code in self._perms.get_codes_for_user(user.id)

    def get_user_permission_codes(self, user: User) -> set[str]:
        return self._perms.get_codes_for_user(user.id)
