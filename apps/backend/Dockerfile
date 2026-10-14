FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /bin/uv

COPY pyproject.toml uv.lock ./
ARG INSTALL_LOCAL=false
ARG INSTALL_EVALUATION=false
RUN set -- --frozen --no-dev --no-install-project; \
    if [ "$INSTALL_LOCAL" = true ]; then set -- "$@" --extra local; fi; \
    if [ "$INSTALL_EVALUATION" = true ]; then set -- "$@" --extra evaluation; fi; \
    uv sync "$@"

COPY . .

FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=base /app /app

ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid "$APP_GID" appgroup \
    && useradd --create-home --uid "$APP_UID" --gid "$APP_GID" appuser \
    && mkdir -p /home/appuser/.cache \
    && chown -R appuser:appgroup /app /home/appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
