"""CLI interface for Google Docs Markdown tool."""

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    name="google-docs-markdown",
    help="Download and edit Google Docs as Markdown using the Google Docs API",
)


def _resolve_document_url(document_url: str | None) -> str:
    """Prompt for document URL if not provided as a positional argument."""
    if document_url:
        return document_url
    url: str = typer.prompt("Document url")
    return url


def _prompt_stale_cleanup(
    written: dict[str, Path],
    find_stale_files: Callable[[Path, set[Path]], list[Path]],
    remove_empty_dirs: Callable[[Path], None],
    *,
    force: bool = False,
) -> None:
    """Check for leftover .md files from removed tabs and offer to delete them."""
    import os

    if not written:
        return
    written_paths = list(written.values())
    output_dir = Path(os.path.commonpath(written_paths))
    if output_dir.is_file():
        output_dir = output_dir.parent

    stale = find_stale_files(output_dir, set(written_paths))
    if not stale:
        return

    typer.echo("\nThe following files are no longer in the document:")
    for p in stale:
        typer.echo(f"  {p}")
    if force or typer.confirm("Delete?", default=False):
        for p in stale:
            p.unlink()
            typer.echo(f"  Deleted {p}")
        remove_empty_dirs(output_dir)


@app.command()
def download(
    document_url: Annotated[
        str | None,
        typer.Argument(help="Google Doc URL or document ID"),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output",
            help=(
                "Parent directory for output (a subdirectory named after the"
                " document title is created inside it; defaults to current directory)"
            ),
        ),
    ] = None,
    tabs: Annotated[
        list[str] | None, typer.Option("-t", "--tabs", help="Specific tabs to download (defaults to all tabs)")
    ] = None,
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Overwrite existing files and delete stale files without prompting"),
    ] = False,
) -> None:
    """Download a Google Doc as Markdown."""
    from google_docs_markdown.downloader import (
        Downloader,
        FileConflictError,
        find_stale_files,
        remove_empty_dirs,
    )

    document_url = _resolve_document_url(document_url)
    dl = Downloader()
    typer.echo("Downloading...")

    try:
        written = dl.download_to_files(
            document_url,
            output_dir=output,
            tab_names=tabs or None,
            overwrite=force,
        )
    except FileConflictError as exc:
        typer.echo("The following files already exist:")
        for p in exc.existing_paths:
            typer.echo(f"  {p}")
        if not typer.confirm("Overwrite?"):
            raise typer.Abort() from exc
        written = dl.download_to_files(
            document_url,
            output_dir=output,
            tab_names=tabs or None,
            overwrite=True,
        )
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for tab_path, file_path in written.items():
        typer.echo(f"  {tab_path} -> {file_path}")
    typer.echo(f"Downloaded {len(written)} tab(s).")

    _prompt_stale_cleanup(written, find_stale_files, remove_empty_dirs, force=force)


@app.command("list-tabs")
def list_tabs(
    document_url: Annotated[str | None, typer.Argument(help="Google Doc URL or document ID")] = None,
) -> None:
    """List all tabs in a Google Doc."""
    from google_docs_markdown.downloader import Downloader, TabSummary

    document_url = _resolve_document_url(document_url)
    dl = Downloader()

    try:
        tabs = dl.get_tabs(document_url)
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not tabs:
        typer.echo("No tabs found.")
        return

    def _print_tab(tab: TabSummary, indent: int = 0) -> None:
        prefix = "  " * indent
        typer.echo(f"{prefix}- {tab.title} (id: {tab.tab_id})")
        for child in tab.child_tabs:
            _print_tab(child, indent + 1)

    title = dl.get_document_title(document_url)
    typer.echo(f'Tabs in "{title}":')
    for tab in tabs:
        _print_tab(tab)


@app.command()
def upload(
    document_url: Annotated[str | None, typer.Argument(help="Google Doc URL or document ID")] = None,
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
    document_url = _resolve_document_url(document_url)
    typer.echo("Uploading Markdown to a Google Doc...")
    raise NotImplementedError("This command is not implemented yet")


@app.command()
def diff(
    document_url: Annotated[str | None, typer.Argument(help="Google Doc URL or document ID")] = None,
    local_document_path: Annotated[
        str | None,
        typer.Option(
            "--local-path",
            help="Path to local markdown file (if not provided, inferred from document URL)",
        ),
    ] = None,
) -> None:
    """Show differences between local Markdown and Google Doc."""
    document_url = _resolve_document_url(document_url)
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
