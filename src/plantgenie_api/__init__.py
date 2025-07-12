import os

from pathlib import Path

DUCKDB_DATABASE_BASENAME = "upsc-plantgenie.db"

ENV_DATA_PATH = os.environ.get("DATA_PATH", __file__)

BACKEND_DATA_PATH = (
    Path(ENV_DATA_PATH)
    if ENV_DATA_PATH
    else Path(__file__).parent.parent / "example_data"
)

DUCKDB_DATABASE_PATH = (
    Path(ENV_DATA_PATH) / DUCKDB_DATABASE_BASENAME
    if ENV_DATA_PATH
    else Path(__file__).parent / DUCKDB_DATABASE_BASENAME
)

def main() -> None:
    print("Hello from plantgenie-api!")
