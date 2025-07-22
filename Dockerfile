FROM python:3.13-bookworm

RUN useradd -m -u 1000 appuser

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    ncbi-blast+ && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /app
RUN chown -R appuser:appuser /app

USER appuser
ENV HOME=/home/appuser
ENV PATH="$HOME/.local/bin:$PATH"

ADD --chown=appuser:appuser https://astral.sh/uv/0.7.15/install.sh /home/appuser/uv-installer.sh
RUN sh /home/appuser/uv-installer.sh && rm /home/appuser/uv-installer.sh

# Create a virtualenv
WORKDIR /app
RUN uv venv /app/.venv
COPY --chown=appuser:appuser pyproject.toml .

RUN uv pip install -r pyproject.toml

COPY --chown=appuser:appuser . .

RUN uv pip install -e .

RUN uv sync --locked
CMD ["uv", "run", "fastapi", "dev", "/app/src/plantgenie_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
