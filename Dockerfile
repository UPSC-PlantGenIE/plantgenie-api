FROM python:3.13-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.9.15 /uv /uvx /bin/

WORKDIR /app

# this is the main plantgenie backend app
COPY README.md .
COPY pyproject.toml /app/
COPY uv.lock .
COPY src ./src
COPY packages ./packages

# installs packages and deps
RUN uv sync --frozen

RUN useradd --no-create-home appuser

USER appuser

ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/app/src"
# obviates the need to do something like `source /app/.venv/bin/activate`
ENV PATH="/app/.venv/bin:$PATH"

CMD ["fastapi", "run", "/app/src/plantgenie_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
