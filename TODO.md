# TODO — dev deployment

Work on the dev Waldur project first (`NAISS 2026/4-1190`, terraform workspace
`dev`). Once something is stable there it moves to prod (`NAISS 2025/22-1577`,
workspace `prod`) — see the last section for what is already queued to move.

Prod is live on `www.plantgenie.se` and should not be touched to test any of
this.

## Blockers before the first `dev` apply

`dev.tfvars` has three `CHANGEME` values. All three come from a single tag.

Decided: dev builds are driven by prerelease tags like `v0.3.5-dev`. Both
`build-frontend-release.yaml` and `build-docker-image-release.yaml` already fire
on `v*.*.*`, and that pattern matches a `-dev` suffix, so one tag produces all
three artifacts:

- `plantgenie-ui-v0.3.5-dev.zip` attached to the release
- `fastapi-backend:v0.3.5-dev`
- `celery-worker:v0.3.5-dev`

Tags fire regardless of which branch they are on, so tagging a feature branch
gives a deployable dev build. No per-branch CI is needed — the branch-tagging
workflow change considered earlier is dropped.

- [x] `build-frontend-release.yaml` marks `-dev` tags as prereleases
      (`prerelease: ${{ contains(github.ref_name, '-dev') }}`), so they do not
      take over "Latest". Untested until the first tag is cut.
- [x] First dev tag `v0.4.6-dev` cut 2026-08-31. Both workflows succeeded, the
      release is correctly marked Pre-release, and `dev.tfvars` now points at
      `v0.4.6-dev` for both images and the UI zip. The zip URL is deterministic:
      `https://github.com/UPSC-PlantGenIE/plantgenie-api/releases/download/<tag>/plantgenie-ui-<tag>.zip`
      Note this bundle is the **new React UI** from `ui/`, built with
      `VITE_API_BASE_URL=/api/` — unlike prod, which serves `plantgenie-ui`
      v0.3.4.
- [x] `build-docker-image.yaml` built `plantgenie-api:latest`, which nothing
      deployed — the tfvars pin `fastapi-backend` and `celery-worker`. Deleted
      in `96904db` alongside the Waldur terraform rewrite.

## First `dev` apply

- [x] `terraform workspace select dev && terraform apply -var-file=dev.tfvars`.
      Six instances, two volumes, a floating IP. Remember
      `set -a; source ../.env.shared; set +a` first — the destroy provisioners
      read the token from the environment.
- [x] Point `dev.plantgenie.se` at the dev nginx floating IP. It previously
      pointed at the old SSC deployment, so this was a cutover, not a new
      record.
- [x] `sudo certbot --nginx -d dev.plantgenie.se` on the dev nginx VM. HTTPS
      confirmed working 2026-09-01.
- [ ] Populate the dev shared volume: copy the duckdb database across, plus the
      BLAST databases. Required regardless of the v2-only focus — `lifespan` in
      `dependencies.py` does `db_path.resolve(strict=True)` then
      `duckdb.connect()`, so the API will not boot without
      `plantgenie-backend.db` present, and it also needs all six `OS_*` Swift
      vars set.
- [x] Load the graph into dev neo4j. Done 2026-09-02, not by loading CSVs on
      the VM but by dumping the local store and restoring it:
      `neo4j-admin database dump neo4j --to-stdout` locally, then
      `database load neo4j --from-stdin --overwrite-destination=true` on dev.
      Only the `neo4j` database moves, so dev keeps its own tfvars password
      (auth lives in the untouched `system` database). Reachable over bolt at
      `dev.plantgenie.se:7687` through the nginx stream proxy. See
      `neo4j-data-load-plan.md` for how the local store was built.

## Fixes to prove on dev, then carry to prod

- [ ] **`fsid=1` on the NFS export.** Add to the `/etc/exports` line in
      `nginx-cloud-init.yaml`. Without it every nginx replacement gives the
      export new file handles and all clients go `ESTALE` — hit on prod after
      the TLS rebuild. Deliberately not applied to prod yet; it rides along with
      the next prod nginx change.
- [ ] **Destroy provisioner for `neo4j_data_attachment`.** `shared_attachment`
      has one and it is proven; the neo4j volume does not, and it will hold the
      real graph load. Same three lines plus `detach-volume.py`.
- [ ] **Port `shared-volume.service` to neo4j.** neo4j's volume was formatted by
      hand because `disk_setup`/`fs_setup` cannot work when the volume attaches
      after the instance. nginx's udev-triggered oneshot handles both a fresh
      volume and one moving between instances.

      This bit on 2026-09-02: after a reboot, `/dev/sdb` came back raw with no
      filesystem and no `neo4j_data` label, so `opt-neo4j.mount` failed its
      device dependency and `systemctl start neo4j` hung on
      `RequiresMountsFor`. Recovered with
      `mkfs.ext4 -L neo4j_data /dev/sdb` and `mount -a`, which is exactly the
      manual step this item exists to remove.

## Smaller things

- [ ] `vars.VITE_APP_TITLE` is unset on this repo. Old repo has `PlantGenIE`.
- [ ] `external_network_uuid` and `external_network_backend_id` are declared in
      `variables.tf` and referenced nowhere. Dead in both tfvars files.
- [ ] A scoped service token for automation instead of a personal one. The
      current token is shared by both workspaces and expires.
- [ ] Report the port `security_groups` HTTP 500 to NAISS. Reproduction and
      talking points are at the bottom of `HANDOFF.md`, still unsent.
- [ ] Swift still points at the old cluster (`OS_*` in `.env.shared`). A
      self-hosted MinIO on the new cluster is the likely replacement.

## Dependency hygiene

Direct deps were bumped via `uv lock --upgrade` on 2026-09-01. `redis` (6.4.0)
and `testcontainers` (4.13.3) are held below latest by something in the
resolution; not chased down.

- [ ] **Consolidate on one HTTP client.** Three are in the tree: `aiohttp`
      (`plantgenie_api/client.py`), `requests` (blast + enrichment routes,
      `shared/services/openstack.py`), and `httpx` (unit tests, arriving via
      `fastapi[standard]`). httpx covers sync and async, so it is the obvious
      survivor and `aiohttp` would go.
- [ ] **Removal candidates — declared but never imported.** Verify against the
      Swift/MinIO decision above before pulling the Swift ones, since that
      rewrite may remove them anyway.
      - `pyarrow` (root) — zero references in the repo
      - `python-keystoneclient` (root, task-queue) — never imported; Keystone
        auth is done by hand with `requests` in `shared/services/openstack.py`
      - `python-swiftclient` (task-queue) — Swift is only touched in
        `plantgenie_api` and `shared`
      - `networkx` + `types-networkx` (task-queue) — only `go-enrich` uses it
      - `docker` + `types-docker` (task-queue dev) — testcontainers pulls docker
        itself
      - `redis` (root) — direct import only in `test_container_setup.py`;
        `celery[redis]` already provides it
- [ ] **Imported but not declared**, currently relying on transitives:
      `requests` (root and `shared`), `httpx` (root dev), `duckdb`
      (task-queue), `pydantic` (`shared`).
