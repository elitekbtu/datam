FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=sqlite+aiosqlite:////data/app.db

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ ./

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data \
    && chown -R app:app /app /data

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic -c database/alembic.ini upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
