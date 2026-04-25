FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY src/ src/
RUN uv sync --frozen --no-dev

FROM python:3.12-slim

# HF Spaces requires a non-root user with uid 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH="/home/user/.local/bin:/app/.venv/bin:$PATH"

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder --chown=user:user /app/.venv /app/.venv

# Copy app source + frontend (HF builds without bind mounts)
COPY --chown=user:user src/ /app/src/
COPY --chown=user:user frontend/ /app/frontend/

ENV PYTHONPATH=/app/src PORT=7860

EXPOSE 7860

CMD ["sh", "-c", "uvicorn job_researcher.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
