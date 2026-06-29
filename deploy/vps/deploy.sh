#!/bin/bash
# ============================================================
#  VPS деплой — Ubuntu 22.04 / Debian 12
#  Использование: bash deploy.sh your-server-ip
# ============================================================

set -euo pipefail

SERVER_IP=${1:-"your-server-ip"}
APP_DIR="/opt/auth-manager"
DOCKER_COMPOSE_VERSION="2.24.0"

echo "==> Подключение к серверу $SERVER_IP"

ssh root@$SERVER_IP << 'REMOTE'
set -euo pipefail

# Установка Docker
if ! command -v docker &>/dev/null; then
  echo "Установка Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker && systemctl start docker
fi

# Установка Docker Compose
if ! command -v docker compose &>/dev/null; then
  curl -SL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64"     -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
fi

# Создание директории
mkdir -p /opt/auth-manager
cd /opt/auth-manager

echo "Сервер готов к деплою."
REMOTE

echo "==> Копирование файлов..."
rsync -avz --exclude node_modules --exclude __pycache__ --exclude .git \
  . root@$SERVER_IP:$APP_DIR/

echo "==> Запуск приложения..."
ssh root@$SERVER_IP << REMOTE
  cd $APP_DIR
  cp .env.example .env
  echo "ВАЖНО: Отредактируйте .env на сервере!"
  docker compose -f docker-compose.prod.yml pull
  docker compose -f docker-compose.prod.yml up -d
  echo "==> Деплой завершён"
REMOTE
