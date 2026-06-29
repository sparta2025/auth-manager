#!/bin/sh
set -e

echo "==> Waiting for database..."
# Already handled by Docker healthcheck, but double-check
python -c "
import time, sqlalchemy
engine = sqlalchemy.create_engine('${DATABASE_URL}')
for i in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text('SELECT 1'))
        print('Database ready.')
        break
    except Exception as e:
        print(f'Waiting... ({i+1}/30): {e}')
        time.sleep(2)
else:
    print('Database not available after 60s')
    exit(1)
"

echo "==> Running Alembic migration..."
# Используем явный revision ID — исключает ошибку multiple heads
alembic upgrade a1b2c3d4e5f6

echo "==> Seeding database..."
python -m app.seed.seed

echo "==> Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
