FROM python:3.13-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9.15 /uv /uvx /bin/

WORKDIR /app

# this is the root applications pyproject.toml and lockfile
COPY pyproject.toml /app/
COPY uv.lock /app/

# this is the main celery application code
COPY packages/task-queue/pyproject.toml /app/packages/task-queue/pyproject.toml
COPY packages/task-queue/src /app/packages/task-queue/src
# and its dependency on the shared library
COPY packages/shared/pyproject.toml /app/packages/shared/pyproject.toml
COPY packages/shared/src /app/packages/shared/src

# packages need a README.md or the install fails
RUN touch /app/packages/shared/README.md
RUN touch /app/packages/task-queue/README.md

WORKDIR /app/packages/task-queue
# installs only packages from the above package (task-queue)
# task-queue depends on the `shared` package, so its deps too
RUN uv sync --frozen

FROM python:3.13-bookworm

RUN useradd --no-create-home appuser

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ncbi-blast+ && \
    rm -rf /var/lib/apt/lists/*

USER appuser

ENV PYTHONUNBUFFERED=1

# Copy the virtual environment and source code from the builder stage
# /app/.venv contains the installed dependencies
COPY --from=builder /app/.venv /app/.venv
# /app/packages/task-queue/src contains the celery application code
COPY --from=builder /app/packages/task-queue/src/task_queue /app/src/task_queue
# We also need the source of the shared dependency package (shared)
COPY --from=builder /app/packages/shared/src /app/packages/shared/src

# task-queue is copied into the src directory, so needs to be added to path
ENV PYTHONPATH="/app/src"
# obviates the need to do something like `source /app/.venv/bin/activate`
ENV PATH="/app/.venv/bin:$PATH"

CMD ["/app/.venv/bin/celery", "-A", "task_queue.celery.app", "worker", "--loglevel=info"]
