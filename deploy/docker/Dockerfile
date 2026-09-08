FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock \
    && groupadd --gid 10001 medical-api \
    && useradd --uid 10001 --gid 10001 --home-dir /nonexistent --no-create-home --shell /usr/sbin/nologin medical-api \
    && mkdir -p /data /app/backups \
    && chown -R medical-api:medical-api /data /app/backups

COPY . /app
RUN find /app -type d -name '__pycache__' -prune -exec rm -rf {} + \
    && rm -rf /app/.pytest_cache \
    && chown -R root:root /app \
    && chown medical-api:medical-api /app/backups

USER medical-api
ENV MEDICAL_API_DATABASE_URL=sqlite:////data/medical.db \
    MEDICAL_API_BIND_HOST=0.0.0.0 \
    MEDICAL_API_PORT=8000 \
    MEDICAL_API_WORKERS=1

EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/livez', timeout=3).read()" || exit 1

ENTRYPOINT ["/app/deploy/docker/entrypoint.sh"]
