# PlantGenIE API

FastAPI backend, Celery task queue, and the new React UI for PlantGenIE.
The graph lives in neo4j, accounts and gene lists live in sqlite, and the
legacy v1 endpoints read duckdb. Deployed with Terraform to OpenStack
through Waldur on NAISS infrastructure: dev is NAISS 2026/4-1190, prod is
NAISS 2025/22-1577.

## Start here

- `TODO.md`: open work (Now / Next / Long term). Check this first.
- `HANDOFF.md`: deployment state, landmines, and decisions already made.
  Read the relevant section before touching infra or re-deciding anything.
- `MANUAL-DEPLOY.md`: updating a running deployment without an apply.
- `.claude/handoffs/`: dated per-session records. Write one with the
  `session-handoff` skill.
- `neo4j-data-load-plan.md`: the graph load plan.

## Layout

- `src/plantgenie_api/`: FastAPI app, mounted at `/api`
  - `api/v2/`: accounts, blast, genes, lists, taxa/assemblies/annotations
  - `api/v1/`: legacy
  - `dependencies.py`: lifespan, `Neo4jDep`, `AccountDep`, sqlite connection
  - `sqlite/schema.sql`: accounts and gene lists
- `packages/`: uv workspace members. `task-queue` (Celery: blast,
  enrichment), `shared` (config, database, openstack), `go-enrich`, `etl`
- `ui/`: React 19, Vite, Redux Toolkit / RTK Query, wouter, Tailwind 4, Yarn 4
- `scripts/neo4j/`: Cypher load scripts
- `infra/`: Terraform with the Waldur provider, workspaces `dev` and `prod`

## Commands

Backend, from the repo root:

```
uv run pytest src/tests/plantgenie_api/unit -q   # fast, fake neo4j; the default
uv run pytest                                    # all but e2e; starts containers, takes minutes
uv run pytest -m e2e                             # needs the compose stack and the vite dev server
uv run ruff check
uv run ty check
```

UI, from `ui/`:

```
yarn test:run
yarn lint
yarn format:check
yarn build
```

Stack: `docker compose --env-file .env up`. `.env` must set `HOST_DATA_DIR`
and `WORKTREE`.

## Running tests

- Run tests scoped to what changed (`uv run pytest <path>`,
  `yarn test:run <path>`), then the full unit suite once before calling a
  step done.
- Run `uv run pytest` and `uv run pytest -m e2e` only when asked.
- Run UI tests in the foreground with a 15s timeout. The full suite takes
  about 6s. If it times out, say so and show the last output.
- Never filter test output through `grep`, `head` or `tail`.
- Report failures as test name, expected vs received, and `file:line`.

## Tests

- TDD: failing test first, confirm it fails for the right reason, then
  the minimum to pass. The `tdd-feature` skill has the details.
- Few, trusted tests beat many unread ones.
- Backend unit tests override `get_neo4j_session` with `FakeNeo4jSession`.
  Set `next_records` to the shape the Cypher `RETURN` produces.
- UI tests sit beside the component as `<Component>.test.tsx`. API calls
  are mocked in `ui/src/mocks/handlers.ts`.

## Code style

- Python: ruff, line length 75, type annotations checked with ty. New
  endpoints are v2; response models subclass `PlantGenieModel`
  (camelCase aliases, `extra="forbid"`).
- UI: API calls go through RTK Query hooks in `ui/src/api/plantgenieApi.ts`.
  Prettier: semicolons, double quotes, 2-space indent, ES5 trailing commas.
  Tailwind built-in scales only, no arbitrary values. Brand colours are in
  "UPSC brand palette" in `TODO.md`.
- Shell: `set -euo pipefail`, quoted variables.
- Full variable names, never abbreviated (`connection`, not `con`).
- No explanatory comments in code.

## Git workflow

- Conventional Commits: `type(scope): imperative summary`, types `feat`,
  `fix`, `refactor`, `docs`, `test`, `chore`. Scopes: `api`, `ui`,
  `task-queue`, `etl`, `infra`, `neo4j`.
- A body that explains why, when the summary does not.
- No mention of Claude, Claude Code or AI assistance in commit messages:
  no `Co-Authored-By`, `Claude-Session` or "Generated with" lines.
- Commit only when asked.

## Data

- Sources are read-only: `/opt/data/plantgenie-knowledge` (also the local
  `DATA_PATH`) and the MinIO bucket `plantgenie-knowledge`.
- The graph is rebuilt from `scripts/neo4j/`. Deployed graphs get it by
  dump and restore, never by running load scripts against them.
- `plantgenie-userdata.sqlite` holds real accounts and gene lists. Never
  overwrite it. Every rsync from `/opt/data/plantgenie-knowledge` spells
  out `--exclude='plantgenie-userdata.sqlite'`.
- `schema.sql` is not a migration. A new column on an existing table
  needs a hand-applied `ALTER TABLE`.

## Boundaries

Always

- Work in dev (NAISS 2026/4-1190, workspace `dev`, `dev.plantgenie.se`).
- Explain what a command does before running it.
- Keep justifications for changes terse.
- Change dependencies only with `uv add` / `uv remove` and
  `yarn add` / `yarn remove`.

Ask first

- Creating or editing any file. Show the proposed change and wait.
  Approving a plan is not approval to write.
- Adding a dependency.
- Any command that reaches a remote host: `ssh`, `scp`, `rsync`,
  `terraform`, `gh`, `mc`, `curl` against a deployment.
- Commits and tags.

Never

- Use prod (`www.plantgenie.se`, workspace `prod`, NAISS 2025/22-1577) to
  test anything.
- Read, `cat`, `grep` or print credentials files without explicit
  permission: `.env`, `.env.*`, `infra/*.tfvars`, `infra/*.pem`,
  `infra/terraform.tfstate.d/`.
- Hand-edit `uv.lock` or `yarn.lock`.
- Commit secrets or data (`data/`, dumps, CSVs).
- Force-push or rewrite published history.
