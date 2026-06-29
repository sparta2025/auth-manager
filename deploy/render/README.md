# Деплой на Render.com

## Автоматически через Blueprint

1. Зайдите на https://render.com
2. New → Blueprint
3. Укажите ваш GitHub репозиторий
4. Render автоматически создаст сервисы из `render.yaml`

## Вручную

### Backend
1. New → Web Service → Docker
2. Root Directory: `backend`
3. Добавьте PostgreSQL database
4. Установите env vars из `.env.example`

### Frontend  
1. New → Web Service → Docker
2. Root Directory: `frontend`
3. Build arg: `VITE_API_URL=""`

## Важно для Render

- Free tier засыпает после 15 минут неактивности
- Для production используйте Starter ($7/мес)
- PostgreSQL free tier — 90 дней, потом $7/мес
