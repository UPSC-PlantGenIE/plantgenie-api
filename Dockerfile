# FROM ghcr.io/astral-sh/uv:python3.13-bookworm
FROM python:3.13-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates ncbi-blast+

# Download the latest installer
ADD https://astral.sh/uv/0.6.6/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"
ENV UV_SYSTEM_PYTHON=1

# ADD . /app
WORKDIR /app

COPY pyproject.toml .
RUN uv pip install -r pyproject.toml

COPY . .
RUN uv pip install -e .

# RUN uv sync --frozen

CMD ["uv", "run", "fastapi", "dev", "/app/src/plantgenie_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
