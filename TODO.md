# TODO

Work on the dev Waldur project first (`NAISS 2026/4-1190`, terraform workspace
`dev`). Once something is stable there it moves to prod (`NAISS 2025/22-1577`,
workspace `prod`).

Prod is live on `www.plantgenie.se` and should not be touched to test any of
this.

Completed deployment, account and gene-list work moved to `HANDOFF.md` on
2026-09-10 — this file is open work only.

Work these TDD-style: write the test, watch it fail, write the minimum to pass,
refactor. UI first against static data, then add the backend endpoints and
update the tests where they break — except where an auth scheme has to exist
before the UI can be faked against it.

## Now

- [ ] **Reorder the wizard so the list is named last.** Naming and describing a
      list before choosing what goes in it asks for a decision the user cannot
      make yet. Wanted order: taxon, genome, then list details. Note the Figma
      file has naming as step 1 across three artboards
      (`Desktop — Step 1: List Details`, `Step 2: Select Taxon`,
      `Step 3: Select Genome`), so the design needs the same reordering.

## Next

- [ ] **Redraw the Figma landing board.** `Desktop — Landing (Signed out)`
      (node `122:2`) no longer matches what ships: the board has one card and
      a hero, the app has two cards side by side (`#returning-user` and
      `#new-account-card`) and no hero. The returning-visitor board was never
      drawn and is not needed — a signed-in visitor is redirected to `/lists`.
- [ ] **BLAST history per account.** Let a user see their past searches. The
      auth this needs is already in place, but `submit_blast`
      (`api/v2/blast/routes.py:51`) persists **nothing** linking a job to an
      owner — it writes `{job_id}.fa` to disk and dispatches celery with
      `task_id=job_id`. So the work is a job→account record written at submit
      time (a sqlite table alongside `gene_lists` is the obvious shape), plus
      the query and the listing UI. The UI half is the easy half.
- [ ] **Error handling across the UI.** Failed requests are currently silent:
      the wizard's "Create list" button just does nothing when the POST fails,
      which is how a 401 from the new account gating read as a broken selector
      during e2e debugging. Every mutation should surface a message and a
      pending state — `useCreateListMutation` already returns `isLoading` and
      `error`, and `GenomeSelector.tsx:116` has a `<p role="alert">` pattern to
      follow. Wanted everywhere, not just the wizard.

      Includes the one landing-page case left unhandled: a stored ID the
      backend cannot be asked about. `useAccountIdSync` treats any rejection
      the same, so a network failure silently signs the user out and drops
      their ID. A rejected ID should be cleared; an unreachable backend should
      keep it and say so.
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
- [ ] **Rename GeneList → PlantGenIE.** The navbar wordmark is done
      (`components/Navbar.tsx:56`). Still wrong: `<title>GeneList</title>` in
      `ui/index.html:17`, and the wordmark on all 18 Figma artboards.
- [ ] **Populate the dev shared volume.** Copy the duckdb database across, plus
      the BLAST databases. Blocking: `lifespan` in `dependencies.py` does
      `db_path.resolve(strict=True)` then `duckdb.connect()`, so the dev API
      will not boot without `plantgenie-backend.db` present, and it also needs
      all six `OS_*` Swift vars set.

## Long term — may or may not happen

### nginx and limits

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
- [ ] **Rate limit `/api/v2/accounts`: creation and sign-in.** Both routes
      under it are abuse targets. `POST` is unauthenticated row creation, so a
      loop grows the `accounts` table. `GET /me` answers 200 or 401, so a loop
      guesses IDs. All attempts count, successful or not — nobody signs in
      constantly. The app also calls `/me` on every full page load
      (`useAccountIdSync`), so leave room for refreshes and new tabs.
      `limit_req_zone $binary_remote_addr zone=accounts:10m rate=10r/m;` in
      the `http` block, and a `location /api/v2/accounts` carrying
      `limit_req zone=accounts burst=10 nodelay;` plus
      `limit_req_status 429;`. The location must be declared **before** the
      general `/api/` one.
- [ ] **Loose per-IP limit on all of `/api/`.** Every endpoint that takes the
      ID can be used to guess it, so the accounts limit alone is bypassed by
      guessing through `GET /v2/lists` instead. Around `5r/s` with a burst —
      normal browsing never reaches it, and one IP would need ~6,000 years to
      find any one of 10,000 accounts. nginx applies only the matching
      location's `limit_req`, so repeat this zone inside the accounts
      location too.
- [ ] **Rate limit `POST /api/v2/blast`.** A BLAST search against pinsy is 20
      Gbases of work; submitting them in a loop is a cheap way to flatten the
      machine. Same shape as the accounts limit, with a tighter rate.
- [ ] **Check `proxy_read_timeout` against polling.** Not an issue while results
      are fetched by polling a job id, but it becomes one the moment anything
      waits on a search in-request.

### Deployment and storage

- [ ] **Swift still points at the old cluster** (`OS_*` in `.env.shared`). A
      self-hosted MinIO on the new cluster is the likely replacement.
- [ ] **`fsid=1` on the NFS export.** Add to the `/etc/exports` line in
      `nginx-cloud-init.yaml`. Without it every nginx replacement gives the
      export new file handles and all clients go `ESTALE` — hit on prod after
      the TLS rebuild. Deliberately not applied to prod yet; it rides along with
      the next prod nginx change.
- [ ] **Destroy provisioner for `neo4j_data_attachment`.** `shared_attachment`
      has one and it is proven; the neo4j volume does not, and it holds the real
      graph load. Same three lines plus `detach-volume.py`.
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
- [ ] **A scoped service token for automation** instead of a personal one. The
      current token is shared by both workspaces and expires.

### Dependency hygiene

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

### Features

- [ ] **Search-driven list building.** Full text and/or semantic search over
      gene descriptions, returning scored results with a configurable result
      count or score threshold, rows selectable as in the add-by-ID flow. No
      endpoint exists for this yet.
- [ ] **JBrowse on the gene page.** `genes/GenePage.tsx` exists and is
      populated; embedding a JBrowse instance in it is still open.
- [ ] **Account details page.** Reveal the ID in groups of four, copy,
      download-as-file, and a blunt warning that losing it loses the lists.
      Deferred behind the landing page — the login flow is what actually blocks
      users, and the landing page carries the warning already.
- [ ] **A feature strip on the landing page.** The shipped page is two cards
      and nothing else — a visitor who has not been told what PlantGenIE is
      gets no answer from it. Naming what the site does (build lists, add by
      ID, search genes, BLAST) is the smallest version, growing as features
      land.

### Loose ends

- [ ] `external_network_uuid` and `external_network_backend_id` are declared in
      `variables.tf` and referenced nowhere. Dead in both tfvars files.
- [ ] Report the port `security_groups` HTTP 500 to NAISS. Reproduction and
      talking points are in `HANDOFF.md`, still unsent.

## Reference — account IDs

Decided 2026-09-03, built out over the following week. A 16-digit ID, generated
server-side, that is both identity and credential: possession is access, there
is no password. Displayed in groups of four. The endpoints, `AccountDep`, bearer
injection, list scoping and the landing page are all done — see `HANDOFF.md`.

Decisions worth not re-litigating:

- **No email in v1.** Recovery by email was considered and deferred: there is no
  SMTP anywhere in the repo, and an address is PII in a way an anonymous number
  is not. Phase 2 if it is wanted, with verification, rate limiting, and a
  recovery response that does not reveal whether an address is registered.
- **Accounts are created without a signup form.** This was chosen over keeping
  anonymous lists in localStorage specifically to avoid a second, client-side
  implementation of lists plus a bulk-claim endpoint on signup. Losing
  localStorage loses the lists either way; the only difference is where the
  bytes sit.

  Superseded in part: the original spec had creation happen silently on first
  list creation, with the account page only ever *revealing* an ID that already
  existed. The landing page makes generation an explicit click instead. The
  reasoning above still holds — what changes is that minting is deliberate
  rather than a side effect of loading the site.
- **Only a SHA-256 of the ID is stored**, so a database leak does not hand over
  working credentials. Plain SHA-256 rather than a password hash because the
  input is high-entropy and random — but 16 digits is only ~53 bits, so rate
  limiting carries the real load.
- **Paste-your-ID is the login flow**, and the only way to reach an account from
  a second device. Easy to overlook because there is no password.

## Reference — UPSC brand palette

Derived 2026-09-10 for the landing page. The three brand colours, with the
contrast ratios that decide where each one may be used:

| Role | Value | On white | Use for |
| --- | --- | --- | --- |
| Blue | `#424753` | 9.30:1 | Headings, section titles, body emphasis |
| Green | `#097e35` | 5.19:1 | Wordmark, primary button fill, outline buttons |
| Yellow | `#fcc542` | 1.59:1 | Warning surfaces only — **never** text or white-on-yellow |

Notes:

- The green above is the **logo** green, sampled from
  `UPSC_Logo_A_RGB_White.png` (the "White" refers to the wordmark; the leaf mark
  is in full colour). The UPSC website CSS uses `#0b9e17` instead, which fails
  AA with white text at 3.55:1 and so cannot carry a primary button. If
  `#0b9e17` is the official green, keep it for large text and borders and use
  `#097e35` as the interactive shade.
- Yellow takes dark text well — `#424753` on `#fcc542` is 5.85:1 — which is why
  the landing page uses it as an 18% fill with a 3px left rule behind the
  "save your ID" warning.
- Do **not** re-derive this from `upsc.se`'s stylesheets. That site is a Joomla
  template whose most-repeated colours are template chrome, not the brand.
- In code, `--color-upsc-blue`, `--color-upsc-green` and `--color-upsc-yellow`
  are in `ui/src/index.css` and the navbar uses the blue. **Not done:**
  `--color-primary` is still `#3885f5`, so every `bg-primary` button — the
  landing page's three, the wizard's, the list pages' — is still the old blue.
  Pointing `--color-primary` at `#097e35` switches them all at once.
