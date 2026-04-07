FROM python:3.13-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

WORKDIR /app

COPY README.md .
COPY pyproject.toml /app/
COPY uv.lock .
COPY src ./src
COPY packages/shared ./packages/shared
COPY packages/go-enrich ./packages/go-enrich
COPY packages/task-queue ./packages/task-queue

# lockfile cannot change, dev deps not installed
RUN uv sync --locked --no-group dev

RUN useradd --no-create-home appuser

USER appuser

ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/app/src"
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["fastapi", "run", "/app/src/plantgenie_api/main.py", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
