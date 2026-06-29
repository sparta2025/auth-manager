from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL:               str  = "postgresql://postgres:postgres@localhost:5432/auth_db"
    SECRET_SALT:                str  = "change-this-to-random-secret-string-in-production"
    ACCESS_TOKEN_EXPIRE_HOURS:  int  = 24
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    # SMTP
    SMTP_HOST:     str  = "smtp.gmail.com"
    SMTP_PORT:     int  = 587
    SMTP_USER:     str  = ""
    SMTP_PASSWORD: str  = ""
    SMTP_FROM:     str  = "noreply@auth-manager.local"
    SMTP_ENABLED:  bool = False          # False = log to console only

    # Frontend base URL (for reset-password links)
    FRONTEND_URL:  str  = "http://localhost:3000"

    # Admin email for system notifications
    ADMIN_EMAIL:   str  = "admin@example.com"

    # Password policy (mutable at runtime via /admin/policy)
    PASSWORD_MIN_LENGTH:      int  = 8
    PASSWORD_REQUIRE_UPPER:   bool = False
    PASSWORD_REQUIRE_SPECIAL: bool = False
    PASSWORD_EXPIRE_DAYS:     int  = 0   # 0 = no expiry

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
