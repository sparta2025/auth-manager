# Деплой на VPS (Ubuntu 22.04)

## Требования
- VPS с минимум 1 GB RAM (рекомендуется 2 GB)
- Ubuntu 22.04 или Debian 12
- Домен (для SSL)

## Быстрый деплой

```bash
# На локальной машине:
bash deploy/vps/deploy.sh your-server-ip
```

## Ручной деплой

```bash
# 1. Подключиться к серверу
ssh root@your-server-ip

# 2. Установить Docker
curl -fsSL https://get.docker.com | sh

# 3. Скопировать проект
git clone https://github.com/your/repo.git /opt/auth-manager
cd /opt/auth-manager

# 4. Настроить окружение
cp .env.example .env
nano .env   # Заполните все переменные!

# 5. Запустить
docker compose -f docker-compose.prod.yml up -d

# 6. Настроить SSL (опционально)
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## Полезные команды

```bash
# Логи
docker compose -f docker-compose.prod.yml logs -f app

# Обновление
git pull
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Бэкап БД
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U postgres auth_db > backup_$(date +%Y%m%d).sql
```
