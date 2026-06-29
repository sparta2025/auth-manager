"""
User repository — v3.

Performance (правило performance.md):
  get_all() использует joinedload для user_roles и roles
  чтобы избежать N+1 запросов при отображении списка пользователей.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.models import User, UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: str) -> User | None:
        return (
            self._db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> User | None:
        return (
            self._db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(User.email == email)
            .first()
        )

    def get_all(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """
        Список пользователей с пагинацией и фильтрацией.
        joinedload устраняет N+1 при обращении к user.user_roles.
        """
        q = self._db.query(User).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
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

    def create(
        self, *, first_name: str, last_name: str, middle_name: str | None,
        email: str, recovery_email: str | None, password_hash: str,
    ) -> User:
        user = User(
            first_name=first_name, last_name=last_name, middle_name=middle_name,
            email=email, recovery_email=recovery_email,
            password_hash=password_hash, is_active=True,
        )
        self._db.add(user)
        self._db.flush()
        return user

    def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            # None допустимо для nullable полей
            if value is not None or key in ("middle_name", "recovery_email",
                                             "deleted_at", "avatar_url"):
                setattr(user, key, value)
        self._db.flush()
        return user

    def deactivate(self, user: User) -> User:
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        self._db.flush()
        return user

    def activate(self, user: User) -> User:
        user.is_active = True
        user.deleted_at = None
        self._db.flush()
        return user
