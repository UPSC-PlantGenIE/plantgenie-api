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
- [ ] Cut the first `v*.*.*-dev` tag and set `fastapi_image_tag`,
      `celery_worker_image_tag` and `ui_download_url` in `dev.tfvars` to match.
      The zip URL is deterministic:
      `https://github.com/UPSC-PlantGenIE/plantgenie-api/releases/download/<tag>/plantgenie-ui-<tag>.zip`
- [ ] `build-docker-image.yaml` builds `plantgenie-api:latest`, which nothing
      deploys — the tfvars pin `fastapi-backend` and `celery-worker`. Dead
      workflow, decide whether to delete it.

## First `dev` apply

- [ ] `terraform workspace select dev && terraform apply -var-file=dev.tfvars`.
      Six instances, two volumes, a floating IP. Remember
      `set -a; source ../.env.shared; set +a` first — the destroy provisioners
      read the token from the environment.
- [ ] Point `dev.plantgenie.se` at the dev nginx floating IP. It currently
      points at the old SSC deployment, so this is a cutover, not a new record.
- [ ] `sudo certbot --nginx -d dev.plantgenie.se` on the dev nginx VM.
- [ ] Populate the dev shared volume. Decide where from — a copy of the prod
      one, or a smaller subset. `plantgenie-backend.db` at minimum, since the
      API fails on it.
- [ ] Load the graph into dev neo4j. Both deployments currently have an empty
      store; real content comes from the knowledge-builder load into
      `/opt/neo4j/import`. `NEO4J_AUTH` only applies to an empty data
      directory, so the tfvars password takes effect only on a fresh store.

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
