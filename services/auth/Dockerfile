FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# Workspace manifest + lock file (lock file may not exist yet — uv handles both cases)
COPY pyproject.toml uv.lock* ./

# Shared library sources (workspace members that auth depends on)
COPY libs/ ./libs/

# Auth service source
COPY services/auth/ ./services/auth/

# Install only auth's dependencies (no dev extras)
RUN uv sync --package auth --no-dev

WORKDIR /app/services/auth

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD sh -c 'uv run uvicorn src.api:app --host 0.0.0.0 --port ${APP_PORT}'