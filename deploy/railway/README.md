# Деплой на Railway.app

## Быстрый старт

```bash
npm i -g @railway/cli && railway login
railway init auth-manager && railway link
railway add --plugin postgresql
railway vars set SECRET_SALT=$(python -c "import secrets; print(secrets.token_hex(32))")
railway vars set SMTP_ENABLED=false ADMIN_EMAIL=admin@example.com
railway up
```

## Переменные окружения

| Переменная | Источник |
|---|---|
| DATABASE_URL | Автоматически от PostgreSQL plugin |
| SECRET_SALT | Сгенерируйте: python -c "import secrets; print(secrets.token_hex(32))" |
| FRONTEND_URL | https://your-app.up.railway.app |
| ADMIN_EMAIL | Email администратора |

## Команды

```bash
railway logs                          # Логи в реальном времени
railway shell                         # SSH в контейнер
railway run python -m app.seed.seed   # Загрузить тестовые данные
railway run alembic upgrade a1b2c3d4e5f6  # Применить миграции
```
