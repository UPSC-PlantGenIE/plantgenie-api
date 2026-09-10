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

## nginx

All of this lives in `infra/nginx-cloud-init.yaml`, not in the running
`/etc/nginx/nginx.conf` — certbot rewrites that file in place, and it is on the
boot volume, so anything edited by hand is lost on the next nginx replacement.

- [ ] **`client_max_body_size`.** The BLAST submit endpoint caps queries at 1 MB
      in the handler, but uvicorn buffers the whole body first, so a huge POST is
      fully received before being rejected. nginx should refuse it at the edge.
      Note nginx's default is already `1m`, which is *below* what a 1 MB query
      plus JSON overhead needs — so this has to be set explicitly, high enough
      for a legitimate query and low enough to be a real limit. Somewhere around
      `2m`, and the app keeps its own check for direct callers.
- [ ] **Rate limit `POST /api/v2/accounts`.** Unauthenticated row creation:
      anyone can call it in a loop and grow the `accounts` table. Two directives
      — `limit_req_zone $binary_remote_addr zone=accounts:10m rate=5r/m;` in the
      `http` block, and a `location /api/v2/accounts` carrying
      `limit_req zone=accounts burst=5 nodelay;` plus `limit_req_status 429;`.
      The location must be declared **before** the general `/api/` one.
- [ ] **Rate limit `POST /api/v2/blast`.** A BLAST search against pinsy is 20
      Gbases of work; submitting them in a loop is a cheap way to flatten the
      machine. Same shape as above, with a tighter rate.
- [ ] **Check `proxy_read_timeout` against polling.** Not an issue while results
      are fetched by polling a job id, but it becomes one the moment anything
      waits on a search in-request.

- [ ] `vars.VITE_APP_TITLE` is unset on this repo. Old repo has `PlantGenIE`.
- [ ] `external_network_uuid` and `external_network_backend_id` are declared in
      `variables.tf` and referenced nowhere. Dead in both tfvars files.
- [ ] A scoped service token for automation instead of a personal one. The
      current token is shared by both workspaces and expires.
- [ ] Report the port `security_groups` HTTP 500 to NAISS. Reproduction and
      talking points are at the bottom of `HANDOFF.md`, still unsent.
- [ ] Swift still points at the old cluster (`OS_*` in `.env.shared`). A
      self-hosted MinIO on the new cluster is the likely replacement.

## Gene list feature

Merged in from `plantgenie-old/api-new-react-ui-api-integration/TODO.md`. The
API section of that file is fully done, all of it superseded by v2: `/v2/taxa`
with common names, string slug IDs on Assembly and Annotation, `?taxon=` /
`?assembly=` filters, and `geneCount` / `isDefault` on Annotation.

- [x] Rewire the React wizard onto `/v2/taxa` + `/v2/assemblies` +
      `/v2/annotations`. Done — `GenomeSelector.tsx` uses all three hooks.
      Retiring the v1 endpoints is still outstanding.
- [ ] **Account IDs.** A unique numeric ID per user, like mullvad.net's VPN
      account numbers, used to store and retrieve their lists. Not started:
      `api/v2/lists/routes.py:61` returns a hardcoded `account_id="stub"` and
      nothing filters on it, so every list is visible to everyone. Visible on
      dev now that it is on a public URL. Specced 2026-09-03, see below.
- [x] Empty gene list page after "create list" — `lists/ListPage.tsx`.
- [x] Screens for adding user-entered gene IDs, with a validation view showing
      descriptions and IDs that were not found — `lists/AddByIdPage.tsx`,
      backed by `/v2/genes/lookup`.
- [ ] **Search-driven list building.** Full text and/or semantic search over
      gene descriptions, returning scored results with a configurable result
      count or score threshold, rows selectable as in the add-by-ID flow. No
      endpoint exists for this yet.
- [~] Gene list page populated with real genes, rows linking through to gene
      pages. `genes/GenePage.tsx` exists; embedding a JBrowse instance there is
      still open.
- [ ] **Error handling across the UI.** Failed requests are currently silent:
      the wizard's "Create list" button just does nothing when the POST fails,
      which is how a 401 from the new account gating read as a broken selector
      during e2e debugging. Every mutation should surface a message and a
      pending state — `useCreateListMutation` already returns `isLoading` and
      `error`, and `GenomeSelector.tsx:116` has a `<p role="alert">` pattern to
      follow. Wanted everywhere, not just the wizard.
- [ ] **Server-side validation of BLAST queries.** `BlastPage.tsx` checks the
      query starts with `>` so the user is not made to wait for a round trip,
      but that is a convenience, not a gate — anyone can POST directly. The
      submit endpoint must enforce, independently:
      - a **1 MB cap** on the query, returning 413. v1 capped the uploaded file
        (`MAX_FILE_SIZE` in `api/v1/blast/routes.py`); v2 takes the sequence as
        JSON text, so the cap applies to the field, and uvicorn will have
        buffered the whole body before the handler sees it.
      - real FASTA parsing rather than a `>` check, plus a cap on how many
        sequences one query may hold.
      - characters restricted to the nucleotide/protein alphabets.
      Note v1 used `FastaValidator`, whose import is currently unresolved —
      one of the four pre-existing `ty` errors.

Work these TDD-style as before: write the test, watch it fail, write the
minimum to pass, refactor. UI first against static data, then add the backend
endpoints and update the tests where they break.

## Account IDs — spec

Decided 2026-09-03. A 16-digit ID, generated server-side, that is both identity
and credential: possession is access, there is no password. Displayed in groups
of four.

**No email in v1.** Recovery by email was considered and deferred: there is no
SMTP anywhere in the repo, and an address is PII in a way an anonymous number is
not. Phase 2 if it is wanted, with verification, rate limiting, and a recovery
response that does not reveal whether an address is registered.

**Accounts are created silently on first use**, not by a signup form. The first
list creation with no stored ID does `POST /v2/accounts` first. This was chosen
over keeping anonymous lists in localStorage specifically to avoid a second,
client-side implementation of lists plus a bulk-claim endpoint on signup. Losing
localStorage loses the lists either way; the only difference is where the bytes
sit. The account page therefore *reveals* an ID that already exists rather than
creating one.

Endpoints:

| method | path | notes |
| --- | --- | --- |
| `POST` | `/v2/accounts` | 201 `{accountId}` — the only time the plaintext ID is returned |
| `GET` | `/v2/accounts/me` | validates the bearer; 200 `{createdAt, listCount}` or 401 |
| all | `/v2/lists/*` | require the bearer, filtered by owner |

Auth is `Authorization: Bearer <16 digits>`. An `AccountDep` dependency hashes
the token, looks it up and 401s if unknown, in the same shape as `Neo4jDep` and
`SqliteDep`.

Only a SHA-256 of the ID is stored, so a database leak does not hand over
working credentials. Plain SHA-256 rather than a password hash because the input
is high-entropy and random — but 16 digits is only ~53 bits, so rate limiting
carries the real load.

```sql
CREATE TABLE IF NOT EXISTS accounts (
    account_hash TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
ALTER TABLE gene_lists ADD COLUMN account_hash TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS gene_lists_account ON gene_lists (account_hash);
```

The `ALTER` is not idempotent under `schema.sql`'s `CREATE TABLE IF NOT EXISTS`
style and needs a guard, or the dev database gets dropped. Existing dev lists
become ownerless either way, so deleting them is simplest.

UI. `accountSlice` and `useAccountIdSync.ts` already persist an account id to
`localStorage.accountId`, so what is new is:

- `prepareHeaders` in `plantgenieApi.ts` injecting the bearer
- first list creation with no stored ID calling `POST /v2/accounts` first
- an `/account` page: the ID in groups of four, copy, download-as-file, and a
  blunt warning that losing it loses the lists
- **a paste-your-ID field on that page** — this is the login flow, and the only
  way to reach an account from a second device. Easy to overlook because there
  is no password
- a 401 meaning the stored ID is stale: clear it and start over

Two things to settle while building: `POST /v2/accounts` is unauthenticated row
creation and wants rate limiting, and `create_list`'s `account_id="stub"`
response field either becomes real or goes away.

Ladder — backend first here, against the UI-first note above, because the UI
cannot be meaningfully faked against an auth scheme that does not exist yet:

1. `POST /v2/accounts` returns a 16-digit ID
2. `GET /v2/accounts/me` 401s on an unknown ID
3. `GET /v2/lists` returns only that account's lists
4. UI: header injection, then bootstrap on first list, then the account page,
   then paste-existing-ID

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
