"""
2FA / TOTP endpoints.

Flow:
  1. POST /auth/2fa/setup     → возвращает secret + QR-код (base64 PNG)
  2. POST /auth/2fa/enable    → пользователь вводит OTP для подтверждения
  3. POST /auth/2fa/disable   → отключить 2FA (нужен OTP)
  4. GET  /auth/2fa/status    → включена ли 2FA
  5. POST /auth/2fa/verify    → проверка OTP при логине (если 2FA включена)
"""
import base64
import io
import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, UserTOTP

router = APIRouter(prefix="/auth/2fa", tags=["2FA / TOTP"])

APP_NAME = "AuthManager"


def _get_or_create_totp(db: Session, user_id: str) -> UserTOTP:
    record = db.query(UserTOTP).filter(UserTOTP.user_id == user_id).first()
    if not record:
        record = UserTOTP(user_id=user_id, secret=pyotp.random_base32(), is_enabled=False)
        db.add(record)
        db.flush()
    return record


class OTPRequest(BaseModel):
    otp: str


@router.get("/status", summary="Статус 2FA")
def totp_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(UserTOTP).filter(UserTOTP.user_id == user.id).first()
    return {"enabled": record.is_enabled if record else False}


@router.post("/setup", summary="Получить QR-код для настройки 2FA")
def totp_setup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Генерирует (или возвращает существующий) TOTP-секрет и QR-код."""
    record = _get_or_create_totp(db, user.id)
    db.commit()

    totp = pyotp.TOTP(record.secret)
    uri  = totp.provisioning_uri(name=user.email, issuer_name=APP_NAME)

    # Генерация QR-кода в base64 PNG
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "secret":  record.secret,
        "qr_code": f"data:image/png;base64,{qr_b64}",
        "enabled": record.is_enabled,
    }


@router.post("/enable", status_code=204, summary="Активировать 2FA")
def totp_enable(payload: OTPRequest,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    record = db.query(UserTOTP).filter(UserTOTP.user_id == user.id).first()
    if not record:
        raise HTTPException(400, detail="Сначала выполните /auth/2fa/setup.")
    if not pyotp.TOTP(record.secret).verify(payload.otp, valid_window=1):
        raise HTTPException(400, detail="Неверный код.")
    record.is_enabled = True
    db.commit()


@router.post("/disable", status_code=204, summary="Отключить 2FA")
def totp_disable(payload: OTPRequest,
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    record = db.query(UserTOTP).filter(UserTOTP.user_id == user.id).first()
    if not record or not record.is_enabled:
        raise HTTPException(400, detail="2FA не активирована.")
    if not pyotp.TOTP(record.secret).verify(payload.otp, valid_window=1):
        raise HTTPException(400, detail="Неверный код.")
    record.is_enabled = False
    db.commit()


@router.post("/verify", status_code=204, summary="Проверить OTP-код")
def totp_verify(payload: OTPRequest,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Используется фронтендом сразу после логина, если 2FA включена."""
    record = db.query(UserTOTP).filter(UserTOTP.user_id == user.id).first()
    if not record or not record.is_enabled:
        return  # 2FA не включена — пропускаем
    if not pyotp.TOTP(record.secret).verify(payload.otp, valid_window=1):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Неверный OTP-код.")
