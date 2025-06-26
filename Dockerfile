FROM python:3.13-bookworm

RUN useradd -m -u 1000 appuser

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    ncbi-blast+ && \
    rm -rf /var/lib/apt/lists/*

# Download and install `uv` as appuser
USER appuser
ENV HOME=/home/appuser
ENV PATH="$HOME/.local/bin:$PATH"
ENV UV_SYSTEM_PYTHON=0

ADD --chown=appuser:appuser https://astral.sh/uv/0.7.15/install.sh /home/appuser/uv-installer.sh
RUN sh /home/appuser/uv-installer.sh && rm /home/appuser/uv-installer.sh

# Create a virtualenv
ENV VIRTUAL_ENV=$HOME/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

WORKDIR /app
COPY --chown=appuser:appuser pyproject.toml .

RUN uv pip install -r pyproject.toml

COPY --chown=appuser:appuser . .

RUN uv pip install -e .

CMD ["uv", "run", "fastapi", "dev", "/app/src/plantgenie_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
