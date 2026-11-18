FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_SCRIPTS_DIR=/app/db \
    FRONTEND_DIST_DIR=/app/frontend/dist \
    PORT=8000
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY db /app/db
COPY --from=frontend /frontend/dist /app/frontend/dist
RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "python -m app.db.migrate && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
