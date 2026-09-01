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


def wait_for_instance_uuid(api, token, floating_ip_uuid, wanted, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        fip = request("GET", f"{api}/openstack-floating-ips/{floating_ip_uuid}/", token)
        if fip.get("instance_uuid") == wanted:
            return fip
        time.sleep(5)
    raise SystemExit(
        f"floating ip {floating_ip_uuid} was not assigned to {wanted} within {timeout}s"
    )


def main():
    api = os.environ["WALDUR_API_URL"].rstrip("/") + "/api"
    token = os.environ["WALDUR_ACCESS_TOKEN"]
    instance_uuid = os.environ["INSTANCE_UUID"]
    floating_ip_uuid = os.environ["FLOATING_IP_UUID"]
    floating_ip_url = os.environ["FLOATING_IP_URL"]
    subnet_url = os.environ["SUBNET_URL"]

    fip = request("GET", f"{api}/openstack-floating-ips/{floating_ip_uuid}/", token)

    if fip.get("instance_uuid") == instance_uuid:
        print(f"floating ip {fip['address']} already assigned to {instance_uuid}")
        return

    try:
        request(
            "POST",
            f"{api}/openstack-instances/{instance_uuid}/update_floating_ips/",
            token,
            {"floating_ips": [{"subnet": subnet_url, "url": floating_ip_url}]},
        )
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"update_floating_ips failed: HTTP {error.code} {error.read().decode()[:500]}"
        )

    fip = wait_for_instance_uuid(api, token, floating_ip_uuid, instance_uuid)
    print(f"assigned floating ip {fip['address']} to {instance_uuid}")


if __name__ == "__main__":
    main()
