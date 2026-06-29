import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    first_name:     str           = Field(..., min_length=1, max_length=100)
    last_name:      str           = Field(..., min_length=1, max_length=100)
    middle_name:    str | None    = Field(None, max_length=100)
    email:          EmailStr
    recovery_email: EmailStr | None = None
    password:       str           = Field(..., min_length=8, max_length=128)
    password_repeat:str           = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_repeat:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str      = "bearer"
    expires_at:   datetime


class UserResponse(BaseModel):
    id:             str
    first_name:     str
    last_name:      str
    middle_name:    str | None
    email:          str
    recovery_email: str | None
    is_active:      bool
    last_login_at:  datetime | None
    avatar_url:     str | None
    created_at:     datetime
    updated_at:     datetime

    model_config = {"from_attributes": True}


class UserWithRolesResponse(UserResponse):
    roles: list[dict] = []

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    first_name:     str | None = Field(None, min_length=1, max_length=100)
    last_name:      str | None = Field(None, min_length=1, max_length=100)
    middle_name:    str | None = Field(None, max_length=100)
    recovery_email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password:     str = Field(..., min_length=8, max_length=128)
    new_password_repeat: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.new_password_repeat:
            raise ValueError("Passwords do not match.")
        return self


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token:        str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_repeat: str = Field(..., min_length=8)

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.new_password_repeat:
            raise ValueError("Passwords do not match.")
        return self


class SessionResponse(BaseModel):
    id:         str
    created_at: datetime
    expires_at: datetime
    ip_address: str | None
    user_agent: str | None

    model_config = {"from_attributes": True}
