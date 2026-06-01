from __future__ import annotations

import typer

app = typer.Typer(
    help="PlantGenie knowledge graph build system.",
    no_args_is_help=True,
)


if __name__ == "__main__":
    app()
