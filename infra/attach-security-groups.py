#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
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


def find_port(api, token, tenant_uuid, internal_ip):
    query = urllib.parse.urlencode({"tenant_uuid": tenant_uuid})
    for port in request("GET", f"{api}/openstack-ports/?{query}", token):
        for fixed_ip in port.get("fixed_ips") or []:
            if fixed_ip.get("ip_address") == internal_ip:
                return port["uuid"]
    raise SystemExit(f"no port found with fixed ip {internal_ip}")


def main():
    api = os.environ["WALDUR_API_URL"].rstrip("/") + "/api"
    token = os.environ["WALDUR_ACCESS_TOKEN"]
    security_groups = json.loads(os.environ["SECURITY_GROUPS"])

    port_uuid = find_port(
        api, token, os.environ["TENANT_UUID"], os.environ["INTERNAL_IP"]
    )

    try:
        request(
            "POST",
            f"{api}/openstack-ports/{port_uuid}/update_security_groups/",
            token,
            {"security_groups": security_groups},
        )
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"update_security_groups failed: HTTP {error.code} {error.read().decode()[:500]}"
        )

    print(f"attached {len(security_groups)} security groups to port {port_uuid}")


if __name__ == "__main__":
    main()
