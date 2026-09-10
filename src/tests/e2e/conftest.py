import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
API_URL = "http://localhost:8000"
SITE_URL = "http://localhost:5173"
SERVICES = ["neo4j", "rabbitmq", "redis", "api", "celery_worker"]


def responds(url: str) -> bool:
    try:
        return httpx.get(url, timeout=2).status_code < 500
    except httpx.TransportError:
        return False


def wait_until(condition: Callable[[], bool], message: str, seconds: int):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.5)
    pytest.fail(message)


@pytest.fixture(scope="session")
def live_server():
    subprocess.run(
        ["docker", "compose", "up", "-d", "--wait", *SERVICES],
        cwd=REPO_ROOT,
        check=True,
    )
    wait_until(
        lambda: responds(f"{API_URL}/api/"),
        f"API at {API_URL} did not become ready",
        seconds=120,
    )
    yield API_URL


@pytest.fixture(scope="session")
def site(live_server: str):
    if responds(SITE_URL):
        yield SITE_URL
        return

    vite = subprocess.Popen(
        ["yarn", "dev"],
        cwd=REPO_ROOT / "ui",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wait_until(
        lambda: responds(SITE_URL),
        f"vite at {SITE_URL} did not become ready",
        seconds=60,
    )

    yield SITE_URL

    vite.terminate()
    vite.wait(timeout=10)
