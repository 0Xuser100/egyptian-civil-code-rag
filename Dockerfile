# syntax=docker/dockerfile:1

# ============================================================
# Stage 1: Build
# ============================================================
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# System dependencies required to build Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install the same uv version used by local development
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /uvx /bin/

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml uv.lock ./

# Create a production virtual environment
RUN uv sync \
    --locked \
    --no-dev \
    --no-install-project


# ============================================================
# Stage 2: Runtime
# ============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
     PYTHONPATH="/app/src"\
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Runtime system libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the prepared virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY src ./src

# Copy RAG runtime artifacts
COPY data/processed ./data/processed

# Create a dedicated non-root user
RUN useradd \
        --create-home \
        --uid 10001 \
        --shell /usr/sbin/nologin \
        appuser \
    && chown -R appuser:appuser /app

USER appuser

# FastAPI port
EXPOSE 8000

# Container health check
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=120s \
    --retries=3 \
    CMD curl --fail http://127.0.0.1:8000/health || exit 1


# Start FastAPI
CMD ["uvicorn", "rag.api:app", "--host", "0.0.0.0", "--port", "8000"]