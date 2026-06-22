import os
import time
from pathlib import Path
from uuid import uuid4

from jinja2 import Template
from shared.services.openstack import ComputeClient, SwiftClient

BUCKET = os.environ["KB_BUILD_BUCKET"]
IMAGE_ID = os.environ["KB_VM_IMAGE_ID"]
FLAVOR_ID = os.environ["KB_VM_FLAVOR_ID"]
NETWORK_ID = os.environ["KB_VM_NETWORK_ID"]
KEY_NAME = os.environ["KB_VM_KEY_NAME"]
KB_IMAGE_TAG = os.environ["KB_IMAGE_TAG"]
GHCR_USER = os.environ["GHCR_USERNAME"]
GHCR_PAT = os.environ["GHCR_PAT"]

CLOUD_INIT = Path(__file__).parent / "cloud-init.yaml.j2"
TIMEOUT_S = 60 * 60
POLL_INTERVAL_S = 30


def render_cloud_init(run_id: str) -> str:
    return Template(CLOUD_INIT.read_text()).render(
        run_id=run_id,
        bucket=BUCKET,
        kb_image_tag=KB_IMAGE_TAG,
        ghcr_user=GHCR_USER,
        ghcr_pat=GHCR_PAT,
        os_auth_url=os.environ["OS_AUTH_URL"],
        os_auth_type=os.environ["OS_AUTH_TYPE"],
        os_app_cred_id=os.environ["OS_APPLICATION_CREDENTIAL_ID"],
        os_app_cred_secret=os.environ["OS_APPLICATION_CREDENTIAL_SECRET"],
    )


def poll_for_marker(swift: SwiftClient, run_id: str) -> str:
    deadline = time.monotonic() + TIMEOUT_S
    success = f"builds/{run_id}/SUCCESS-{run_id}"
    failed = f"builds/{run_id}/FAILED-{run_id}"
    while time.monotonic() < deadline:
        if swift.head_object(BUCKET, success):
            return "success"
        if swift.head_object(BUCKET, failed):
            return "failed"
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"no marker for {run_id} after {TIMEOUT_S}s")


def launch() -> str:
    run_id = uuid4().hex
    print(f"run_id={run_id}")

    compute = ComputeClient()
    swift = SwiftClient()

    server = compute.create_server(
        name=f"kb-build-{run_id}",
        image_id=IMAGE_ID,
        flavor_id=FLAVOR_ID,
        network_id=NETWORK_ID,
        key_name=KEY_NAME,
        user_data=render_cloud_init(run_id),
    )
    print(f"server={server.id}")

    try:
        result = poll_for_marker(swift, run_id)
        print(f"result={result}")
        return result
    finally:
        compute.delete_server(server.id)
        print(f"deleted server={server.id}")


if __name__ == "__main__":
    launch()
