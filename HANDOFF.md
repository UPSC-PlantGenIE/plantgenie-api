# Handoff — Waldur migration

Branch: `feature/waldur-migration`, cut from `origin/main` at `ae30a51` (the
merge of `feature/react-ui-api-integration`, PR #6).

## Goal

Migrate the deployed infrastructure off the current OpenStack cluster onto the
new one, which is fronted by Waldur. Today's `infra/` is Terraform against the
OpenStack provider directly.

Two Waldur projects are available, one per environment:

- **dev** — runs the new React UI from this repo's `ui/`.
- **prod** — keeps running the old UI from the separate `plantgenie-ui` repo
  until we're ready to cut over.

Both run the same FastAPI backend from this repo.

## Decided: Terraform with the Waldur provider

`waldur/waldur`, pinned to `8.1.3-rc.2` in `infra_waldur/main.tf`. Note this is
a prerelease — Terraform will not select it automatically, so the pin is load
bearing. Without it `init` silently picks `0.0.10`, whose schema is far behind
the published docs.

There is no direct OpenStack API access on this cluster: no Horizon, no openrc.
Everything goes through Waldur's REST API, so the existing `infra/` cannot be
re-pointed — it has to be rewritten against `waldur_openstack_*` resources.
`infra_waldur/` is that rewrite, starting from a single test instance.

Auth is `WALDUR_API_URL` + `WALDUR_ACCESS_TOKEN` (both in `.env.shared`, and in
`infra_waldur/prod.tfvars`, which is gitignored). Tokens expire; a stale one
returns `{"detail": "Token has expired."}`.

Worth doing: a scoped service token for automation, rather than a personal one.

## Verified working end to end

`infra_waldur/` provisions an SSH key, the `plantgenie-test` scratch instance, a
100 GB data volume, a `plantgenie-neo4j` instance running neo4j off that volume,
and a `plantgenie-nginx` instance with a floating IP proxying bolt to it.

Verified end to end on 2026-08-27: the volume detaches from one instance and
attaches to another, neo4j starts against the mounted store, and
`bolt://<nginx floating ip>:7687` authenticates from outside the cluster.

The neo4j store copied from the old `north-dev` cluster is faithful but empty —
`databases/` is 880K and `transactions/` is 515M, because nothing was ever
loaded into the dev database. Real content comes from the knowledge-builder load
into `/opt/neo4j/import`.

Project `NAISS 2025/22-1577` (`950a75640950426a94a8ac2cd446b7e3`), tenant
`1cb7834e0b48471398af441b7c1af91a`, internal network
`naiss-202522-1577-int-net` on `192.168.42.0/24`, external network
`openstack-pub` (backend id `45060427-7ac9-4262-9b6b-285867cf983e`), floating
IP quota 50.

## Landmines found the hard way

- **`security_groups` on port creation returns HTTP 500.** Server-side crash,
  not validation. Reproduces with an *empty* list, so it is not about the shape
  of the entries: `POST /api/openstack-ports/` with
  `{"name": "x", "network": "<url>", "security_groups": []}` → 500. The same
  payload without the key → 201. The provider docs' own port example cannot run
  against this deployment. **Report this to NAISS.**
- **The workaround** is `POST /api/openstack-ports/{uuid}/update_security_groups/`
  with a list of URL *strings*. Note the inconsistency: that endpoint wants
  strings, while `PATCH` on the port wants dicts (and 500s anyway).
  `infra_waldur/attach-security-groups.py` does this, driven by a
  `null_resource` provisioner after the instance is created.
- **Always include `default` in the group set.** `ssh` and `web` are
  ingress-only; `default` carries the allow-all egress rules. Without it the
  instance cannot reply and SSH hangs with no error — this cost an afternoon.
  `default` also allows all traffic between ports that carry it, which is what
  `internal_traffic` did in the old `infra/`, so no extra group is needed for
  VM-to-VM.
- **Security groups cannot be declared on the instance.** Both
  `instance.security_groups` and `instance.ports[].security_groups` are
  computed-only in the provider schema, in 0.0.10 and 8.1.3-rc.2 alike. The
  instance-level `update_security_groups` action reports success but never
  propagates to the port, so it has to be done per-port.
- **A standalone `waldur_openstack_port` is a dead end.** Passing it to the
  instance as `ports = [{ port = ... }]` makes order submission 500; only
  `ports = [{ subnet = ... }]` works, and that makes Waldur create its own port
  that Terraform never sees. Hence the IP-based port lookup in the script.
- **`waldur_core_ssh_public_key` needs `trimspace()`** on the public key.
  Waldur strips the trailing newline, and the mismatch fails the apply with
  "Provider produced inconsistent result after apply". The key is still created,
  leaving state drift to clean up.
- **`name` filters are substring matches.** `pcd.small` matches three flavors.
  Use `name_exact`.
- **`waldur_openstack_volume_attachment` 404s on create.** The API action works
  fine — `POST /api/openstack-volumes/{uuid}/attach/` with
  `{"instance": "<instance url>"}` returns 202 — so this is the provider, not
  the deployment. `infra_waldur/attach-volume.py` drives it from a
  `null_resource`, detaching from the current instance first if needed and
  waiting on `runtime_state`.
- **`user_data` needs `trimspace()` too**, same as the ssh key: Waldur strips
  the trailing newline and the apply fails with "Provider produced inconsistent
  result after apply". The message says "inconsistent values for sensitive
  attribute" because `user_data` is sensitive in the schema, so terraform will
  not show you the diff.
- **The prebuilt groups do not cover bolt.** `web` is 80/443 only, `ssh` is 22,
  `ping` is icmp, `rdp` is 3389, all from `0.0.0.0/0`. Port 7687 needed a new
  group.
- `waldur_openstack_security_group` as a *resource* works. `nginx.tf` creates
  the `bolt` group with an inline `rules` list; attribute names match the API
  (`direction`, `ethertype`, `protocol`, `from_port`, `to_port`, `cidr`).
- **The guest sees volumes as `/dev/sdX`, not `/dev/vdX`.** The Waldur API
  reports the same. The old `infra/` modules all assume `/dev/vdb`.
- **Destroying an instance destroys its attached data volume.** Replacing nginx
  on 2026-08-30 deleted `plantgenie-shared` and everything on it. Terraform had
  *not* planned that: the 7 destroys were 3 instances plus 4 `null_resource`s,
  and `waldur_openstack_volume.shared` was never in the plan. It went out of
  band, and the next `attach-volume.py` run failed with a 404 on the volume GET.
  **The neo4j data volume is exposed to exactly the same thing**, and it will
  hold the real graph load. Detach before replacing an instance, or find
  whatever the Waldur equivalent of `delete_on_termination` is.
- **`fixed_ips` works at create and silently no-ops on update.** Pinning an
  instance's internal IP works if the port is created with it. Changing a pin on
  an existing instance plans as an in-place update, and the apply fails with
  "Provider produced inconsistent result after apply ... was 192.168.42.10, but
  now 192.168.42.91". State is left untouched, so it is recoverable, but the
  only way to move a pinned IP is `-replace`. When `user_data` changes in the
  same apply that is free, since that forces replacement on its own.
- **Instances cannot reference each other's IPs both ways.** The old `infra/`
  created six standalone `openstack_networking_port_v2` resources and fed every
  module `port.all_fixed_ips[0]`, so no instance ever depended on another. That
  is unavailable here (see the standalone-port dead end above), so IPs come from
  `instance.internal_ips`, and any two VMs that point at each other deadlock:
  nginx proxies to application while application NFS-mounts from nginx gives
  `Error: Cycle`. Pinning both addresses as constants is what breaks it. A data
  source in the middle does not help — reading an address inherits a dependency
  on whatever owns it.

## Watch list

Things that may bite later. Fix when they surface, not before.

- `neo4j-cloud-init.yaml` uses `$RELEASE` for the docker apt source instead of
  the old hardcoded `noble`. It worked on Ubuntu 26.04, but it is doing a
  lookup the old file did not.
- Volumes attach *after* the instance resource completes, so `/dev/sdb` does not
  exist while cloud-init runs and `disk_setup`/`fs_setup` can never work.
  Uncommenting those blocks in `neo4j-cloud-init.yaml` will not help. neo4j's
  volume was formatted by hand for this reason. nginx instead ships
  `shared-volume.service`, a oneshot that udev triggers off `dev-sdb.device`:
  it formats only if `blkid` finds no filesystem, mounts, and pulls up
  `nfs-server`. That works for a fresh volume and for one moving between
  instances, so port it to neo4j at its next rebuild.
- Splitting the NFS server onto its own VM was considered on 2026-08-30 and not
  done. It was the other way to break the dependency cycle, and it is still the
  cleaner separation, but pinning the two IPs solved the same problem without a
  seventh instance. Worth revisiting if nginx starts doing too much.
- Old cluster's sshd sets `AllowAgentForwarding no`, so `ssh -A` through to
  those instances does not work. Stage copies through your laptop instead.
- The volume attaches *after* the instance resource completes, so cloud-init
  could reach `mounts` before the disk exists. Handled by `nofail` on the mount
  plus `RequiresMountsFor=/opt/neo4j` on `neo4j.service`, which is why neo4j is
  a systemd unit rather than a `docker run` in `runcmd` as in the old modules.
- `NEO4J_AUTH` only applies to an empty data directory, so `neo4j_password` in
  tfvars is ignored whenever an existing store is attached. The database
  currently takes the old `north-dev` password, not the tfvars one.
- Backend and celery talk to Swift on the *old* cluster
  (`packages/shared/.../openstack.py`, `OS_*` in `.env.shared`). Decided
  2026-08-28: keep pointing at the old cluster's Swift for now. A self-hosted
  MinIO on the new cluster is the likely replacement.

## What the new cluster has to provide

The backend gained a hard Neo4j dependency in the merge:

- `dependencies.py` calls `verify_connectivity()` during the FastAPI lifespan,
  so the app will not start without a reachable Neo4j — including on the prod
  instance, whose old UI doesn't use it.
- Env vars `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` must be present.
- `docker-compose.yaml` bind-mounts `/opt/neo4j/{data,logs,import}`. The
  `import` directory is where the curated CSVs land for the graph load.

## Deploy model (decided)

Single `main` branch, no `dev` branch. The difference between environments is
deployment config, not source history.

- push to `main` → dev Waldur project (`build-docker-image.yaml` already does
  the images).
- tag `v*.*.*` → prod (`build-docker-image-release.yaml`).

## Current state

Seven instances are running as of 2026-08-30, `plantgenie-application` having
been added. They can be stopped and started with
`POST /api/openstack-instances/{uuid}/{stop,start}/`; the provider has no
power-state attribute, so this is outside Terraform and causes no plan drift.

Boot ordering no longer needs babysitting. Both NFS clients mount with `nofail`
and their units carry `RequiresMountsFor=/opt/app-data`, so a late nginx means
the service retries every 10s instead of coming up wrong. Verified by reboot on
both application and queue.

nginx's floating IP is now `130.236.225.56`; the bolt endpoint moved with it.
Internal addresses are pinned for nginx (`192.168.42.11`) and application
(`192.168.42.12`) in a `locals` block in `main.tf`. Everything else is DHCP.

Stopping does not appear to reduce what the project is charged: the instances'
marketplace `state` stays `OK` while `runtime_state` is `SHUTOFF`, and no
per-VM plan exists — only the tenant carries one (`Default`, unit `month`).
Whether NAISS meters core-hours behind that monthly plan is not visible from
the API. Worth asking them in the same mail as the port `security_groups` 500.

nginx, application and queue were all replaced on 2026-08-30, so their uuids have
changed. neo4j, rabbitmq and redis are unchanged:

| instance | uuid |
| --- | --- |
| neo4j | `5a67f8c36b97450faa886f8e848369cf` |
| rabbitmq | `cc0d27b76716413793dcc2198121ad96` |
| redis | `7fae473ae5804cffab9b1499281a0c28` |

Current uuids for the rest: `terraform state show waldur_openstack_instance.<name>`.

## Remaining work

Ordered. Each group is a separate apply.

**A. Queue backing services** — nothing depends on them, so they go first.

- [x] `rabbitmq.tf` + `rabbitmq-cloud-init.yaml`, ported from
      `infra/modules/rabbitmq`. Docker, `rabbitmq:4.2.5-management-alpine`, no
      floating IP, security groups `default` + `ssh`.
- [x] `redis.tf` + `redis-cloud-init.yaml`, same shape, redis on 6379.
- [x] Verified 2026-08-28 with `nc -z` from the nginx VM: 5672 and 6379 both
      open. Both boot volumes are 50 GB, unlike the earlier instances' 20 GB.

**B. Shared storage**

- [x] `waldur_openstack_volume.shared`, 100 GB, attached to nginx by
      `attach-volume.py` in the same way as `neo4j_data`.
- [x] NFS server in `nginx-cloud-init.yaml`: `nfs-kernel-server`, `/etc/exports`
      for the internal subnet, ufw 2049. nginx was recreated to pick this up,
      so its floating IP changed and the bolt endpoint moved with it.
- [x] Copy the old SSC NFS contents into `/srv/shared`, staged through the
      laptop since the old cluster's sshd sets `AllowAgentForwarding no`. Done
      2026-08-28.

**C. Celery**

- [x] `queue.tf` + cloud-init from `infra/modules/queue`: NFS mount at
      `/opt/app-data`, `docker login ghcr.io`, celery-worker image.
- [x] Verified 2026-08-28: `add.delay(2, 3).get()` returns 5 from inside the
      container, so the task reaches rabbitmq and the result comes back out of
      redis.
- The Swift application credential was created by Terraform in the old `infra/`
  (`openstack_identity_application_credential_v3.celery`). There is no identity
  API here, so `os_application_credential_{id,secret}` are tfvars, reusing the
  credential already in `.env.shared` — still pointing at old-cluster Swift.
- `config.py` hardcodes `broker_url`/`result_backend` to localhost; the
  deployment relies on celery reading `CELERY_BROKER_URL` and
  `CELERY_RESULT_BACKEND` from the environment to override them.
- `docker login` runs once in cloud-init, so GHCR credentials are baked into the
  instance's boot. Rotating the PAT means recreating the VM or logging in by
  hand. The one carried over from `north-dev.tfvars` had already expired
  (Jul 22 2026) and was replaced.

**D. Backend** — start here next session. It needs the same NFS mount as the
queue, so it is the place to prove the pattern in E before applying it to the
already-working queue.

- [x] `application.tf` from `infra/modules/application`, plus `NEO4J_URI`,
      `NEO4J_USER`, `NEO4J_PASSWORD`. Otherwise the same env block as
      `queue-cloud-init.yaml`, plus `-p 8000:8000`. nginx reaches it over the
      internal network, so `default` + `ssh` are the only groups it needs.
- [x] Built with the `fastapi.service` shape from E rather than the old module's
      `runcmd` `docker run`. Reboot-verified 2026-08-30: host and container
      listings of `/opt/app-data` match.
- [x] nginx `http` block proxying `/api/` to the app and `/rabbitmq/` to the
      management UI. `server_name _` on port 80, no TLS yet. Both return 200
      through `http://130.236.225.56/`.
- [ ] `location /` serving the UI bundle. Not started — needs a decision on
      where the bundle comes from (GitHub release asset, which is a private repo
      so the `wget` needs a token, or rsync'd up by hand).
- [ ] TLS. Needs certbot, `python3-certbot-nginx`, the acme-challenge location,
      ufw 443 and a real `server_name`, with DNS already pointing at the
      floating IP. **Settle the floating IP first** — it changes every time
      nginx's `user_data` changes, which would break DNS and the cert on every
      later nginx edit.
- [ ] Nothing published has the v2 API. `fastapi_image_tag` is `v0.4.5`, and no
      tag contains the commit that added `src/plantgenie_api/api/v2` — it came
      in with the PR #6 merge. `/api/v1/available-species` works; `/api/v2/taxa`
      404s until a new image is built. Bumping the tag is now a one-VM change,
      since the application's pinned IP keeps nginx out of the plan.

**E. Make the NFS mount survive boot ordering** — done 2026-08-30.

Both problems below are fixed, on application and queue alike. The queue was
being replaced anyway when its `nfs_internal_ip` moved to the pinned `.11`, so
the change rode along for free. `docker exec celery-worker python -c "from
task_queue.tasks import add; print(add.delay(2, 3).get(timeout=10))"` returns 5.

The original diagnosis, kept because it explains why the fix is shaped this way:

- The fstab entry has no `nofail`, so a missing NFS server blocks boot. `nofail`
  alone is not enough though: it stops the block, it does not retry.
- Worse, `docker run --restart unless-stopped` from `runcmd` means dockerd
  restarts celery-worker at boot independently of the mount. Docker bind mounts
  default to `rprivate` propagation, so if `/opt/app-data` mounts *after* the
  container starts, the container keeps seeing the empty underlying directory
  for its whole life. The worker looks healthy and silently has no data.

Fix, mirroring `neo4j.service` in `neo4j-cloud-init.yaml:52`:

- [x] fstab entry gains `nofail`: `"defaults,nfsvers=4,nofail"`. systemd already
      treats `nfs` as `_netdev`, so network ordering is automatic.
- [x] A `celery-worker.service` with `Requires=docker.service`,
      `After=docker.service`, `RequiresMountsFor=/opt/app-data`,
      `Restart=always`, `RestartSec=10`, and `ExecStart=/usr/bin/docker run
      --rm ...` carrying the env vars previously in `runcmd`.
- [x] Drop `--restart unless-stopped` so systemd owns the lifecycle instead of
      racing dockerd.

`RequiresMountsFor` also covers "eventually": systemd retries the mount unit on
every restart attempt, so a late nginx means the worker retries every 10s until
the mount succeeds rather than coming up wrong once.

Changing `user_data` replaces the instance. The queue VM holds no state, so it
is a clean rebuild, but it shows up as destroy/create in the plan.

## Repo state

`infra_waldur/` is fully committed: `49305a9` covers neo4j and nginx, `95c2c82`
adds rabbitmq, redis, the shared volume and the celery queue, and a third commit
adds the application, the pinned IPs, the nginx `http` block and the celery
systemd unit. Nothing in `infra_waldur/` is outstanding. `IMPLEMENTATION.md`
stays untracked — unrelated semantic-search notes, don't commit it.
`prod.tfvars` and the state files are gitignored and local; HCP Terraform
state-only with local execution is the fallback if more than one person needs to
apply.

`plantgenie-test` is still running and still costing something. Nothing
references it. Removing it means deleting lines 73–131 of `instance.tf` only —
that file also holds the shared data sources and the `tls_private_key.ssh` /
`waldur_core_ssh_public_key.ssh` that every other instance uses.

Already committed as `160010b`: the frontend release workflow ported from
`plantgenie-ui` (adapted for `ui/`, no Rust/wasm step, Yarn 4 `--immutable`),
plus `packageManager` and `engines.node` in `ui/package.json` so corepack and
`setup-node` pin the right versions in CI.

## TODO: report the port security_groups 500 to NAISS

Not sent yet. Reproduction below.

Fails, HTTP 500 with an HTML error page and no JSON body:

```bash
curl -X POST "https://waldur.pcd.arrhenius.naiss.se/api/openstack-ports/" \
  -H "Authorization: token $WALDUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sgtest",
    "network": "https://waldur.pcd.arrhenius.naiss.se/api/openstack-networks/d562b9c5dd2c4fa88f10fa1486ee97b8/",
    "security_groups": []
  }'
```

Succeeds, HTTP 201, identical payload minus the `security_groups` key:

```bash
curl -X POST "https://waldur.pcd.arrhenius.naiss.se/api/openstack-ports/" \
  -H "Authorization: token $WALDUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sgtest",
    "network": "https://waldur.pcd.arrhenius.naiss.se/api/openstack-networks/d562b9c5dd2c4fa88f10fa1486ee97b8/"
  }'
```

Points to make:

- An *empty* list fails, so it is not about the contents. Also tried
  `[{"name": "ssh"}]`, `[{"name": "ssh", "url": "..."}]`, and with `fixed_ips`
  present as in the provider's documented example — all 500. Only
  `[{"url": "..."}]` differs, returning 400
  (`{"security_groups": [{"name": ["This field is required."]}]}`), which shows
  the serializer expects `name` and then crashes downstream of validation.
- **The endpoint's own `OPTIONS` metadata advertises the field as writable at
  creation**, and pins down the only legal shape:

  ```json
  "security_groups": {
    "required": false, "read_only": false,
    "child": {"children": {
      "uuid": {"read_only": true},
      "name": {"required": true, "read_only": false, "max_length": 150},
      "url":  {"read_only": true}
    }}
  }
  ```

  `name` is the only settable child — and `[{"name": "ssh"}]` is exactly the
  payload that 500s. This also explains the 400 from `[{"url": "..."}]`: `url`
  is read-only, so it is discarded and the required `name` is then missing.
  Validation is behaving correctly; the crash is downstream of it.
- Since `[]` also 500s, the handler is failing on the popped `security_groups`
  value unconditionally, before any per-group lookup can happen.
- Adding a valid `fixed_ips` entry (`ip_address` plus the subnet's *backend*
  id, `f775592d-4f27-4c22-864a-6f737df3d8ea` — the Waldur uuid is rejected
  here) does not help. Nor does `port_security_enabled: true`, worth noting
  since both the network and the subnet report `port_security_enabled: null`.
- `PATCH /api/openstack-ports/{uuid}/` with `security_groups` as dicts also
  500s; as URL strings it returns 400 (`Expected a dictionary, but got str`).
- `POST /api/openstack-ports/{uuid}/update_security_groups/` with a list of URL
  *strings* works (202). The capability exists, just not at creation — and the
  two endpoints disagree on whether they want strings or dicts.
- This makes the `waldur_openstack_port` example in the Terraform provider docs
  unusable, since it declares `security_groups` on the port.

Context for their logs: project `NAISS 2025/22-1577`
(`950a75640950426a94a8ac2cd446b7e3`), tenant `1cb7834e0b48471398af441b7c1af91a`,
2026-08-25 around 12:30–12:45 CEST and again around 19:45–20:00 CEST. The 500s
are Django's `DEBUG=False` HTML page (145 bytes, `server: gunicorn`), so there
is no body on our side at all. A traceback from theirs would say whether it is
the serializer or the backend executor.

`vars.VITE_API_BASE_URL` needs setting on this repo's `production` GitHub
environment before a tagged release builds a usable bundle.
