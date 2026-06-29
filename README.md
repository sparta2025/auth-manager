# Auth Manager v3

Полностековое приложение для управления аутентификацией, авторизацией и профилями пользователей с собственной RBAC-моделью.

[![CI](https://github.com/sparta2025/auth-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/sparta2025/auth-manager/actions/workflows/ci.yml)
![Backend Tests](https://img.shields.io/badge/backend-89%2F89-brightgreen)
![Frontend Tests](https://img.shields.io/badge/frontend-30%2F30-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Node](https://img.shields.io/badge/node-20-blue)

---

## Содержание

- [Архитектура](#архитектура)
- [Стек](#стек)
- [Функциональность](#функциональность)
- [Быстрый старт (Docker Compose)](#быстрый-старт-docker-compose)
- [Локальная разработка](#локальная-разработка)
- [Структура проекта](#структура-проекта)
- [API Reference](#api-reference)
- [RBAC-модель](#rbac-модель)
- [Политика паролей](#политика-паролей)
- [Безопасность](#безопасность)
- [Переменные окружения](#переменные-окружения)
- [Деплой](#деплой)
- [CI/CD](#cicd)
- [Тестирование](#тестирование)
- [Тестовые пользователи](#тестовые-пользователи)
- [Журнал аудита](#журнал-аудита)

---

## Архитектура

```
┌──────────────┐     ┌──────────────────────┐     ┌────────────┐
│   Browser    │────▶│  Nginx Reverse Proxy │────▶│  FastAPI   │
│  React SPA   │◀────│  (frontend:80)       │◀────│  (:8000)   │
└──────────────┘     └──────────────────────┘     └─────┬──────┘
      │                       │                          │
      │  WebSocket            │  /ws/                    │
      └───────────────────────┘                          │
                                                         ▼
                                                  ┌──────────────┐
                                                  │  PostgreSQL  │
                                                  │   (:5432)    │
                                                  └──────────────┘
```

**Слои backend:**

```
HTTP Request
    │
    ▼
Middleware (CORS, SecurityHeaders, RequestID, SlowAPI)
    │
    ▼
API Layer (app/api/)          ← маршруты, валидация HTTP
    │
    ▼
Dependencies (app/core/dependencies.py) ← аутентификация, проверка прав
    │
    ▼
Service Layer (app/services/) ← бизнес-логика
    │
    ▼
Repository Layer (app/repositories/) ← работа с БД
    │
    ▼
ORM Models (app/models/)      ← SQLAlchemy модели
    │
    ▼
PostgreSQL
```

**Поток запроса:**

```
Регистрация:
  POST /auth/register
    → RegisterRequest (валидация Pydantic + password policy)
    → проверка уникальности email
    → bcrypt(password, rounds=12)
    → INSERT users
    → создание Notification для администратора
    → 201 UserResponse

Логин:
  POST /auth/login
    → timing-safe поиск user по email
    → bcrypt.verify(password, hash)
    → 2FA check (если включена)
    → генерация HMAC-SHA256 токена (64 hex)
    → INSERT access_tokens (expires_at = now + 24h)
    → 200 TokenResponse

Запрос к защищённому ресурсу:
  GET /reports  +  Authorization: Bearer <token>
    → get_current_token: SELECT access_tokens WHERE token=? AND expires_at>now
    → get_current_user: user.is_active?
    → require_permission("reports:read"):
        JOIN: user → user_roles → role_permissions → permissions.code
    → 200 OK  |  401  |  403
```

---

## Стек

| Слой | Технология |
|---|---|
| **Backend** | FastAPI 0.111 + SQLAlchemy 2.0 + Alembic 1.13 + PostgreSQL 16 |
| **Frontend** | React 19 + Vite 8 + TypeScript 6 + Tailwind CSS 3 |
| **Фреймворк auth** | Собственная реализация (Opaque Session Token, HMAC-SHA256) |
| **Хэширование** | bcrypt 4.x (cost=12) |
| **2FA** | TOTP (pyotp + qrcode + Pillow) |
| **Rate Limiting** | slowapi (200/мин глобально) |
| **Email** | aiosmtplib (SMTP с консольным fallback) |
| **Валидация** | Pydantic v2 + email-validator |
| **Security** | OWASP Headers, CSP, X-Frame-Options, HSTS |
| **Тесты backend** | pytest 8 + pytest-asyncio + httpx + SQLite in-memory |
| **Тесты frontend** | Vitest 4 + Testing Library + MSW |
| **Контейнеризация** | Docker multi-stage + Docker Compose |
| **CI/CD** | GitHub Actions (tests → build → deploy) |

---

## Функциональность

### Аутентификация
- Регистрация с валидацией пароля по политике
- Логин с Bearer token
- Logout (мгновенная инвалидация токена)
- Смена пароля (с подтверждением текущего)
- Восстановление пароля через email (токен 60 мин)
- Refresh token (продление сессии)
- 2FA / TOTP (Google Authenticator, Authy)
- Аватар (загрузка/просмотр)
- Просмотр и завершение сессий

### Администрирование
- CRUD пользователей (создание, редактирование, поиск, фильтрация)
- CRUD ролей (с защитой системных ролей от удаления)
- CRUD разрешений (resource:action)
- Назначение ролей пользователям
- Назначение разрешений ролям
- Hard delete, activate, deactivate пользователей
- Массовые операции: activate, deactivate, assign-role
- Принудительный logout всех сессий пользователя
- Установка пароля пользователю администратором
- Экспорт пользователей в CSV
- Журнал аудита с экспортом в CSV
- Управление политикой паролей (runtime)
- Real-time уведомления (WebSocket)

### Пользовательский кабинет
- Просмотр/редактирование профиля
- Просмотр своих ролей и разрешений
- Управление 2FA
- Управление сессиями
- Самодеактивация

### Ресурсы (Mock API для демонстрации RBAC)
- **Reports** — CRUD (разрешения: reports:*)
- **Documents** — CRUD (разрешения: documents:*)
- **Settings** — read/update (разрешения: settings:*)

---

## Быстрый старт (Docker Compose)

```bash
cd authorization-personal-account-management

# Создать .env из шаблона
cp .env.example .env
# ⚠️ Отредактируйте SECRET_SALT (обязательно!)

# Запуск одной командой:
docker compose up --build
```

После запуска:

| Сервис | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

Docker Compose автоматически:
1. Запускает PostgreSQL 16
2. Применяет миграции Alembic (revision `a1b2c3d4e5f6`)
3. Загружает seed-данные (23 пользователя, 3 роли, 16 разрешений)
4. Запускает backend (uvicorn на :8000)
5. Запускает frontend (Nginx на :80, mapped на :3000)

---

## Локальная разработка

### Backend

```bash
cd backend

# Виртуальное окружение
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

pip install -r requirements.txt

# Настройка БД (нужен запущенный PostgreSQL)
cp .env.example .env
# Отредактируйте DATABASE_URL под свою БД

# Миграция + seed
alembic upgrade a1b2c3d4e5f6
python -m app.seed.seed

# Запуск dev-сервера с hot-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install

# Vite проксирует /auth/, /admin/ и другие на localhost:8000
npm run dev
# → http://localhost:5173

# Сборка production
npm run build
```

---

## Структура проекта

```
.
├── backend/                          FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/                      Эндпоинты
│   │   │   ├── auth.py               /auth/* (register, login, logout, me, profile, sessions, forgot/reset password)
│   │   │   ├── auth_refresh.py       /auth/refresh (продление токена)
│   │   │   ├── admin.py              /admin/* (users, roles, permissions CRUD)
│   │   │   ├── admin_policy.py       /admin/policy (управление политикой паролей)
│   │   │   ├── resources.py          /reports, /documents, /settings (Mock API)
│   │   │   ├── totp.py               /auth/2fa/* (TOTP setup, enable, disable, verify)
│   │   │   ├── avatar.py             /avatars/* (загрузка/получение аватаров)
│   │   │   ├── bulk.py               /admin/users/bulk/*, /admin/*/export/csv
│   │   │   └── ws.py                 /ws/notifications (WebSocket)
│   │   ├── core/
│   │   │   ├── config.py             Settings (pydantic-settings, env vars)
│   │   │   ├── database.py           engine, SessionLocal, get_db
│   │   │   ├── security.py           bcrypt, HMAC-SHA256 token generation
│   │   │   ├── dependencies.py       get_current_token, get_current_user, require_permission, require_admin
│   │   │   ├── password_policy.py    validate_password(), get_policy()
│   │   │   ├── limiter.py            slowapi rate limiter
│   │   │   └── logging_config.py     Структурированный JSON логгер
│   │   ├── middleware/               Безопасность
│   │   │   └── security.py           SecurityHeadersMiddleware, RequestIDMiddleware
│   │   ├── models/
│   │   │   └── models.py             User, AccessToken, Role, Permission, UserRole,
│   │   │                             RolePermission, PasswordReset, AuditLog, Notification, UserTOTP
│   │   ├── repositories/            DB-слой
│   │   │   ├── user_repo.py          UserRepository
│   │   │   ├── token_repo.py         TokenRepository
│   │   │   ├── role_repo.py          RoleRepository
│   │   │   └── permission_repo.py    PermissionRepository
│   │   ├── schemas/                  Pydantic v2 схемы
│   │   │   ├── auth.py               RegisterRequest, LoginRequest, TokenResponse, UserResponse, SessionResponse
│   │   │   ├── admin.py              RoleCreate/Update/Response, PermissionCreate/Update/Response, AdminCreateUserRequest
│   │   │   └── resources.py          ReportCreate/Response, DocumentCreate/Response, SettingsResponse
│   │   ├── services/                 Бизнес-логика
│   │   │   ├── auth_service.py       AuthService (register, login, logout, forgot/reset password, change_password, update_profile, deactivate)
│   │   │   ├── permission_service.py PermissionService
│   │   │   ├── audit_service.py      AuditService
│   │   │   └── email_service.py      EmailService (SMTP / console)
│   │   └── seed/
│   │       └── seed.py               Идемпотентный seed (3 роли, 16 permissions, 23 пользователя)
│   ├── alembic/                      Миграции
│   │   ├── versions/
│   │   │   └── a1b2c3d4e5f6_initial_schema.py  Единственная миграция (полная схема)
│   │   └── env.py
│   ├── tests/
│   │   ├── conftest.py               Фикстуры (test client, test db, auth headers)
│   │   ├── unit/
│   │   │   ├── test_security.py      bcrypt hash/verify, token generation
│   │   │   └── test_schemas.py       Pydantic валидация
│   │   └── integration/
│   │       ├── test_auth.py          Регистрация, логин, logout, profile, forgot/reset password
│   │       ├── test_admin_crud.py    CRUD пользователей, ролей, разрешений, назначения
│   │       └── test_permissions.py   Проверка разграничения доступа
│   ├── uploads/                      Загруженные аватары
│   ├── Dockerfile                    Multi-stage (builder → runtime), non-root
│   ├── entrypoint.sh                 wait DB → alembic upgrade → seed → uvicorn
│   ├── requirements.txt              Python-зависимости
│   ├── pytest.ini                    Конфиг pytest (TESTING=1, DATABASE_URL=sqlite://)
│   └── alembic.ini                   Конфиг Alembic
│
├── frontend/                         React + Vite + TypeScript
│   ├── src/
│   │   ├── api/                      HTTP клиент
│   │   │   ├── client.ts             Axios instance + interceptors + error handler
│   │   │   ├── auth.ts               authApi (login, register, me, myRoles, myPermissions, sessions, 2FA)
│   │   │   ├── admin.ts              adminApi (users, roles, permissions, notifications, audit)
│   │   │   └── resources.ts          reportsApi, documentsApi, settingsApi
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.tsx     Sidebar + User block + Navigation + Notifications
│   │   │   │   └── ProtectedRoute.tsx Auth guard
│   │   │   └── ui/
│   │   │       ├── index.tsx         Spinner, PageLoader, Alert, Modal, ConfirmModal, Table, Badge, EmptyState, DangerZone
│   │   │       ├── PasswordStrength.tsx Визуальный индикатор надёжности пароля
│   │   │       └── ThemeToggle.tsx   Светлая/Тёмная/Системная тема
│   │   ├── hooks/
│   │   │   ├── useTokenRefresh.ts    Автообновление токена за 5 мин до истечения
│   │   │   ├── useTheme.ts           Управление темой (localStorage + system preference)
│   │   │   └── useNotificationSocket.ts  WebSocket для real-time уведомлений
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── RegisterPage.tsx
│   │   │   │   ├── ForgotPasswordPage.tsx
│   │   │   │   ├── ResetPasswordPage.tsx
│   │   │   │   ├── DashboardPage.tsx
│   │   │   │   ├── ProfilePage.tsx
│   │   │   │   ├── SessionsPage.tsx
│   │   │   │   └── TwoFactorPage.tsx
│   │   │   ├── admin/
│   │   │   │   ├── UsersPage.tsx
│   │   │   │   ├── RolesPage.tsx
│   │   │   │   ├── PermissionsPage.tsx
│   │   │   │   ├── NotificationsPage.tsx
│   │   │   │   ├── AuditLogPage.tsx
│   │   │   │   └── PolicyPage.tsx
│   │   │   └── resources/
│   │   │       ├── ReportsPage.tsx
│   │   │       ├── DocumentsPage.tsx
│   │   │       └── SettingsPage.tsx
│   │   ├── store/
│   │   │   └── auth.tsx              AuthContext + AuthProvider (state: user, roles, permissions, isAuthenticated, isLoading, isAdmin)
│   │   ├── types/
│   │   │   └── index.ts              TypeScript типы (User, Role, Permission, TokenResponse, SessionInfo, Report, Document, Settings, Notification, AuditEntry)
│   │   └── test/
│   │       ├── setup.ts              Настройка MSW + Testing Library
│   │       ├── mocks/
│   │       │   ├── server.ts         MSW server
│   │       │   └── handlers.ts       MSW handlers
│   │       ├── unit/
│   │       │   ├── tokenRefresh.test.ts
│   │       │   └── security.test.ts
│   │       └── integration/
│   │           ├── auth.test.tsx
│   │           ├── rbac.test.tsx
│   │           └── notifications.test.tsx
│   ├── Dockerfile                    Multi-stage (node → nginx)
│   ├── nginx.conf                    Rate limiting, security headers, proxy, gzip, SPA
│   ├── vite.config.ts                Vite + proxy backend
│   └── vitest.config.ts              Vitest with jsdom
│
├── deploy/                           Конфиги деплоя
│   ├── railway/                      railway.toml + инструкция
│   ├── render/                       render.yaml + инструкция
│   ├── vps/                          deploy.sh + nginx-ssl.conf + инструкция
│   └── github-actions/               deploy.yml
│
├── .github/workflows/
│   ├── ci.yml                        Tests (backend + frontend) + Docker build check
│   └── deploy.yml                    Build & push images → SSH deploy on main
│
├── docker-compose.yml                Локальная разработка (db + app + frontend)
├── docker-compose.prod.yml           Production (replicas, internal network, SSL)
├── .env.example                      Все переменные окружения с комментариями
└── README.md                         ← Этот файл
```

---

## API Reference

Полная документация: **http://localhost:8000/docs** (Swagger UI) и **http://localhost:8000/redoc** (ReDoc).

### Аутентификация (`/auth`)

| Метод | URL | Описание | Auth | Rate Limit |
|---|---|---|---|---|
| POST | `/auth/register` | Регистрация нового пользователя | — | 10/мин |
| POST | `/auth/login` | Логин, получение Bearer token | — | 10/мин |
| POST | `/auth/logout` | Инвалидация токена | Bearer | — |
| POST | `/auth/refresh` | Продление токена (старый инвалидируется) | Bearer | — |
| GET | `/auth/me` | Профиль текущего пользователя | Bearer | — |
| GET | `/auth/me/roles` | Роли текущего пользователя | Bearer | — |
| GET | `/auth/me/permissions` | Разрешения текущего пользователя | Bearer | — |
| PUT | `/auth/profile` | Обновление профиля (имя, отчество, recovery_email) | Bearer | — |
| POST | `/auth/change-password` | Смена пароля | Bearer | 5/мин |
| POST | `/auth/forgot-password` | Запрос сброса пароля (письмо на email) | — | 5/мин |
| POST | `/auth/reset-password` | Сброс пароля по токену из письма | — | 10/мин |
| DELETE | `/auth/profile` | Самодеактивация аккаунта | Bearer | — |
| GET | `/auth/me/sessions` | Список активных сессий | Bearer | — |
| DELETE | `/auth/me/sessions/{id}` | Завершить сессию | Bearer | — |
| GET | `/auth/public/roles` | Публичный список ролей | — | — |
| GET | `/auth/password-policy` | Текущая политика паролей | — | — |

### 2FA (`/auth/2fa`)

| Метод | URL | Описание | Auth |
|---|---|---|---|
| GET | `/auth/2fa/status` | Статус 2FA (включена/выключена) | Bearer |
| POST | `/auth/2fa/setup` | Получить TOTP secret + QR-код (base64 PNG) | Bearer |
| POST | `/auth/2fa/enable` | Активировать 2FA (подтвердить OTP) | Bearer |
| POST | `/auth/2fa/disable` | Отключить 2FA (подтвердить OTP) | Bearer |
| POST | `/auth/2fa/verify` | Проверить OTP-код (после логина) | Bearer |

### Аватар (`/avatars`)

| Метод | URL | Описание | Auth |
|---|---|---|---|
| POST | `/avatars/upload` | Загрузить аватар | Bearer |
| GET | `/avatars/{filename}` | Получить аватар | — |

### Администрирование (`/admin`) — только `administrator`

| Метод | URL | Описание |
|---|---|---|
| GET | `/admin/users` | Список пользователей (с поиском, фильтром, пагинацией) |
| POST | `/admin/users` | Создать пользователя |
| GET | `/admin/users/{id}` | Профиль пользователя |
| PUT | `/admin/users/{id}` | Редактировать пользователя |
| PATCH | `/admin/users/{id}/activate` | Активировать пользователя |
| PATCH | `/admin/users/{id}/deactivate` | Деактивировать пользователя |
| DELETE | `/admin/users/{id}` | Hard delete пользователя |
| POST | `/admin/users/{id}/set-password` | Установить пароль |
| POST | `/admin/users/{id}/logout-all` | Завершить все сессии |
| GET | `/admin/users/{id}/roles` | Роли пользователя |
| POST | `/admin/users/{id}/roles` | Назначить роли |
| POST | `/admin/users/bulk/deactivate` | Массовая деактивация |
| POST | `/admin/users/bulk/activate` | Массовая активация |
| POST | `/admin/users/bulk/assign-role` | Массовое назначение роли |
| GET | `/admin/users/export/csv` | Экспорт пользователей в CSV |
| GET | `/admin/roles` | Список ролей |
| POST | `/admin/roles` | Создать роль |
| PUT | `/admin/roles/{id}` | Обновить роль |
| DELETE | `/admin/roles/{id}` | Удалить роль (кроме system) |
| GET | `/admin/roles/{id}/permissions` | Разрешения роли |
| POST | `/admin/roles/{id}/permissions` | Назначить разрешения роли |
| GET | `/admin/permissions` | Список разрешений |
| POST | `/admin/permissions` | Создать разрешение |
| PUT | `/admin/permissions/{id}` | Обновить разрешение |
| DELETE | `/admin/permissions/{id}` | Удалить разрешение |
| GET | `/admin/policy` | Текущая политика паролей |
| PUT | `/admin/policy` | Обновить политику паролей (runtime) |
| GET | `/admin/notifications` | Уведомления |
| GET | `/admin/notifications/unread-count` | Количество непрочитанных |
| PATCH | `/admin/notifications/{id}/read` | Отметить прочитанным |
| PATCH | `/admin/notifications/read-all` | Отметить все прочитанными |
| GET | `/admin/audit-log` | Журнал аудита |
| GET | `/admin/audit-log/export/csv` | Экспорт аудита в CSV |

### Ресурсы (Mock API)

| Метод | URL | Требуемое разрешение |
|---|---|---|
| GET | `/reports` | reports:read |
| POST | `/reports` | reports:create |
| PUT | `/reports/{id}` | reports:update |
| DELETE | `/reports/{id}` | reports:delete |
| GET | `/documents` | documents:read |
| POST | `/documents` | documents:create |
| PUT | `/documents/{id}` | documents:update |
| DELETE | `/documents/{id}` | documents:delete |
| GET | `/settings` | settings:read |
| PUT | `/settings` | settings:update |

### WebSocket

| URL | Описание |
|---|---|
| `ws://host/ws/notifications?token={access_token}` | Real-time уведомления для администратора |

### Health

| Метод | URL | Описание |
|---|---|---|
| GET | `/health` | Health check (status, version) |

---

## RBAC-модель

Схема: **пользователь → роли → разрешения**.

Каждое разрешение имеет формат `resource:action`:

- `users:create`, `users:read`, `users:update`, `users:delete`, `users:manage`
- `reports:create`, `reports:read`, `reports:update`, `reports:delete`
- `documents:create`, `documents:read`, `documents:update`, `documents:delete`
- `settings:read`, `settings:update`
- `audit:read`
- `notifications:read`

### Матрица доступа по умолчанию

| Разрешение | administrator | manager | user |
|---|---|---|---|
| users:* (5 разрешений) | ✅ | ❌ | ❌ |
| reports:create/update/delete | ✅ | ✅ | ❌ |
| reports:read | ✅ | ✅ | ✅ |
| documents:create/update/delete | ✅ | ✅ | ❌ |
| documents:read | ✅ | ✅ | ✅ |
| settings:read | ✅ | ✅ | ✅ |
| settings:update | ✅ | ❌ | ❌ |
| audit:read | ✅ | ❌ | ❌ |
| notifications:read | ✅ | ❌ | ❌ |

### Проверка доступа (SQL)

```sql
SELECT DISTINCT p.code
FROM users u
JOIN user_roles ur ON ur.user_id = u.id
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE u.id = :user_id;
```

Этот запрос выполняется через `PermissionRepository.get_codes_for_user()`.

---

## Политика паролей

Управляется через переменные окружения (чтение при старте) и API `/admin/policy` (runtime).

| Параметр | По умолчанию | Описание |
|---|---|---|
| `PASSWORD_MIN_LENGTH` | 8 | Минимальная длина пароля |
| `PASSWORD_REQUIRE_UPPER` | false | Требовать заглавную букву |
| `PASSWORD_REQUIRE_SPECIAL` | false | Требовать спецсимвол |
| `PASSWORD_EXPIRE_DAYS` | 0 | Срок действия пароля (0 = бессрочно) |

Валидация всегда включает:
- Минимум N символов (настраивается)
- Хотя бы одна буква (A-Z, a-z)
- Хотя бы одна цифра (0-9)

При несоответствии возвращается HTTP 400 с описанием ошибки.

---

## Безопасность

### Opaque Session Token (вместо JWT)

| Критерий | Opaque Token | JWT |
|---|---|---|
| Мгновенный logout | ✅ удаляем запись из БД | ❌ нужен blocklist |
| Деактивация аккаунта | ✅ удаляем все токены | ❌ ждём истечения |
| Уязвимости | Нет (нет подписи) | alg:none, RS→HS confusion |
| Раскрытие данных | Нет (токен непрозрачен) | Payload читается без ключа |
| Стоимость | +1 DB запрос / request | Нет DB запроса |

### Механизмы

- **Bcrypt 4.x** (cost=12) — без passlib, прямой вызов `bcrypt.hashpw/checkpw`
- **Timing-safe login** — dummy hash для несуществующих пользователей (предотвращает timing attack)
- **OWASP Security Headers** — каждый ответ содержит:
  - `X-Frame-Options: SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security` (в production)
  - `Content-Security-Policy`
  - `Permissions-Policy`
- **Rate Limiting** (slowapi):
  - Глобально: 200 запросов/минута
  - `/auth/login`: 10/мин
  - `/auth/register`: 10/мин
  - `/auth/change-password`: 5/мин
  - `/auth/forgot-password`: 5/мин
- **Non-root Docker user** (appuser) — принцип наименьших привилегий
- **Internal Docker network** — БД недоступна снаружи в production
- **RequestID** — каждый запрос получает уникальный X-Request-ID для трассировки
- **Логирование** — пароли, токены, секреты NEVER попадают в логи (фильтр SENSITIVE полей)

### Коды ошибок API

| Код | Ситуация |
|---|---|
| 400 | Невалидные данные, несоответствие политике паролей |
| 401 | Отсутствует / истёк / неверный токен |
| 403 | Токен валиден, но нет нужного разрешения |
| 404 | Ресурс не найден |
| 409 | Конфликт (email занят, имя роли дублируется) |
| 422 | Ошибка валидации Pydantic |
| 429 | Rate limit exceeded |
| 500 | Внутренняя ошибка сервера |

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
# Обязательно замените SECRET_SALT!
```

| Переменная | По умолчанию | Обязательная | Описание |
|---|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/auth_db` | ✅ | Connection string к PostgreSQL |
| `SECRET_SALT` | `change-this-...` | ✅ | HMAC-ключ для токенов (64 hex, `secrets.token_hex(32)`) |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | | Время жизни access token (часы) |
| `PASSWORD_RESET_EXPIRE_MINUTES` | `60` | | Время жизни ссылки сброса пароля (минуты) |
| `SMTP_ENABLED` | `false` | | false = логировать в консоль |
| `SMTP_HOST` | `smtp.gmail.com` | | SMTP-сервер |
| `SMTP_PORT` | `587` | | Порт SMTP |
| `SMTP_USER` | | | SMTP-логин |
| `SMTP_PASSWORD` | | | SMTP-пароль |
| `SMTP_FROM` | `noreply@auth-manager.local` | | From-адрес писем |
| `FRONTEND_URL` | `http://localhost:3000` | ✅ | URL фронтенда (для ссылок в письмах) |
| `ADMIN_EMAIL` | `admin@example.com` | | Email для системных уведомлений |
| `PASSWORD_MIN_LENGTH` | `8` | | Минимальная длина пароля |
| `PASSWORD_REQUIRE_UPPER` | `false` | | Требовать заглавную |
| `PASSWORD_REQUIRE_SPECIAL` | `false` | | Требовать спецсимвол |
| `PASSWORD_EXPIRE_DAYS` | `0` | | Срок действия пароля (0 = без ограничения) |

Генерация `SECRET_SALT`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Деплой

### 1. Docker Compose (локальный или VPS)

```bash
# Production
docker compose -f docker-compose.prod.yml up -d
```

### 2. Railway (самый быстрый облачный деплой)

```bash
npm i -g @railway/cli && railway login
railway init auth-manager && railway link
railway add --plugin postgresql
railway vars set SECRET_SALT=$(python -c "import secrets; print(secrets.token_hex(32))")
railway up
```

Подробнее: [`deploy/railway/README.md`](deploy/railway/README.md)

### 3. Render.com (Blueprint)

1. Загрузите репозиторий на GitHub
2. Render → New → Blueprint → выберите репозиторий
3. Render автоматически создаст сервисы из `deploy/render/render.yaml`

Подробнее: [`deploy/render/README.md`](deploy/render/README.md)

### 4. VPS (Ubuntu 22.04 / Debian 12)

```bash
bash deploy/vps/deploy.sh your-server-ip
```

Или вручную:

```bash
ssh root@your-server-ip
curl -fsSL https://get.docker.com | sh
git clone <repo> /opt/auth-manager
cd /opt/auth-manager
cp .env.example .env
# Отредактировать .env
docker compose -f docker-compose.prod.yml up -d
# Настроить SSL через certbot
```

Подробнее: [`deploy/vps/README.md`](deploy/vps/README.md)

### Production checklist

- [ ] `SECRET_SALT` — сгенерирована случайная 64-символьная hex-строка
- [ ] `DATABASE_URL` — использует `sslmode=require` (если облако)
- [ ] `FRONTEND_URL` — установлен реальный домен
- [ ] `SMTP_ENABLED=true` — настроен SMTP для отправки писем
- [ ] SSL-сертификат (Let's Encrypt) — настроен через certbot
- [ ] Nginx `server_tokens off` — скрыта версия сервера
- [ ] Docker non-root user — используется (по умолчанию)
- [ ] Internal network — БД изолирована (в docker-compose.prod.yml)

---

## CI/CD

### CI (`.github/workflows/ci.yml`)

Срабатывает на каждый push/PR в `main` и `develop`:

1. **Backend Tests** — Python 3.12, SQLite in-memory, все тесты
2. **Frontend Tests** — Node 20, npm ci → tsc → vitest
3. **Docker Build Check** — сборка образов backend и frontend (без пуша)

### CD (`.github/workflows/deploy.yml`)

Срабатывает на push в `main` или по тегу `v*`:

1. **Build & Push** — Docker образы в GitHub Container Registry (ghcr.io)
2. **Deploy via SSH** — подключение к VPS, pull образов, `docker compose up -d`

Необходимые Secrets:
- `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`
- `GITHUB_TOKEN` (доступен автоматически)

---

## Тестирование

### Backend (89 тестов, SQLite in-memory, без PostgreSQL)

```bash
cd backend
TESTING=1 DATABASE_URL=sqlite:// python -m pytest tests/ -v
```

Тесты используют SQLite в памяти, не требуют запущенного PostgreSQL.

В режиме `TESTING=1` rate limiter отключается.

### Frontend (30 тестов, Vitest + jsdom + MSW)

```bash
cd frontend
npm test              # Разовый прогон
npm run test:watch    # Watch-режим
npm run test:coverage # С отчётом покрытия
```

TypeScript проверка:
```bash
npx tsc -b
```

### Линтинг

```bash
cd frontend
npm run lint          # Oxlint
```

---

## Тестовые пользователи

После выполнения `seed.py` создаются 23 пользователя:

### Основные (для демо)

| Email | Пароль | Роль |
|---|---|---|
| admin@example.com | Admin1234! | administrator |
| manager@example.com | Manager1234! | manager |
| user@example.com | User1234! | user |

### Дополнительные (для тестирования)

**10 менеджеров** (пароль `Test1234!`):
`manager1@example.com` … `manager10@example.com`

**10 пользователей** (пароль `Test1234!`):
`user1@example.com` … `user10@example.com`

---

## Журнал аудита

Каждое значимое действие записывается в таблицу `audit_log`:

| Поле | Описание | Пример |
|---|---|---|
| `id` | UUID записи | `550e8400-e29b-...` |
| `user_id` | UUID пользователя (кто сделал) | `550e8400-...` |
| `action` | Действие | `user.login`, `admin.user_created` |
| `entity_type` | Тип сущности | `user`, `role`, `permission` |
| `entity_id` | ID сущности | `550e8400-...` |
| `detail` | Доп. информация | `Admin admin@example.com created user test@example.com` |
| `ip_address` | IP-адрес | `192.168.1.1` |
| `created_at` | Временная метка | `2026-06-28T12:00:00Z` |

Доступен экспорт в CSV через `GET /admin/audit-log/export/csv`.

---

## База данных

### Схема (10 таблиц)

```
users → access_tokens (1:N)
users → user_roles (1:N) → roles (N:M)
roles → role_permissions (1:N) → permissions (N:M)
users → password_resets (1:N)
users → audit_log (1:N)
users → notifications (1:N)
users → user_totp (1:1)
```

### Миграции

```bash
cd backend
alembic upgrade a1b2c3d4e5f6    # Применить миграцию
alembic downgrade a1b2c3d4e5f6  # Откатить
```

`entrypoint.sh` автоматически выполняет `alembic upgrade a1b2c3d4e5f6` при старте.

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

Ответ:
```json
{
  "access_token": "a3f8c2d1...",
  "token_type": "bearer",
  "expires_at": "2026-06-29T12:00:00Z"
}
```

### Запрос с токеном

```bash
TOKEN="a3f8c2d1..."
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Создание пользователя (admin)

```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "New",
    "last_name": "User",
    "email": "new@example.com",
    "password": "Password123",
    "role_ids": ["<role-uuid>"]
  }'
```

### Назначение ролей

```bash
curl -X POST http://localhost:8000/admin/users/{USER_ID}/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_ids": ["<role-uuid>"]}'
```

---

## Troubleshooting

### "Множественные головы миграций"

Используйте явный revision target:
```bash
alembic upgrade a1b2c3d4e5f6
```

### Rate limit в тестах

```bash
TESTING=1 DATABASE_URL=sqlite:// python -m pytest
```

Переменная `TESTING=1` отключает rate limiter и использует уникальные ключи для каждого запроса.

### PostgreSQL не запускается

Проверьте, что порт 5432 не занят:
```bash
netstat -ano | findstr :5432
```
Или используйте Docker PostgreSQL:
```bash
docker run -d --name auth-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16-alpine
```

### Логи

```bash
docker compose logs -f app      # Логи backend
docker compose logs -f db       # Логи PostgreSQL
docker compose logs -f frontend # Логи Nginx
```

---

## Лицензия

MIT
