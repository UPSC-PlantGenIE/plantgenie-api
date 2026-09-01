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


def wait_for_release(api, token, floating_ip_uuid, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        fip = request("GET", f"{api}/openstack-floating-ips/{floating_ip_uuid}/", token)
        if not fip.get("instance_uuid"):
            return fip
        time.sleep(5)
    raise SystemExit(
        f"floating ip {floating_ip_uuid} was not released within {timeout}s"
    )


def main():
    api = os.environ["WALDUR_API_URL"].rstrip("/") + "/api"
    token = os.environ["WALDUR_ACCESS_TOKEN"]
    instance_uuid = os.environ["INSTANCE_UUID"]
    floating_ip_uuid = os.environ["FLOATING_IP_UUID"]

    try:
        fip = request(
            "GET", f"{api}/openstack-floating-ips/{floating_ip_uuid}/", token
        )
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print(f"floating ip {floating_ip_uuid} no longer exists")
            return
        raise

    if fip.get("instance_uuid") != instance_uuid:
        print(f"floating ip {floating_ip_uuid} is not assigned to {instance_uuid}")
        return

    print(f"releasing floating ip {fip['address']} from {instance_uuid}")
    request(
        "POST",
        f"{api}/openstack-instances/{instance_uuid}/update_floating_ips/",
        token,
        {"floating_ips": []},
    )
    wait_for_release(api, token, floating_ip_uuid)
    print(f"released floating ip {fip['address']}")


if __name__ == "__main__":
    main()
