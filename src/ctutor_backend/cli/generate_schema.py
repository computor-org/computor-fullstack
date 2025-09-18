"""CLI command for generating VS Code JSON schema."""

from __future__ import annotations

import click

from ctutor_backend.scripts.generate_json_schema import main as generate_schema_main


@click.command(name="generate-schema")
def generate_schema() -> None:
    """Generate JSON schema for extension metadata files."""

    generate_schema_main()
    click.echo(click.style("✅ JSON schema generation complete", fg="green"))


if __name__ == "__main__":
    generate_schema()
