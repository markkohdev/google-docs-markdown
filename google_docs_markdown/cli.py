"""CLI interface for Google Docs Markdown tool."""

from typing import Annotated

import typer

app = typer.Typer(
    name="google-docs-markdown",
    help="Download and edit Google Docs as Markdown using the Google Docs API",
)


@app.command()
def download(
    document_url: Annotated[
        str,
        typer.Option(
            prompt=True, help="Google Doc URL or document ID (you will be prompted for this if not provided)"
        ),
    ],
    output: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output",
            help="Output file or directory path (defaults to a directory named after the document title)",
        ),
    ] = None,
    tabs: Annotated[
        list[str] | None, typer.Option("-t", "--tabs", help="Specific tabs to download (defaults to all tabs)")
    ] = None,
) -> None:
    """Download a Google Doc as Markdown."""
    typer.echo("Downloading a Google Doc as Markdown...")
    raise NotImplementedError("This command is not implemented yet")


@app.command("list-tabs")
def list_tabs(
    document_url: Annotated[str, typer.Option(prompt=True, help="Google Doc URL or document ID")],
) -> None:
    """List all tabs in a Google Doc."""
    typer.echo("Listing all tabs in a Google Doc...")
    raise NotImplementedError("This command is not implemented yet")


@app.command()
def upload(
    document_url: Annotated[
        str, typer.Option(prompt=True, help="Google Doc URL or document ID (for update mode)")
    ],
    local_document_path: Annotated[
        str | None,
        typer.Option(
            "--local-path",
            help="Path to local markdown file (if not provided, inferred from document URL)",
        ),
    ] = None,
    create: Annotated[bool, typer.Option("--create", help="Create a new Google Doc instead of updating the existing one")] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Force upload even when no changes detected")
    ] = False,
) -> None:
    """Upload Markdown to a Google Doc."""
    typer.echo("Uploading Markdown to a Google Doc...")
    raise NotImplementedError("This command is not implemented yet")


@app.command()
def diff(
    document_url: Annotated[str, typer.Option(prompt=True, help="Google Doc URL or document ID")],
    local_document_path: Annotated[
        str | None,
        typer.Option(
            "--local-path",
            help="Path to local markdown file (if not provided, inferred from document URL)",
        ),
    ] = None,
) -> None:
    """Show differences between local Markdown and Google Doc."""
    typer.echo("Showing differences between local Markdown and Google Doc...")
    raise NotImplementedError("This command is not implemented yet")


@app.command()
def setup() -> None:
    """Set up authentication and configuration."""
    typer.echo("Setting up authentication and configuration...")
    raise NotImplementedError("This command is not implemented yet")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
