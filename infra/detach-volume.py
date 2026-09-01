#!/usr/bin/env python3
import json
import os
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

    try:
        volume = request("GET", f"{api}/openstack-volumes/{volume_uuid}/", token)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print(f"volume {volume_uuid} no longer exists")
            return
        raise

    if not volume.get("instance"):
        print(f"volume {volume_uuid} is not attached")
        return

    print(f"detaching from {volume['instance_name']}")
    request("POST", f"{api}/openstack-volumes/{volume_uuid}/detach/", token, {})
    wait_for_runtime_state(api, token, volume_uuid, "available")
    print(f"detached volume {volume_uuid}")


if __name__ == "__main__":
    main()
