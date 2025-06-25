import os

from pathlib import Path

DUCKDB_DATABASE_BASENAME = "upsc-plantgenie.db"

ENV_DATA_PATH = os.environ.get("DATA_PATH", __file__)
DUCKDB_DATABASE_PATH = (
    Path(ENV_DATA_PATH) / DUCKDB_DATABASE_BASENAME
    if ENV_DATA_PATH
    else Path(__file__).parent / DUCKDB_DATABASE_BASENAME
)

def main() -> None:
    print("Hello from plantgenie-api!")
