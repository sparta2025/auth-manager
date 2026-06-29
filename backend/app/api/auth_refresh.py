"""
Refresh token endpoint.
POST /auth/refresh — выдаёт новый access token по текущему валидному токену.
Клиент вызывает автоматически за 5 минут до истечения.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_token
from app.core.security import generate_token
from app.models.models import AccessToken
from app.schemas.auth import TokenResponse

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/refresh", response_model=TokenResponse,
             summary="Обновить access token")
def refresh_token(
    token_record: AccessToken = Depends(get_current_token),
    db: Session = Depends(get_db),
):
    """
    Принимает текущий валидный Bearer token, инвалидирует его
    и выдаёт новый с полным сроком жизни.
    Вызывается автоматически фронтендом за 5 минут до истечения.
    """
    from app.repositories.token_repo import TokenRepository
    repo = TokenRepository(db)

    # Создаём новый токен
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
    )
    new_token = repo.create(
        user_id=token_record.user_id,
        token=generate_token(),
        expires_at=expires_at,
        ip_address=token_record.ip_address,
        user_agent=token_record.user_agent,
    )

    # Удаляем старый
    repo.delete(token_record)
    db.commit()

    return TokenResponse(access_token=new_token.token, expires_at=new_token.expires_at)
