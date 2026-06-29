# Auth Manager — Frontend

React-приложение для управления аутентификацией, авторизацией и профилями пользователей.

**v3.0.0** | React 19 + TypeScript 6 + Vite 8 + Tailwind CSS 3 | [Root README](../README.md)

---

## Содержание

- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Компоненты](#компоненты)
- [Маршрутизация](#маршрутизация)
- [Управление состоянием](#управление-состоянием)
- [API-слой](#api-слой)
- [Хуки](#хуки)
- [Темы](#темы)
- [Разработка](#разработка)
- [Сборка и деплой](#сборка-и-деплой)
- [Тестирование](#тестирование)

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    App (BrowserRouter)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    AuthProvider                       │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │                   Routes                        │   │   │
│  │  │  ┌──────────────┐    ┌────────────────────┐    │   │   │
│  │  │  │  Public       │    │  ProtectedRoute    │    │   │   │
│  │  │  │  /login       │    │  ┌─────────────┐   │    │   │   │
│  │  │  │  /register    │    │  │  AppLayout   │   │    │   │   │
│  │  │  │  /forgot-...  │    │  │  ┌────────┐  │   │    │   │   │
│  │  │  │  /reset-...   │    │  │  │ Sidebar │  │   │    │   │   │
│  │  │  └──────────────┘    │  │  │ ├─User   │  │   │    │   │   │
│  │  │                       │  │  │ ├─Nav    │  │   │    │   │   │
│  │  │                       │  │  │ └────────┘  │   │    │   │   │
│  │  │                       │  │  │  <Outlet/>  │   │    │   │   │
│  │  │                       │  │  └─────────────┘   │    │   │   │
│  │  │                       │  └────────────────────┘    │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Toaster (react-hot-toast)                       │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘

API Layer:
┌─────────────────────────────────────────────────────────────┐
│  apiClient (Axios)                                          │
│  ├─ Interceptor: inject Bearer token from localStorage      │
│  ├─ Interceptor: 401 → clear token → redirect /login        │
│  ├─ getErrorMessage() → user-friendly message               │
│  │                                                           │
│  ├─ authApi      /auth/*                                   │
│  ├─ adminApi     /admin/*                                   │
│  └─ resourcesApi /reports, /documents, /settings            │
└─────────────────────────────────────────────────────────────┘
```

### Технологии

| Технология | Версия | Назначение |
|---|---|---|
| React | 19.2 | UI-библиотека |
| TypeScript | 6.0 | Типизация |
| Vite | 8.1 | Сборщик / dev-сервер |
| Tailwind CSS | 3.4 | CSS-фреймворк |
| React Router | 7.18 | Маршрутизация |
| Axios | 1.18 | HTTP-клиент |
| Lucide React | 1.21 | Иконки |
| react-hot-toast | 2.6 | Уведомления |
| Vitest | 4.1 | Тест-раннер |
| Testing Library | 10/16/14 | Тестирование React |
| MSW | 2.14 | Мок-сервер для тестов |

---

## Структура проекта

```
frontend/
├── src/
│   ├── api/                        HTTP-клиент
│   │   ├── client.ts               Axios instance, interceptors, error handler
│   │   ├── auth.ts                 authApi — login, register, me, sessions, 2FA
│   │   ├── admin.ts                adminApi — users, roles, permissions, notifications, audit
│   │   └── resources.ts            reportsApi, documentsApi, settingsApi
│   │
│   ├── components/
│   │   ├── layout/                 Каркас приложения
│   │   │   ├── AppLayout.tsx       Sidebar + Header + User block + Navigation + ThemeToggle
│   │   │   └── ProtectedRoute.tsx  Guard — редирект на /login если не аутентифицирован
│   │   └── ui/                     UI-kit (переиспользуемые компоненты)
│   │       ├── index.tsx           Spinner, PageLoader, Alert, Modal, ConfirmModal,
│   │       │                       StatusBadge, Table, EmptyState, DangerZone
│   │       ├── PasswordStrength.tsx Индикатор надёжности пароля с чеклистом
│   │       └── ThemeToggle.tsx     Переключатель темы (светлая/тёмная/системная)
│   │
│   ├── hooks/                      Пользовательские хуки
│   │   ├── useTokenRefresh.ts      Автоматическое продление токена за 5 мин до истечения
│   │   ├── useTheme.ts             Управление темой (localStorage + matchMedia)
│   │   └── useNotificationSocket.ts WebSocket для real-time уведомлений
│   │
│   ├── pages/
│   │   ├── auth/                   Публичные и пользовательские страницы
│   │   │   ├── LoginPage.tsx       Вход (с подсказкой тестовых аккаунтов)
│   │   │   ├── RegisterPage.tsx    Регистрация (с PasswordStrength)
│   │   │   ├── ForgotPasswordPage.tsx Восстановление пароля
│   │   │   ├── ResetPasswordPage.tsx  Сброс пароля по токену
│   │   │   ├── DashboardPage.tsx   Обзор (роли, permissions, статистика)
│   │   │   ├── ProfilePage.tsx     Редактирование профиля + аватар
│   │   │   ├── SessionsPage.tsx    Управление сессиями
│   │   │   └── TwoFactorPage.tsx   Настройка 2FA/TOTP
│   │   ├── admin/                  Административные страницы (только administrator)
│   │   │   ├── UsersPage.tsx       CRUD пользователей + модалка создания
│   │   │   ├── RolesPage.tsx       CRUD ролей
│   │   │   ├── PermissionsPage.tsx CRUD разрешений
│   │   │   ├── NotificationsPage.tsx  Уведомления
│   │   │   ├── AuditLogPage.tsx    Журнал аудита
│   │   │   └── PolicyPage.tsx      Управление политикой паролей
│   │   └── resources/              Ресурсы (Mock API)
│   │       ├── ReportsPage.tsx     Отчёты (CRUD)
│   │       ├── DocumentsPage.tsx   Документы (CRUD)
│   │       └── SettingsPage.tsx    Настройки (read/update)
│   │
│   ├── store/
│   │   └── auth.tsx                AuthContext + AuthProvider
│   │                               state: user, roles[], permissions[], isAuthenticated,
│   │                               isLoading, isAdmin
│   │                               actions: login(), logout(), refreshMe()
│   │
│   ├── types/
│   │   └── index.ts                TypeScript типы: User, Role, Permission, TokenResponse,
│   │                               SessionInfo, Report, Document, Settings, Notification, AuditEntry
│   │
│   ├── test/                       Тесты
│   │   ├── setup.ts                Настройка MSW + Testing Library (jest-dom)
│   │   ├── mocks/
│   │   │   ├── server.ts           MSW server (setupServer)
│   │   │   └── handlers.ts         MSW handlers (все API-эндпоинты)
│   │   ├── unit/
│   │   │   ├── tokenRefresh.test.ts  Тест автообновления токена
│   │   │   └── security.test.ts      Тест механизмов безопасности
│   │   └── integration/
│   │       ├── auth.test.tsx         Тесты страниц аутентификации
│   │       ├── rbac.test.tsx         Тесты RBAC-интерфейса
│   │       └── notifications.test.tsx Тесты уведомлений
│   │
│   ├── App.tsx                    Корневой компонент (Router + Provider + Routes)
│   ├── main.tsx                   Entry point (createRoot + StrictMode)
│   └── index.css                  Tailwind directives + кастомные классы
│
├── public/
│   └── favicon.svg
│
├── dist/                          Production-сборка
├── Dockerfile                     Multi-stage (node:20 → nginx:1.27-alpine)
├── nginx.conf                     Rate limiting, security headers, API proxy, SPA
├── vite.config.ts                 Vite + React + proxy /auth /admin и др. на backend
├── vitest.config.ts               Vitest + jsdom + setupFiles
├── tailwind.config.js             Tailwind + brand colors + dark mode (class)
├── postcss.config.js              PostCSS + Tailwind + Autoprefixer
├── tsconfig.json                  Ссылки на tsconfig.app.json + tsconfig.node.json
├── tsconfig.app.json              Compiler options для src/
├── tsconfig.node.json             Compiler options для конфигов
├── package.json                   Зависимости и скрипты
├── index.html                     HTML-шаблон
├── .env                           VITE_API_URL=http://localhost:8000
├── .env.production                VITE_API_URL=http://localhost:8000
└── .gitignore
```

---

## Компоненты

### UI-kit (`src/components/ui/index.tsx`)

| Компонент | Props | Описание |
|---|---|---|
| `Spinner` | `className` | Анимированный Loader2 (lucide) |
| `PageLoader` | — | Центрированный спинер на всю страницу |
| `Alert` | `type`, `message` | Цветной alert: error/success/info/warning |
| `StatusBadge` | `active` | Зелёный/красный бейдж "Активен/Деактивирован" |
| `Modal` | `open`, `onClose`, `title`, `size` | Модальное окно с backdrop и заголовком |
| `ConfirmModal` | `open`, `onConfirm`, `title`, `message`, `danger`, `loading` | Модалка подтверждения с кнопками |
| `Table` | `headers`, `children` | Таблица с заголовками и разделителями |
| `EmptyState` | `icon`, `title`, `description`, `action` | Пустое состояние с иконкой |
| `DangerZone` | `title`, `children` | Красный блок для опасных действий |

### PasswordStrength (`src/components/ui/PasswordStrength.tsx`)

Визуальный индикатор надёжности пароля:
- 4-уровневая шкала (серый → красный → жёлтый → синий → зелёный)
- Динамический чеклист (длина, буква, цифра, заглавная, спецсимвол)
- Учитывает текущую политику из Settings

### ThemeToggle (`src/components/ui/ThemeToggle.tsx`)

Три режима: светлая / тёмная / системная. Использует `useTheme()` хук.

### AppLayout (`src/components/layout/AppLayout.tsx`)

Основной каркас приложения:

```
┌────────────────────────────────────────────────────┐
│  Sidebar (w-64)                   │  Main (flex-1) │
│  ┌────────────────────────────┐   │  ┌──────────┐  │
│  │  Logo "Auth Manager v3.0"  │   │  │          │  │
│  │  ───────────────────────── │   │  │  <Outlet/>│  │
│  │  User block                │   │  │          │  │
│  │  ┌────────────────────┐    │   │  │          │  │
│  │  │ Avatar + Name      │    │   │  └──────────┘  │
│  │  │ Email              │    │   │                 │
│  │  │ [ThemeToggle][Logout]│   │   │                 │
│  │  └────────────────────┘    │   │                 │
│  │  ───────────────────────── │   │                 │
│  │  ГЛАВНАЯ                  │   │                 │
│  │  ├─ Обзор                 │   │                 │
│  │  ├─ Мой профиль           │   │                 │
│  │  ├─ Мои сессии            │   │                 │
│  │  └─ 2FA защита            │   │                 │
│  │                           │   │                 │
│  │  АДМИНИСТРИРОВАНИЕ (admin)│   │                 │
│  │  ├─ Пользователи          │   │                 │
│  │  ├─ Роли                  │   │                 │
│  │  ├─ Разрешения            │   │                 │
│  │  ├─ Уведомления [N]       │   │                 │
│  │  ├─ Журнал аудита         │   │                 │
│  │  └─ Политика паролей      │   │                 │
│  │                           │   │                 │
│  │  РЕСУРСЫ                  │   │                 │
│  │  ├─ Отчёты                │   │                 │
│  │  ├─ Документы             │   │                 │
│  │  └─ Настройки             │   │                 │
│  └────────────────────────────┘   └──────────────────┘
└────────────────────────────────────────────────────┘
```

Особенности:
- Секция "Администрирование" видна только `isAdmin`
- Бейдж непрочитанных уведомлений (красный, с числом)
- User block в верхней части сайдбара (под логотипом)
- WebSocket подключение для real-time уведомлений
- Автообновление токена через `useTokenRefresh`

---

## Маршрутизация

```typescript
<Routes>
  {/* Публичные страницы (без аутентификации) */}
  <Route path="/login"           element={<LoginPage />} />
  <Route path="/register"        element={<RegisterPage />} />
  <Route path="/forgot-password" element={<ForgotPasswordPage />} />
  <Route path="/reset-password"  element={<ResetPasswordPage />} />

  {/* Защищённые страницы (требуется Bearer token) */}
  <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
    <Route index               element={<Navigate to="/dashboard" />} />
    <Route path="/dashboard"   element={<DashboardPage />} />
    <Route path="/profile"     element={<ProfilePage />} />
    <Route path="/sessions"    element={<SessionsPage />} />
    <Route path="/2fa"         element={<TwoFactorPage />} />

    <Route path="/admin/users"         element={<UsersPage />} />
    <Route path="/admin/roles"         element={<RolesPage />} />
    <Route path="/admin/permissions"   element={<PermissionsPage />} />
    <Route path="/admin/notifications" element={<NotificationsPage />} />
    <Route path="/admin/audit-log"     element={<AuditLogPage />} />
    <Route path="/admin/policy"        element={<PolicyPage />} />

    <Route path="/reports"   element={<ReportsPage />} />
    <Route path="/documents" element={<DocumentsPage />} />
    <Route path="/settings"  element={<SettingsPage />} />
  </Route>

  <Route path="*" element={<Navigate to="/dashboard" replace />} />
</Routes>
```

`ProtectedRoute` проверяет `isAuthenticated` и `isLoading` из AuthContext. При загрузке показывает `PageLoader`, при отсутствии аутентификации редиректит на `/login`.

---

## Управление состоянием

### AuthContext (`src/store/auth.tsx`)

Централизованное состояние аутентификации через React Context.

```typescript
interface AuthState {
  user:            User | null;
  roles:           Role[];
  permissions:     string[];
  isAuthenticated: boolean;
  isLoading:       boolean;
  isAdmin:         boolean;
}

interface AuthActions {
  login(email: string, password: string): Promise<void>;
  logout(): Promise<void>;
  refreshMe(): Promise<void>;
}
```

**Поток логина:**

```
LoginPage
  → useAuth().login(email, password)
    → POST /auth/login → TokenResponse
    → localStorage.setItem("access_token", token)
    → GET /auth/me → User
    → GET /auth/me/roles → Role[]
    → GET /auth/me/permissions → string[]
    → setState({ user, roles, permissions, isAuthenticated: true })
    → navigate("/dashboard")
```

**Поток logout:**

```
AppLayout → handleLogout()
  → POST /auth/logout
  → localStorage.removeItem("access_token")
  → setState({ user: null, isAuthenticated: false })
  → navigate("/login")
```

**Поток восстановления сессии:**

```
App mount
  → localStorage.getItem("access_token")
  → если токен есть → refreshMe()
    → GET /auth/me → ...
    → GET /auth/me/roles → ...
    → GET /auth/me/permissions → ...
  → setState({ isLoading: false })
```

---

## API-слой

### Axios Client (`src/api/client.ts`)

```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: добавляет Bearer token из localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: при 401 → очистить токен → редирект на /login
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !publicPath) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

### API-модули

| Модуль | Методы |
|---|---|
| `authApi` | `login`, `register`, `logout`, `me`, `myRoles`, `myPermissions`, `updateProfile`, `changePassword`, `forgotPassword`, `resetPassword`, `deleteAccount`, `mySessions`, `revokeSession`, `publicRoles` |
| `adminApi` | `getUsers`, `createUser`, `getUser`, `updateUser`, `activateUser`, `deactivateUser`, `deleteUser`, `setPassword`, `logoutAll`, `getUserRoles`, `assignRoles`, `getRoles`, `createRole`, `updateRole`, `deleteRole`, `getRolePermissions`, `assignPermissionsToRole`, `getPermissions`, `createPermission`, `updatePermission`, `deletePermission`, `getNotifications`, `getUnreadCount`, `markRead`, `markAllRead`, `getAuditLog` |
| `reportsApi` | `getAll`, `create`, `update`, `delete` |
| `documentsApi` | `getAll`, `create`, `update`, `delete` |
| `settingsApi` | `get`, `update` |

### Обработка ошибок

```typescript
function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail))
      return data.detail.map((x) => x.msg).join("; ");
    return error.message;
  }
  return "Неизвестная ошибка";
}
```

---

## Хуки

### useTokenRefresh

Автоматически продлевает токен за 5 минут до истечения.

```typescript
function useTokenRefresh() {
  // setInterval каждые 60 секунд проверяет expires_at
  // если expires_at - now < 5 минут → POST /auth/refresh
  // старый токен инвалидируется, новый сохраняется в localStorage
}
```

Безопасность: не вызывает refresh при отсутствии токена или на страницах логина/регистрации.

### useTheme

Управление темой (светлая/тёмная/системная).

```typescript
function useTheme(): {
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
  resolved: "light" | "dark"; // фактическая тема (для system)
}
```

Хранит выбор в `localStorage("theme")`.
Для `system` подписывается на `matchMedia("prefers-color-scheme: dark")`.
Добавляет/убирает класс `dark` на `document.documentElement`.

### useNotificationSocket

WebSocket для real-time уведомлений администратора.

```typescript
function useNotificationSocket(
  enabled: boolean,
  onNotification: (notification: NotificationPayload) => void
)
```

- Подключается только когда `enabled === true` и токен есть в `localStorage`
- Вызывается из `AppLayout.tsx` с условием `isAdmin && isAuthenticated && !!user`
- URL: `ws://host/ws/notifications?token={token}`
- Авто-переподключение с exponential backoff: 2s → 4s → 8s → ... → 30s max

---

## Темы

Поддерживаются три режима:

1. **Светлая** (light) — по умолчанию
2. **Тёмная** (dark) — класс `dark` на `<html>`
3. **Системная** (system) — подписывается на `prefers-color-scheme`

Настройка темы:
- Переключатель в сайдбаре (рядом с кнопкой logout)
- Сохраняется в `localStorage`
- Применяется через Tailwind `darkMode: "class"`

CSS-переменные:
```css
/* Светлая тема (по умолчанию) */
body { @apply bg-gray-50 text-gray-900; }

/* Тёмная тема */
html.dark body { @apply bg-gray-950 text-gray-100; }
```

---

## Разработка

### Требования

- Node.js 20+
- npm 10+

### Установка и запуск

```bash
cd frontend
npm install

# Dev-сервер с прокси на backend (localhost:8000)
npm run dev
# → http://localhost:5173

# TypeScript проверка
npx tsc -b

# Production-сборка
npm run build
```

Vite проксирует запросы на backend:

| Путь | Target |
|---|---|
| `/auth/*` | `http://localhost:8000` |
| `/admin/*` | `http://localhost:8000` |
| `/reports/*` | `http://localhost:8000` |
| `/documents/*` | `http://localhost:8000` |
| `/settings/*` | `http://localhost:8000` |
| `/health` | `http://localhost:8000` |

### Скрипты

```bash
npm run dev              # Dev-сервер (Vite, порт 5173)
npm run build            # TypeScript + Vite build
npm run preview          # Preview production-сборки
npm run test             # Vitest (разовый прогон)
npm run test:watch       # Vitest (watch)
npm run test:coverage    # Vitest с coverage (v8)
npm run lint             # Oxlint
```

### Добавление новой страницы

1. Создать компонент в `src/pages/{section}/`
2. Добавить импорт в `src/App.tsx`
3. Добавить `<Route>` с нужным path
4. Добавить навигацию в `AppLayout.tsx` (при необходимости)
5. Если нужен новый API-метод → добавить в `src/api/{module}.ts`
6. Если нужен новый тип → добавить в `src/types/index.ts`
7. Написать тесты в `src/test/`

---

## Сборка и деплой

### Docker

```bash
# Сборка
docker build -t auth-manager-frontend .

# Запуск (с прокси на backend)
docker run -d -p 3000:80 auth-manager-frontend
```

### Docker Compose (из корня проекта)

```bash
docker compose up --build
```

Frontend доступен на `http://localhost:3000`.

### Nginx config

`nginx.conf` выполняет:

1. **Rate limiting** — 30 запросов/минуту на `/auth/` и `/admin/`
2. **Security headers** — X-Frame-Options, CSP, HSTS, X-Content-Type-Options
3. **API proxy** — `/auth/`, `/admin/`, `/reports`, `/documents`, `/settings`, `/avatars/`, `/health`, `/docs`, `/ws/`
4. **SPA fallback** — `try_files $uri $uri/ /index.html`
5. **Static cache** — .js, .css, .png и т.д. с `Cache-Control: public, immutable`
6. **Gzip** — сжатие текстовых ресурсов
7. **Server tokens off** — скрытие версии Nginx

---

## Тестирование

**30 тестов** (unit + integration) с Vitest + Testing Library + MSW.

### Запуск

```bash
npm test                       # Разовый прогон
npm run test:watch             # Watch-режим
npm run test:coverage          # С coverage (text + html)
npm run test:ui                # Vitest UI
```

### Структура

```
src/test/
├── setup.ts                   # setupFiles: MSW server lifecycle, jest-dom matchers
├── mocks/
│   ├── server.ts              # setupServer для MSW (listen, resetHandlers, close)
│   └── handlers.ts            # Полные MSW handlers для всех API-эндпоинтов
├── unit/
│   ├── tokenRefresh.test.ts   # Проверка автообновления токена
│   └── security.test.ts       # Проверка безопасности (401 interceptor, etc.)
└── integration/
    ├── auth.test.tsx          # Login, Register, Forgot/Reset password flow
    ├── rbac.test.tsx          # RBAC-интерфейс, разграничение доступа
    └── notifications.test.tsx # Уведомления, WebSocket
```

### Технологии тестирования

| Инструмент | Назначение |
|---|---|
| Vitest 4 | Тест-раннер |
| @testing-library/react | Рендер и взаимодействие с компонентами |
| @testing-library/user-event | Симуляция пользовательских действий |
| @testing-library/jest-dom | Кастомные matchers (toBeInTheDocument, toHaveTextContent...) |
| jsdom | DOM-окружение |
| MSW (Mock Service Worker) | Перехват HTTP-запросов |

### Vite proxy (dev)

```typescript
// vite.config.ts
server: {
  port: 5173,
  proxy: {
    "/auth":      { target: "http://localhost:8000", changeOrigin: true },
    "/admin":     { target: "http://localhost:8000", changeOrigin: true },
    "/reports":   { target: "http://localhost:8000", changeOrigin: true },
    "/documents": { target: "http://localhost:8000", changeOrigin: true },
    "/settings":  { target: "http://localhost:8000", changeOrigin: true },
    "/health":    { target: "http://localhost:8000", changeOrigin: true },
  },
}
```
