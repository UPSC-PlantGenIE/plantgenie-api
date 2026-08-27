#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request


def request(method, url, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as response:
        body = response.read()
    return json.loads(body) if body else None


def wait_for_runtime_state(api, token, volume_uuid, wanted, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        volume = request("GET", f"{api}/openstack-volumes/{volume_uuid}/", token)
        if volume["runtime_state"] == wanted:
            return volume
        time.sleep(5)
    raise SystemExit(f"volume {volume_uuid} did not reach {wanted} within {timeout}s")


def main():
    api = os.environ["WALDUR_API_URL"].rstrip("/") + "/api"
    token = os.environ["WALDUR_ACCESS_TOKEN"]
    volume_uuid = os.environ["VOLUME_UUID"]
    instance_url = os.environ["INSTANCE_URL"]

    volume = request("GET", f"{api}/openstack-volumes/{volume_uuid}/", token)

    if volume.get("instance") == instance_url:
        print(f"volume {volume_uuid} already attached to {volume['instance_name']}")
        return

    if volume.get("instance"):
        print(f"detaching from {volume['instance_name']}")
        request("POST", f"{api}/openstack-volumes/{volume_uuid}/detach/", token, {})
        wait_for_runtime_state(api, token, volume_uuid, "available")

    try:
        request(
            "POST",
            f"{api}/openstack-volumes/{volume_uuid}/attach/",
            token,
            {"instance": instance_url},
        )
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"attach failed: HTTP {error.code} {error.read().decode()[:500]}"
        )

    volume = wait_for_runtime_state(api, token, volume_uuid, "in-use")
    print(f"attached volume {volume_uuid} as {volume['device']}")


if __name__ == "__main__":
    main()
