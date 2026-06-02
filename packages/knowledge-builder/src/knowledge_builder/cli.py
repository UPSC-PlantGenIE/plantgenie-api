from __future__ import annotations

import typer

from knowledge_builder.domain import load_app

app = typer.Typer(
    help="PlantGenie knowledge graph build system.",
    no_args_is_help=True,
)
app.add_typer(load_app, name="load")


if __name__ == "__main__":
    app()
