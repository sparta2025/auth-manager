-- ============================================================
--  Auth Manager v3 — полная схема PostgreSQL
--  Применяется автоматически через Alembic (alembic upgrade head)
--  или вручную: psql -U postgres -d auth_db -f schema.sql
-- ============================================================

-- Создать базу (выполнять от суперпользователя, если БД не существует)
-- CREATE DATABASE auth_db;
-- \c auth_db

-- ── Служебная таблица Alembic ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- ── users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36)  PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    middle_name     VARCHAR(100),
    email           VARCHAR(255) NOT NULL UNIQUE,
    recovery_email  VARCHAR(255),
    password_hash   VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(512),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- ── roles ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id          VARCHAR(36)  PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_system   BOOLEAN      NOT NULL DEFAULT FALSE
);

-- ── permissions ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS permissions (
    id          VARCHAR(36)  PRIMARY KEY,
    code        VARCHAR(100) NOT NULL UNIQUE,  -- 'reports:read'
    resource    VARCHAR(100) NOT NULL,          -- 'reports'
    action      VARCHAR(50)  NOT NULL,          -- 'read'
    description TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_permissions_code ON permissions (code);

-- ── access_tokens ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS access_tokens (
    id          VARCHAR(36) PRIMARY KEY,
    user_id     VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_agent  VARCHAR(512),
    ip_address  VARCHAR(45)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_access_tokens_token   ON access_tokens (token);
CREATE        INDEX IF NOT EXISTS ix_access_tokens_user_id ON access_tokens (user_id);

-- ── user_roles ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_roles (
    id      VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id VARCHAR(36) NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);

-- ── role_permissions ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS role_permissions (
    id            VARCHAR(36) PRIMARY KEY,
    role_id       VARCHAR(36) NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
    permission_id VARCHAR(36) NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
);

-- ── password_resets ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_resets (
    id          VARCHAR(36) PRIMARY KEY,
    user_id     VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── audit_log ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          VARCHAR(36)  PRIMARY KEY,
    user_id     VARCHAR(36)  REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id   VARCHAR(36),
    detail      TEXT,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_audit_log_user_id    ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_log_created_at ON audit_log (created_at);

-- ── notifications ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id          VARCHAR(36)  PRIMARY KEY,
    user_id     VARCHAR(36)  REFERENCES users(id) ON DELETE SET NULL,
    event       VARCHAR(100) NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT,
    link        VARCHAR(512),
    is_read     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── user_totp (2FA) ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_totp (
    id          VARCHAR(36) PRIMARY KEY,
    user_id     VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    secret      VARCHAR(64) NOT NULL,
    is_enabled  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_totp_user_id ON user_totp (user_id);

-- ── Отметить миграцию как применённую (если схема создана вручную) ────────────
INSERT INTO alembic_version (version_num)
VALUES ('a1b2c3d4e5f6')
ON CONFLICT DO NOTHING;

-- ============================================================
--  Для локальной разработки: создать тестовых пользователей
--  запускается отдельно через: python -m app.seed.seed
-- ============================================================
