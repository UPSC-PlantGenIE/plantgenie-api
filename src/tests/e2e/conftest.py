import os
import socket
import threading
import time
from pathlib import Path

import duckdb
import pytest
import uvicorn
from dotenv import dotenv_values

API_PORT = 8000
DATABASE_NAME = "plantgenie-backend.db"
REPO_ROOT = Path(__file__).resolve().parents[3]

FAKE_SWIFT = {
    "OS_AUTH_TYPE": "v3applicationcredential",
    "OS_AUTH_URL": "http://swift.invalid",
    "OS_IDENTITY_API_VERSION": "3",
    "OS_REGION_NAME": "e2e",
    "OS_INTERFACE": "public",
    "OS_APPLICATION_CREDENTIAL_ID": "e2e",
    "OS_APPLICATION_CREDENTIAL_SECRET": "e2e",
}


def port_is_free(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


@pytest.fixture(scope="session")
def live_server(tmp_path_factory: pytest.TempPathFactory):
    if not port_is_free(API_PORT):
        pytest.fail(
            f"port {API_PORT} is in use — stop the dev API before running e2e"
        )

    data_path = tmp_path_factory.mktemp("userdata")
    duckdb.connect(str(data_path / DATABASE_NAME)).close()

    local_env = dotenv_values(REPO_ROOT / ".env")
    os.environ.update(FAKE_SWIFT)
    os.environ["DATA_PATH"] = str(data_path)
    os.environ["DATABASE_NAME"] = DATABASE_NAME
    for key in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"):
        value = local_env.get(key)
        if value is None:
            pytest.fail(f"{key} missing from {REPO_ROOT / '.env'}")
        os.environ[key] = value

    from plantgenie_api.main import app

    server = uvicorn.Server(
        uvicorn.Config(
            app, host="127.0.0.1", port=API_PORT, log_level="warning"
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 30
    while not server.started:
        if time.monotonic() > deadline:
            pytest.fail("API did not start within 30s")
        time.sleep(0.05)

    yield f"http://127.0.0.1:{API_PORT}"

    server.should_exit = True
    thread.join(timeout=10)
