# 1) Збірка інтерфейсу (React + Vite)
FROM node:22-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# 2) Застосунок (FastAPI) + зібраний інтерфейс
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY --from=frontend /fe/dist ./frontend/dist
RUN useradd --create-home crm && chmod +x docker-entrypoint.sh && mkdir -p /app/media && chown -R crm /app
USER crm

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["web"]
