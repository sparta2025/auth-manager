"""
Avatar upload endpoint.
POST /auth/avatar  — загрузка файла (multipart/form-data)
GET  /avatars/{filename} — отдача файла
DELETE /auth/avatar — удаление аватара
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User

router = APIRouter(tags=["Аватар"])

UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/auth/avatar", summary="Загрузить аватар")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, detail="Допустимы только JPEG, PNG, WebP, GIF.")

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(400, detail="Файл не должен превышать 5 МБ.")

    # Удаляем старый аватар если есть
    if user.avatar_url:
        old_path = Path("uploads/avatars") / Path(user.avatar_url).name
        if old_path.exists():
            old_path.unlink()

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(content)

    user.avatar_url = f"/avatars/{filename}"
    db.commit()

    return {"avatar_url": user.avatar_url}


@router.delete("/auth/avatar", status_code=204, summary="Удалить аватар")
def delete_avatar(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.avatar_url:
        path = Path("uploads/avatars") / Path(user.avatar_url).name
        if path.exists():
            path.unlink()
        user.avatar_url = None
        db.commit()


@router.get("/avatars/{filename}", summary="Получить файл аватара")
def get_avatar(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(404, detail="Аватар не найден.")
    return FileResponse(path)
