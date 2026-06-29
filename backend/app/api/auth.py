"""Auth API — v3 with rate limiting."""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_token, get_current_user
from app.core.limiter import limiter
from app.models.models import AccessToken, User
from app.repositories.role_repo import RoleRepository
from app.repositories.token_repo import TokenRepository
from app.repositories.permission_repo import PermissionRepository
from app.schemas.auth import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest,
    RegisterRequest, ResetPasswordRequest, SessionResponse,
    TokenResponse, UpdateProfileRequest, UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/minute")
def register(request: Request, payload: RegisterRequest,
             db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return AuthService(db).register(payload, ip=ip)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest,
          db: Session = Depends(get_db)):
    token_record = AuthService(db).login(payload, request=request)
    return TokenResponse(access_token=token_record.token,
                         expires_at=token_record.expires_at)


@router.post("/logout", status_code=204)
def logout(token_record: AccessToken = Depends(get_current_token),
           db: Session = Depends(get_db)):
    AuthService(db).logout(token_record)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/roles")
def get_my_roles(current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    roles = RoleRepository(db).get_roles_for_user(current_user.id)
    return [{"id": r.id, "name": r.name, "description": r.description,
             "is_system": r.is_system} for r in roles]


@router.get("/me/permissions")
def get_my_permissions(current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    codes = PermissionRepository(db).get_codes_for_user(current_user.id)
    return sorted(codes)


@router.put("/profile", response_model=UserResponse)
def update_profile(payload: UpdateProfileRequest, request: Request,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return AuthService(db).update_profile(current_user, payload, ip=ip)


@router.post("/change-password", status_code=204)
@limiter.limit("5/minute")
def change_password(request: Request, payload: ChangePasswordRequest,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    AuthService(db).change_password(current_user, payload)


@router.post("/forgot-password", status_code=204)
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest,
                    db: Session = Depends(get_db)):
    AuthService(db).forgot_password(payload)


@router.post("/reset-password", status_code=204)
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest,
                   db: Session = Depends(get_db)):
    AuthService(db).reset_password(payload)


@router.delete("/profile", status_code=204)
def delete_account(request: Request,
                   current_user: User = Depends(get_current_user),
                   token_record: AccessToken = Depends(get_current_token),
                   db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    AuthService(db).deactivate_account(current_user, token_record, ip=ip)


@router.get("/me/sessions", response_model=list[SessionResponse])
def my_sessions(current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return TokenRepository(db).get_all_for_user(current_user.id)


@router.delete("/me/sessions/{session_id}", status_code=204)
def revoke_session(session_id: str,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    from fastapi import HTTPException
    repo = TokenRepository(db)
    token = repo.get_by_id(session_id)
    if not token or token.user_id != current_user.id:
        raise HTTPException(404, detail="Сессия не найдена.")
    repo.delete(token)
    db.commit()


@router.get("/public/roles")
def public_roles(db: Session = Depends(get_db)):
    roles = RoleRepository(db).get_public()
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]


@router.get("/password-policy", summary="Получить политику паролей")
def password_policy():
    from app.core.password_policy import get_policy
    return get_policy()
