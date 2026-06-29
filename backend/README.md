# Auth Manager — Backend

Backend-приложение с собственной системой аутентификации и авторизации на базе **FastAPI + SQLAlchemy + PostgreSQL**.

**v3.0.0** | [Root README](../README.md) | [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)

---

## Содержание

- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [База данных](#база-данных)
- [API Endpoints](#api-endpoints)
- [Безопасность](#безопасность)
- [Логирование](#логирование)
- [Конфигурация](#конфигурация)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Примеры запросов](#примеры-запросов)

---

## Архитектура

### Слои приложения

```
HTTP Request
    │
    ▼
Middleware (app/middleware/)
    ├── SecurityHeadersMiddleware  — OWASP заголовки на каждый ответ
    ├── RequestIDMiddleware        — X-Request-ID для трассировки
    └── SlowAPIMiddleware          — Rate limiting
    │
    ▼
API Layer (app/api/)              ← 9 роутеров, Pydantic валидация
    │
    ▼
Dependencies (app/core/dependencies.py)
    ├── get_current_token          — Проверка Bearer token в БД
    ├── get_current_user           — user.is_active?
    ├── require_permission(code)   — Проверка прав доступа
    └── require_admin              — Проверка роли administrator
    │
    ▼
Service Layer (app/services/)     ← Бизнес-логика
    ├── AuthService                — Регистрация, логин, сброс пароля
    ├── PermissionService          — Проверка разрешений
    ├── AuditService               — Запись действий в аудит-лог
    └── EmailService               — Отправка email (SMTP / console)
    │
    ▼
Repository Layer (app/repositories/) ← Работа с БД (N+1 queries solved)
    ├── UserRepository
    ├── TokenRepository
    ├── RoleRepository
    └── PermissionRepository
    │
    ▼
ORM Models (app/models/)          ← 10 SQLAlchemy моделей
    │
    ▼
PostgreSQL
```

### Поток запроса: регистрация

```
POST /auth/register
  → RegisterRequest (Pydantic + field_validator)
  → validate_password() — проверка политики паролей
  → AuthService.register():
      → UserRepository.get_by_email() — проверка уникальности
      → bcrypt.hashpw(password, gensalt(rounds=12))
      → UserRepository.create() — INSERT users
      → RoleRepository.assign_default_role()
      → AuditService.log("user.registered")
      → NotificationService.create("registered")
      → return UserResponse (201)
```

### Поток запроса: логин

```
POST /auth/login
  → LoginRequest (Pydantic)
  → AuthService.login():
      → timing-safe: UserRepository.get_by_email() ИЛИ dummy hash
      → bcrypt.checkpw(password, hash)
      → проверка 2FA (user_totp.is_enabled?)
      → generate_token() — HMAC-SHA256(os.urandom(32), SECRET_SALT)
      → TokenRepository.create() — INSERT access_tokens
      → update last_login_at
      → AuditService.log("user.login")
      → return TokenResponse (200)
```

### Поток запроса: защищённый ресурс

```
GET /reports + Authorization: Bearer <token>
  → get_current_token:
      → TokenRepository.get_valid_token(raw) — SELECT WHERE token=? AND expires_at>now
      → 401 если нет / истёк
  → get_current_user:
      → token_record.user
      → user.is_active? → 401 если нет
  → require_permission("reports:read"):
      → PermissionService.user_has_permission(user, code)
      → SELECT permissions через JOIN user → roles → permissions
      → 403 если нет
  → ReportsPage.list() — возвращает данные (200)
```

---

## Структура проекта

```
backend/
├── app/
│   ├── api/                        9 роутеров
│   │   ├── auth.py                 /auth/register, login, logout, me, profile, sessions,
│   │   │                           change-password, forgot/reset-password
│   │   ├── auth_refresh.py         /auth/refresh (продление токена)
│   │   ├── admin.py                /admin/users, roles, permissions CRUD + назначения
│   │   ├── admin_policy.py         /admin/policy — GET/PUT политика паролей
│   │   ├── resources.py            /reports, /documents, /settings (Mock API)
│   │   ├── totp.py                 /auth/2fa/status, setup, enable, disable, verify
│   │   ├── avatar.py               /avatars/upload, /avatars/{filename}
│   │   ├── bulk.py                 /admin/users/bulk/*, /admin/*/export/csv
│   │   └── ws.py                   /ws/notifications (WebSocket)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               Settings (pydantic-settings, env vars)
│   │   ├── database.py             Engine, SessionLocal, Base, get_db
│   │   ├── security.py             bcrypt.hash_password, verify_password, generate_token
│   │   ├── dependencies.py         get_current_token, get_current_user, require_permission, require_admin
│   │   ├── password_policy.py      validate_password(), get_policy()
│   │   ├── limiter.py              slowapi Limiter (автоотключение в тестах)
│   │   └── logging_config.py       JSON/Human форматтер, SENSITIVE-фильтр
│   ├── middleware/
│   │   └── security.py             SecurityHeadersMiddleware, RequestIDMiddleware
│   ├── models/
│   │   └── models.py               SQLAlchemy ORM: User, AccessToken, Role, Permission,
│   │                               UserRole, RolePermission, PasswordReset, AuditLog,
│   │                               Notification, UserTOTP
│   ├── repositories/
│   │   ├── user_repo.py            get_by_email, get_by_id, create, update, search
│   │   ├── token_repo.py           get_valid_token, get_all_for_user, create, delete, delete_all_for_user
│   │   ├── role_repo.py            get_all, get_by_id, get_by_name, create, update, delete,
│   │                               get_roles_for_user, assign_default_role
│   │   └── permission_repo.py      get_all, get_by_id, get_by_code, create, update, delete,
│   │                               get_codes_for_user, user_has_permission, assign_to_role
│   ├── schemas/
│   │   ├── auth.py                 RegisterRequest, LoginRequest, TokenResponse, UserResponse,
│   │                               UpdateProfileRequest, ChangePasswordRequest,
│   │                               ForgotPasswordRequest, ResetPasswordRequest, SessionResponse
│   │   ├── admin.py                RoleCreate/Update/Response, PermissionCreate/Update/Response,
│   │                               AssignRolesRequest, UserRoleResponse, AdminUpdateUserRequest,
│   │                               AdminSetPasswordRequest, AdminCreateUserRequest,
│   │                               NotificationResponse, AuditLogResponse
│   │   └── resources.py            ReportCreate/Response, DocumentCreate/Response, SettingsResponse
│   ├── services/
│   │   ├── auth_service.py         AuthService (register, login, logout, change_password,
│   │   │                           forgot_password, reset_password, update_profile, deactivate_account)
│   │   ├── permission_service.py   PermissionService (user_has_permission)
│   │   ├── audit_service.py        AuditService (log, get_all)
│   │   └── email_service.py        EmailService (send_password_reset, send_admin_notification)
│   └── seed/
│       └── seed.py                 Идемпотентный seed: 3 роли, 16 permissions,
│                                   23 пользователя (1 admin, 11 managers, 11 users)
├── alembic/
│   ├── env.py                      Alembic env (autogenerate отключён — ручная миграция)
│   └── versions/
│       └── a1b2c3d4e5f6_initial_schema.py  Единственная миграция (полная схема:
│                                            users, access_tokens, roles, permissions,
│                                            user_roles, role_permissions, password_resets,
│                                            audit_log, notifications, user_totp)
├── tests/
│   ├── conftest.py                 Фикстуры: test_client, test_db, admin_auth, manager_auth, user_auth
│   ├── unit/
│   │   ├── test_security.py        Тесты bcrypt hash/verify, token generation
│   │   └── test_schemas.py         Тесты Pydantic валидации (register, login, и т.д.)
│   └── integration/
│       ├── test_auth.py            Тесты: register, login, logout, me, profile, sessions,
│                                   change-password, forgot/reset-password, deactivate
│       ├── test_admin_crud.py      Тесты: CRUD roles, permissions, users, назначения, bulk, export
│       └── test_permissions.py     Тесты: разграничение доступа по ролям
├── uploads/avatars/                Директория для загруженных аватаров
├── docs/
│   ├── documentation.docx          Документация (Word)
│   └── schema.sql                  Схема БД (SQL)
├── Dockerfile                      Multi-stage (builder: gcc+libpq → runtime: libpq5+curl)
├── entrypoint.sh                   wait DB → alembic upgrade a1b2c3d4e5f6 → seed → uvicorn
├── requirements.txt                22 зависимости (FastAPI, SQLAlchemy, Alembic, bcrypt, pyotp...)
├── pytest.ini                      [pytest:env] TESTING=1, DATABASE_URL=sqlite://
├── alembic.ini                     script_location = alembic
└── .env.example                    Шаблон переменных окружения
```

---

## База данных

### ER-диаграмма

```
┌──────────────┐       ┌──────────────────┐
│    users     │       │  access_tokens   │
│──────────────│       │──────────────────│
│ id (UUID PK) │◀──────│ user_id (FK)     │
│ email (UQ)   │  1:N  │ token (UQ, idx)  │
│ password_hash│       │ expires_at       │
│ first_name   │       │ ip_address       │
│ last_name    │       │ user_agent       │
│ middle_name  │       │ created_at       │
│ recovery_email│      └──────────────────┘
│ is_active    │
│ last_login_at│       ┌──────────────────┐
│ deleted_at   │       │  password_resets │
│ avatar_url   │◀──────│──────────────────│
│ created_at   │  1:N  │ user_id (FK)     │
│ updated_at   │       │ token (UQ)       │
└──────┬───────┘       │ expires_at       │
       │               │ used             │
       │               └──────────────────┘
       │
       │ 1:N           ┌──────────────────┐
       ├───────────────│   user_roles     │
       │               │──────────────────│
       │               │ user_id (FK)     │
       │               │ role_id (FK)     │
       │               │ UQ(user,role)    │
       │               └────────┬─────────┘
       │                        │
       │               ┌────────┴──────────┐
       │               │      roles        │
       │               │───────────────────│
       │               │ id (UUID PK)      │
       │               │ name (UQ)         │
       │               │ description       │
       │               │ is_system         │
       │               └────────┬──────────┘
       │                        │
       │               ┌────────┴──────────────┐
       │               │   role_permissions    │
       │               │───────────────────────│
       │               │ role_id (FK)          │
       │               │ permission_id (FK)    │
       │               │ UQ(role,permission)   │
       │               └────────┬──────────────┘
       │                        │
       │               ┌────────┴──────────┐
       │               │   permissions     │
       │               │───────────────────│
       │               │ id (UUID PK)      │
       │               │ code (UQ, idx)    │ e.g. "reports:read"
       │               │ resource          │ e.g. "reports"
       │               │ action            │ e.g. "read"
       │               │ description       │
       │               └───────────────────┘
       │
       │ 1:N           ┌──────────────────┐
       ├───────────────│    audit_log     │
       │               │──────────────────│
       │               │ action           │ "user.login"
       │               │ entity_type      │ "user", "role"
       │               │ entity_id        │
       │               │ detail           │ JSON/free text
       │               │ ip_address       │
       │               │ created_at       │
       │               └──────────────────┘
       │
       │ 1:N           ┌──────────────────┐
       ├───────────────│  notifications   │
       │               │──────────────────│
       │               │ event            │ "registered"
       │               │ title            │
       │               │ body             │
       │               │ is_read          │
       │               │ created_at       │
       │               └──────────────────┘
       │
       │ 1:1           ┌──────────────────┐
       └───────────────│   user_totp      │
                       │──────────────────│
                       │ secret           │
                       │ is_enabled       │
                       └──────────────────┘
```

### Таблицы (10)

| Таблица | Назначение | Ключевые поля |
|---|---|---|
| `users` | Пользователи | `email (UQ)`, `password_hash`, `is_active`, `avatar_url` |
| `access_tokens` | Сессионные токены | `token (UQ,idx)`, `expires_at`, `user_id (FK)` |
| `roles` | Роли | `name (UQ)`, `is_system` |
| `permissions` | Разрешения | `code (UQ,idx)`, `resource`, `action` |
| `user_roles` | Связь M:N | `UQ(user_id, role_id)` |
| `role_permissions` | Связь M:N | `UQ(role_id, permission_id)` |
| `password_resets` | Сброс пароля | `token (UQ)`, `expires_at`, `used` |
| `audit_log` | Журнал аудита | `action`, `user_id (FK)`, `ip_address` |
| `notifications` | Уведомления | `event`, `title`, `is_read` |
| `user_totp` | 2FA | `secret`, `is_enabled`, `user_id (UQ, FK)` |

### Миграции

```bash
# Применить
alembic upgrade a1b2c3d4e5f6

# Откатить
alembic downgrade a1b2c3d4e5f6

# Создать новую (если потребуется)
alembic revision -m "description"
```

> **Важно**: `entrypoint.sh` выполняет `alembic upgrade a1b2c3d4e5f6` — явный revision target исключает ошибку multiple heads.

---

## API Endpoints

Полная документация: **http://localhost:8000/docs** (Swagger UI)

### Аутентификация `/auth`

| Метод | URL | Описание | Auth | Rate limit |
|---|---|---|---|---|
| POST | `/auth/register` | Регистрация нового пользователя (роль user по умолчанию) | — | 10/мин |
| POST | `/auth/login` | Логин, получение Bearer token | — | 10/мин |
| POST | `/auth/logout` | Инвалидировать текущий токен | Bearer | — |
| POST | `/auth/refresh` | Продлить токен (старый инвалидируется) | Bearer | — |
| GET | `/auth/me` | Профиль текущего пользователя | Bearer | — |
| GET | `/auth/me/roles` | Роли текущего пользователя | Bearer | — |
| GET | `/auth/me/permissions` | Разрешения текущего пользователя | Bearer | — |
| PUT | `/auth/profile` | Обновить профиль (имя, отчество, recovery_email) | Bearer | — |
| POST | `/auth/change-password` | Сменить пароль (нужен текущий) | Bearer | 5/мин |
| POST | `/auth/forgot-password` | Запросить сброс пароля (письмо) | — | 5/мин |
| POST | `/auth/reset-password` | Сбросить пароль по токену | — | 10/мин |
| DELETE | `/auth/profile` | Самодеактивация аккаунта | Bearer | — |
| GET | `/auth/me/sessions` | Список активных сессий | Bearer | — |
| DELETE | `/auth/me/sessions/{session_id}` | Завершить указанную сессию | Bearer | — |
| GET | `/auth/public/roles` | Публичный список ролей | — | — |
| GET | `/auth/password-policy` | Текущая политика паролей | — | — |

### 2FA `/auth/2fa`

| Метод | URL | Описание | Auth |
|---|---|---|---|
| GET | `/auth/2fa/status` | Статус 2FA (включена/выключена) | Bearer |
| POST | `/auth/2fa/setup` | Получить TOTP secret + QR-код (base64 PNG) | Bearer |
| POST | `/auth/2fa/enable` | Активировать 2FA (подтвердить OTP) | Bearer |
| POST | `/auth/2fa/disable` | Отключить 2FA (подтвердить OTP) | Bearer |
| POST | `/auth/2fa/verify` | Проверить OTP-код после логина | Bearer |

### Аватар `/avatars`

| Метод | URL | Описание | Auth |
|---|---|---|---|
| POST | `/avatars/upload` | Загрузить аватар | Bearer |
| GET | `/avatars/{filename}` | Получить аватар | — |

### Администрирование `/admin` (только администратор)

#### Пользователи

| Метод | URL | Описание |
|---|---|---|
| GET | `/admin/users` | Список пользователей (query: search, is_active, limit, offset) |
| POST | `/admin/users` | Создать пользователя (с опциональным указанием ролей) |
| GET | `/admin/users/{id}` | Профиль пользователя |
| PUT | `/admin/users/{id}` | Редактировать профиль |
| PATCH | `/admin/users/{id}/activate` | Активировать |
| PATCH | `/admin/users/{id}/deactivate` | Деактивировать (все токены удаляются) |
| DELETE | `/admin/users/{id}` | Hard delete (кроме себя) |
| POST | `/admin/users/{id}/set-password` | Установить пароль (все токены удаляются) |
| POST | `/admin/users/{id}/logout-all` | Завершить все сессии |
| GET | `/admin/users/{id}/roles` | Роли пользователя |
| POST | `/admin/users/{id}/roles` | Назначить роли |
| POST | `/admin/users/bulk/deactivate` | Массовая деактивация |
| POST | `/admin/users/bulk/activate` | Массовая активация |
| POST | `/admin/users/bulk/assign-role` | Массовое назначение роли |
| GET | `/admin/users/export/csv` | Экспорт пользователей в CSV |

#### Роли и разрешения

| Метод | URL | Описание |
|---|---|---|
| GET | `/admin/roles` | Список ролей |
| POST | `/admin/roles` | Создать роль |
| PUT | `/admin/roles/{id}` | Обновить роль |
| DELETE | `/admin/roles/{id}` | Удалить (кроме system) |
| GET | `/admin/roles/{id}/permissions` | Разрешения роли |
| POST | `/admin/roles/{id}/permissions` | Назначить разрешения роли |
| GET | `/admin/permissions` | Список разрешений |
| POST | `/admin/permissions` | Создать разрешение (code: `resource:action`) |
| PUT | `/admin/permissions/{id}` | Обновить описание |
| DELETE | `/admin/permissions/{id}` | Удалить |

#### Политика паролей

| Метод | URL | Описание |
|---|---|---|
| GET | `/admin/policy` | Текущая политика паролей |
| PUT | `/admin/policy` | Обновить политику (runtime) |

#### Уведомления и аудит

| Метод | URL | Описание |
|---|---|---|
| GET | `/admin/notifications` | Список уведомлений (`?unread_only=true`) |
| GET | `/admin/notifications/unread-count` | Количество непрочитанных |
| PATCH | `/admin/notifications/{id}/read` | Отметить прочитанным |
| PATCH | `/admin/notifications/read-all` | Отметить все прочитанными |
| GET | `/admin/audit-log` | Журнал аудита (с пагинацией и фильтрами) |
| GET | `/admin/audit-log/export/csv` | Экспорт аудита в CSV |

### Ресурсы (Mock API) — разрешения resource:action

| Метод | URL | Разрешение | admin | manager | user |
|---|---|---|---|---|---|
| GET | `/reports` | reports:read | ✅ | ✅ | ✅ |
| POST | `/reports` | reports:create | ✅ | ✅ | ❌ |
| PUT | `/reports/{id}` | reports:update | ✅ | ✅ | ❌ |
| DELETE | `/reports/{id}` | reports:delete | ✅ | ✅ | ❌ |
| GET | `/documents` | documents:read | ✅ | ✅ | ✅ |
| POST | `/documents` | documents:create | ✅ | ✅ | ❌ |
| PUT | `/documents/{id}` | documents:update | ✅ | ✅ | ❌ |
| DELETE | `/documents/{id}` | documents:delete | ✅ | ✅ | ❌ |
| GET | `/settings` | settings:read | ✅ | ✅ | ✅ |
| PUT | `/settings` | settings:update | ✅ | ❌ | ❌ |

### WebSocket

| URL | Описание |
|---|---|
| `ws://host/ws/notifications?token={access_token}` | Real-time уведомления для администратора |

### Health

| Метод | URL | Описание |
|---|---|---|
| GET | `/health` | `{"status": "ok", "version": "3.0.0"}` |

---

## Безопасность

### Почему Opaque Token, а не JWT

| Критерий | Opaque Token | JWT |
|---|---|---|
| Мгновенный logout | ✅ удаляем запись из access_tokens | ❌ нужен blocklist |
| Деактивация аккаунта | ✅ TokenRepository.delete_all_for_user() | ❌ ждём истечения всех JWT |
| Algorithm confusion | Нет подписи | alg:none, RS→HS confusion |
| Раскрытие данных | Токен непрозрачен | Base64 payload читается без ключа |
| Стоимость | +1 DB запрос / request | Нет DB запроса |

Формирование токена:

```python
raw   = os.urandom(32)           # 256 бит энтропии
token = HMAC-SHA256(salt, raw)   # привязка к конкретному серверу
```

### Bcrypt (без passlib)

bcrypt 4.x используется напрямую, без passlib, чтобы избежать проблем совместимости между passlib 1.7.x и bcrypt >= 4.0.

- `hash_password(plain)` → bcrypt.gensalt(rounds=12) → decode to str
- `verify_password(plain, hashed)` → bcrypt.checkpw() (timing-safe)

### Timing-safe login

Для несуществующих email генерируется dummy hash и выполняется `bcrypt.checkpw(dummy_password, dummy_hash)`, чтобы время ответа не зависело от существования пользователя.

### Rate Limiting

- Глобально: 200/мин (IP-based)
- `/auth/login`: 10/мин
- `/auth/register`: 10/мин
- `/auth/change-password`: 5/мин
- `/auth/forgot-password`: 5/мин
- `/auth/reset-password`: 10/мин

В тестах (`TESTING=1`) лимиты отключаются — каждый запрос получает уникальный ключ.

### OWASP Security Headers

Middleware `SecurityHeadersMiddleware` добавляет на каждый ответ:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### Non-root Docker user

```dockerfile
RUN useradd --system --no-create-home --shell /bin/false appuser
USER appuser
```

### Request-ID

Каждый запрос получает уникальный `X-Request-ID` (в заголовке запроса или UUID4).

---

## Логирование

Структурированное логирование через `app/core/logging_config.py`.

- **Production** (`LOG_FORMAT=json`): JSON-строки для CloudWatch, Datadog, Loki
- **Development** (`LOG_FORMAT=human`, по умолчанию): цветной human-readable вывод
- Пароли, токены, секреты **никогда** не попадают в логи (фильтр SENSITIVE полей)

Использование:

```python
from app.core.logging_config import get_logger
log = get_logger(__name__)
log.info("User logged in", extra={"user_id": user.id, "ip": ip})
```

---

## Конфигурация

Класс `Settings` в `app/core/config.py` использует `pydantic-settings`.

```python
class Settings(BaseSettings):
    DATABASE_URL:               str
    SECRET_SALT:                str
    ACCESS_TOKEN_EXPIRE_HOURS:  int  = 24
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60
    SMTP_HOST:                  str  = "smtp.gmail.com"
    SMTP_PORT:                  int  = 587
    SMTP_USER:                  str  = ""
    SMTP_PASSWORD:              str  = ""
    SMTP_FROM:                  str  = "noreply@auth-manager.local"
    SMTP_ENABLED:               bool = False
    FRONTEND_URL:               str  = "http://localhost:3000"
    ADMIN_EMAIL:                str  = "admin@example.com"
    PASSWORD_MIN_LENGTH:        int  = 8
    PASSWORD_REQUIRE_UPPER:     bool = False
    PASSWORD_REQUIRE_SPECIAL:   bool = False
    PASSWORD_EXPIRE_DAYS:       int  = 0

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
```

> **Примечание**: Политика паролей (`PASSWORD_*`) может быть изменена в runtime через `PUT /admin/policy`. Изменения применяются немедленно, но не сохраняются в env-файл.

---

## Разработка

### Быстрый старт

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate; Linux: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Отредактировать DATABASE_URL под свою БД

alembic upgrade a1b2c3d4e5f6
python -m app.seed.seed
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
# Локально (одной командой из корня проекта)
docker compose up --build
```

### Добавление нового API-эндпоинта

1. Создать Pydantic схему в `app/schemas/`
2. Добавить бизнес-логику в `app/services/`
3. Добавить/обновить Repository-метод (если нужен новый запрос к БД)
4. Создать или дополнить роутер в `app/api/`
5. Подключить роутер в `app/main.py`
6. Добавить тесты в `tests/`

### Seed-данные

`app/seed/seed.py` — идемпотентный скрипт. При повторном запуске не создаёт дубликатов (проверка по email/name/code).

Структура данных:
- **3 роли**: administrator, manager, user
- **16 разрешений**: users:*, reports:*, documents:*, settings:*, audit:read, notifications:read
- **23 пользователя**: 1 admin, 11 managers, 11 users

---

## Тестирование

**89 тестов** (19 unit + 70 integration), все без PostgreSQL (SQLite in-memory).

```bash
# Все тесты
TESTING=1 DATABASE_URL=sqlite:// python -m pytest tests/ -v

# Конкретные группы
TESTING=1 DATABASE_URL=sqlite:// python -m pytest tests/unit/ -v
TESTING=1 DATABASE_URL=sqlite:// python -m pytest tests/integration/ -v

# С coverage
TESTING=1 DATABASE_URL=sqlite:// python -m pytest --cov=app tests/ -v

# Без захвата stdout (для отладки)
TESTING=1 DATABASE_URL=sqlite:// python -m pytest -s tests/ -v
```

### Структура тестов

```
tests/
├── conftest.py               Фикстуры:
│                               - test_client (FastAPI TestClient + DB rollback)
│                               - test_db (SQLite in-memory с инициализацией схемы)
│                               - admin_auth (Bearer token администратора)
│                               - manager_auth (Bearer token менеджера)
│                               - user_auth (Bearer token пользователя)
├── unit/
│   ├── test_security.py       hash_password, verify_password, generate_token
│   └── test_schemas.py        RegisterRequest, LoginRequest, ChangePasswordRequest
└── integration/
    ├── test_auth.py           20+ тестов: регистрация, логин, logout, сессии,
    │                           смена пароля, forgot/reset, deactivate, профиль
    ├── test_admin_crud.py     30+ тестов: CRUD roles, permissions, users,
    │                           назначения ролей/разрешений, bulk, export
    └── test_permissions.py    15+ тестов: разграничение доступа по ролям,
                                защита системных ролей, 403 на запрещённые ресурсы
```

### Фикстуры

`conftest.py` предоставляет:

- `test_client` — `TestClient(app)` с автозакрытием сессии
- `test_db` — in-memory SQLite + создание схемы + seed
- `admin_auth` — `{"Authorization": "Bearer <admin_token>"}`
- `manager_auth` — `{"Authorization": "Bearer <manager_token>"}`
- `user_auth` — `{"Authorization": "Bearer <user_token>"}`

---

## Примеры запросов

### Регистрация

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ivan",
    "last_name": "Petrov",
    "email": "ivan@example.com",
    "password": "MySecret1",
    "password_repeat": "MySecret1"
  }'
```

### Логин

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin1234!"}'
```

### Запрос с токеном

```bash
TOKEN="<access_token>"
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Создание пользователя (admin)

```bash
ROLES=$(curl -s http://localhost:8000/admin/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python -c "import sys,json; roles=json.load(sys.stdin); print(json.dumps([r['id'] for r in roles]))")

curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"first_name\": \"New\", \"last_name\": \"User\", \"email\": \"new@example.com\", \"password\": \"Password123\", \"role_ids\": $ROLES}"
```

### Настройка 2FA

```bash
# Шаг 1: Получить QR-код
curl -X POST http://localhost:8000/auth/2fa/setup \
  -H "Authorization: Bearer $TOKEN"

# Шаг 2: Активировать (ввести OTP из приложения)
curl -X POST http://localhost:8000/auth/2fa/enable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"otp": "123456"}'
```

### Массовое назначение роли

```bash
curl -X POST http://localhost:8000/admin/users/bulk/assign-role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["<user-uuid-1>", "<user-uuid-2>"],
    "role_id": "<role-uuid>"
  }'
```

### Экспорт CSV

```bash
curl http://localhost:8000/admin/users/export/csv \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -o users.csv
```

---

## Коды ошибок

| Код | Описание |
|---|---|
| 400 | Bad Request — невалидные данные, несоответствие политике паролей |
| 401 | Unauthorized — токен отсутствует, истёк или недействителен |
| 403 | Forbidden — нет нужного разрешения (permission code) |
| 404 | Not Found — ресурс не найден |
| 409 | Conflict — email/role name/permission code уже существует |
| 422 | Unprocessable Entity — ошибка валидации Pydantic |
| 429 | Too Many Requests — превышен rate limit |
| 500 | Internal Server Error — внутренняя ошибка |

---

## Администрирование

### Журнал аудита

Все значимые действия записываются в `audit_log`:

- `user.login`, `user.logout`, `user.registered`
- `user.password_changed`, `user.password_reset`
- `user.profile_updated`, `user.deactivated`, `user.deleted`
- `admin.user_created`, `admin.user_updated`, `admin.user_activated`
- `admin.user_deactivated`, `admin.user_deleted`
- `admin.password_set`, `admin.sessions_revoked`
- `admin.role_created`, `admin.role_deleted`
- `admin.permission_created`, `admin.permission_deleted`
- `admin.bulk_deactivate`, `admin.bulk_activate`, `admin.bulk_assign_role`
- `admin.notification_sent`

### Уведомления (WebSocket)

Подключение: `ws://localhost:8000/ws/notifications?token={access_token}`

События:
- `user.registered` — новый пользователь зарегистрировался
- `user.deactivated` — пользователь самодеактивировался
- `user.profile_updated` — пользователь обновил профиль

---

## Troubleshooting

### "No module named psycopg2"

```bash
pip install psycopg2-binary
```

### "Multiple heads" в Alembic

```bash
alembic upgrade a1b2c3d4e5f6    # Явно указать revision
```

### Rate limit при тестах

```bash
TESTING=1 DATABASE_URL=sqlite:// pytest
```

### Логи контейнера

```bash
docker compose logs -f app
```
