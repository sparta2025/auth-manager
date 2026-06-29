"""FastAPI dependencies — auth + permission checks."""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import AccessToken, User
from app.repositories.token_repo import TokenRepository
from app.services.permission_service import PermissionService


def _extract_bearer(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует или некорректный заголовок Authorization.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth[7:]


def get_current_token(request: Request, db: Session = Depends(get_db)) -> AccessToken:
    raw = _extract_bearer(request)
    token_record = TokenRepository(db).get_valid_token(raw)
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен недействителен или истёк.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_record


def get_current_user(token_record: AccessToken = Depends(get_current_token)) -> User:
    user = token_record.user
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт не активен или удалён.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_permission(code: str):
    def _checker(user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> User:
        if not PermissionService(db).user_has_permission(user, code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется: '{code}'.",
            )
        return user
    return _checker


def require_admin(user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)) -> User:
    if not PermissionService(db).user_has_permission(user, "users:manage"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Требуются права администратора.")
    return user
