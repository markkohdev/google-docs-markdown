"""CLI interface for Google Docs Markdown tool."""

from typing import Annotated

import typer

from google_docs_markdown.api_client import GoogleDocsAPIClient

app = typer.Typer(
    name="google-docs-markdown",
    help="Download and edit Google Docs as Markdown using the Google Docs API",
)


@app.command()
def download(
    document_url: Annotated[
        str,
        typer.Option(prompt=True, help="Google Doc URL or document ID (you will be prompted for this if not provided)"),
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
    client = GoogleDocsAPIClient()
    doc = client.get_document(document_url)
    typer.echo(f"Downloaded document: {doc.get('title')}")


@app.command("list-tabs")
def list_tabs(
    document_url: Annotated[str, typer.Option(prompt=True, help="Google Doc URL or document ID")],
) -> None:
    """List all tabs in a Google Doc."""
    typer.echo("Listing all tabs in a Google Doc...")
    raise NotImplementedError("This command is not implemented yet")


@app.command()
def upload(
    document_url: Annotated[str, typer.Option(prompt=True, help="Google Doc URL or document ID (for update mode)")],
    local_document_path: Annotated[
        str | None,
        typer.Option(
            "--local-path",
            help="Path to local markdown file (if not provided, inferred from document URL)",
        ),
    ] = None,
    create: Annotated[
        bool,
        typer.Option("--create", help="Create a new Google Doc instead of updating the existing one"),
    ] = False,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Force upload even when no changes detected")] = False,
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
def setup(
    revoke: Annotated[
        bool,
        typer.Option("--revoke", help="Revoke existing Application Default Credentials before setting up new ones"),
    ] = False,
    extra_scopes: Annotated[
        str,
        typer.Option("--extra-scopes", help="Additional scopes to append to the required scopes (comma-separated)"),
    ] = "",
    client_id_file: Annotated[
        str | None,
        typer.Option("--client-id-file", help="Path to client ID file for OAuth authentication"),
    ] = None,
) -> None:
    """Set up authentication and configuration."""
    from google_docs_markdown.setup import setup as run_setup

    run_setup(revoke=revoke, extra_scopes=extra_scopes, client_id_file=client_id_file)


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
