from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(
    help="PlantGenie knowledge graph build system.",
    no_args_is_help=True,
)


@app.command()
def init() -> None:
    """Recreate the catalog nodes in Neo4j from the Python catalog."""
    raise NotImplementedError


@app.command()
def sync(
    upstream: Annotated[
        bool,
        typer.Option(
            help="Also re-download upstreams whose source URL ETag changed.",
        ),
    ] = False,
) -> None:
    """Refresh DataAsset checksums from Swift HEAD."""
    raise NotImplementedError


@app.command()
def status(
    step_id: Annotated[
        str | None,
        typer.Argument(help="Root the listing at this step."),
    ] = None,
) -> None:
    """List every step and its staleness."""
    raise NotImplementedError


@app.command()
def plan(
    step_id: Annotated[
        str,
        typer.Argument(help="Step to show the build subgraph for."),
    ],
) -> None:
    """Show the topo subgraph that `build` would run."""
    raise NotImplementedError


@app.command()
def build(
    step_id: Annotated[
        str | None,
        typer.Argument(help="Step to build, after its stale ancestors."),
    ] = None,
    all_steps: Annotated[
        bool,
        typer.Option("--all", help="Build everything stale, topo order."),
    ] = False,
) -> None:
    """Build a step (and its stale ancestors) or everything stale."""
    raise NotImplementedError


@app.command()
def logs(
    target: Annotated[
        str,
        typer.Argument(help="A run id, or a step id with --last."),
    ],
    last: Annotated[
        bool,
        typer.Option(help="Treat target as a step id and fetch its latest."),
    ] = False,
) -> None:
    """Stream or fetch a BuildRun's JSON log."""
    raise NotImplementedError


if __name__ == "__main__":
    app()
