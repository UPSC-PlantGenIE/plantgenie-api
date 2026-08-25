import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def bootstrap_sqlite(path: Path) -> None:
    with sqlite3.connect(str(path)) as conn:
        conn.executescript(SCHEMA_PATH.read_text())
