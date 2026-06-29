# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

LABEL stage="builder"
WORKDIR /app

# Копируем только package.json для кэширования слоёв
COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .

# VITE_API_URL пустой — Nginx проксирует /auth/, /admin/ итд на backend
# Для облака передайте: --build-arg VITE_API_URL=https://api.your-domain.com
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="auth-manager"
LABEL version="3.0.0"
LABEL description="Auth Manager Frontend — React + Vite + Nginx"

# Удаляем дефолтный конфиг
RUN rm -f /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist  /usr/share/nginx/html
COPY nginx.conf                /etc/nginx/conf.d/default.conf

# Non-root: меняем владельца и порт Nginx (опционально для cloud)
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:80/health.txt 2>/dev/null || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
