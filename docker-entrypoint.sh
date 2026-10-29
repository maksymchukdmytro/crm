#!/bin/sh
set -e

# Чекаємо, поки PostgreSQL прийме з'єднання
python - <<'EOF'
import time, sys
from sqlalchemy import create_engine, text
from app.config import config
for i in range(60):
    try:
        with create_engine(config.DATABASE_URL).connect() as c:
            c.execute(text("select 1"))
        sys.exit(0)
    except Exception as e:
        print("Очікування бази даних...", e.__class__.__name__)
        time.sleep(2)
sys.exit("База даних недоступна")
EOF

case "$SECRET_KEY" in
  ""|change-me*|dev-secret*)
    if [ "$1" = "web" ]; then
      echo "ПОМИЛКА: задайте SECRET_KEY у файлі .env (openssl rand -hex 32)"; exit 1
    fi ;;
esac

case "$1" in
  web)
    alembic upgrade head
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_WORKERS:-2}" \
      --proxy-headers --forwarded-allow-ips="*"
    ;;
  worker)
    exec python worker.py
    ;;
  *)
    exec "$@"
    ;;
esac
