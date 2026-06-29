"""
Admin: управление политикой паролей через API.
Правило security.md: валидация на сервере, не только на клиенте.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import require_admin
from app.core.password_policy import get_policy
from app.models.models import User

router = APIRouter(prefix="/admin/policy", tags=["Политика паролей"])


class PasswordPolicyUpdate(BaseModel):
    min_length:       int  = Field(8, ge=4, le=128)
    require_upper:    bool = False
    require_special:  bool = False
    expire_days:      int  = Field(0, ge=0, le=365)


# In-memory store (в продакшене сохранять в Settings-таблицу БД)
_policy_override: dict = {}


@router.get("", summary="Текущая политика паролей")
def get_password_policy(_: User = Depends(require_admin)):
    return get_policy()


@router.put("", summary="Обновить политику паролей")
def update_password_policy(
    payload: PasswordPolicyUpdate,
    _: User = Depends(require_admin),
):
    """
    Обновляет политику паролей в runtime.
    Изменения применяются немедленно ко всем новым паролям.
    Примечание: для persistence перезапишите переменные окружения.
    """
    from app.core import config as cfg
    cfg.settings.PASSWORD_MIN_LENGTH     = payload.min_length
    cfg.settings.PASSWORD_REQUIRE_UPPER  = payload.require_upper
    cfg.settings.PASSWORD_REQUIRE_SPECIAL= payload.require_special
    cfg.settings.PASSWORD_EXPIRE_DAYS    = payload.expire_days
    return get_policy()
