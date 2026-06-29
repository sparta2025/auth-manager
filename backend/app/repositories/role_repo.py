"""Role repository — v3."""
from sqlalchemy.orm import Session
from app.models.models import Role, UserRole


class RoleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_all(self) -> list[Role]:
        return self._db.query(Role).order_by(Role.name).all()

    def get_public(self) -> list[Role]:
        """Roles available for self-registration (non-system)."""
        return self._db.query(Role).filter(Role.is_system == False).order_by(Role.name).all()

    def get_by_id(self, role_id: str) -> Role | None:
        return self._db.query(Role).filter(Role.id == role_id).first()

    def get_by_name(self, name: str) -> Role | None:
        return self._db.query(Role).filter(Role.name == name).first()

    def create(self, *, name: str, description: str | None = None,
               is_system: bool = False) -> Role:
        role = Role(name=name, description=description, is_system=is_system)
        self._db.add(role)
        self._db.flush()
        return role

    def update(self, role: Role, **kwargs) -> Role:
        for key, value in kwargs.items():
            if value is not None:
                setattr(role, key, value)
        self._db.flush()
        return role

    def delete(self, role: Role) -> None:
        self._db.delete(role)
        self._db.flush()

    def get_roles_for_user(self, user_id: str) -> list[Role]:
        return (
            self._db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )

    def assign_roles(self, user_id: str, role_ids: list[str]) -> None:
        self._db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        for role_id in role_ids:
            self._db.add(UserRole(user_id=user_id, role_id=role_id))
        self._db.flush()
