#!/usr/bin/env python3
"""
Download Google Docs as Markdown to the test_outputs directory.

Reads document URLs from tests/resources/document_jsons/doc_urls.txt and
invokes the CLI ``download`` command for each one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from google_docs_markdown.cli import download as cli_download

REPO_ROOT = Path(__file__).resolve().parent.parent
URLS_FILE = REPO_ROOT / "tests" / "resources" / "document_jsons" / "doc_urls.txt"
OUTPUT_DIR = REPO_ROOT / "test_outputs"

app = typer.Typer()


@app.command()
def main(
    urls_file: Annotated[
        Path,
        typer.Option("-f", "--urls-file", help="File containing Google Docs URLs"),
    ] = URLS_FILE,
    output_dir: Annotated[
        Path,
        typer.Option("-o", "--output-dir", help="Parent output directory"),
    ] = OUTPUT_DIR,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing files and delete stale files without prompting"),
    ] = False,
) -> None:
    """Download all docs listed in a URLs file as Markdown into test_outputs/."""
    if not urls_file.exists():
        typer.echo(f"Error: URLs file not found: {urls_file}", err=True)
        raise typer.Exit(1)

    urls = [
        line.strip() for line in urls_file.read_text().splitlines() if line.strip() and not line.strip().startswith("#")
    ]

    if not urls:
        typer.echo("No URLs found in file.")
        raise typer.Exit()

    output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Found {len(urls)} URL(s) in {urls_file}")
    typer.echo(f"Output directory: {output_dir}\n")

    succeeded, failed = 0, 0

    for i, url in enumerate(urls, 1):
        typer.echo(f"[{i}/{len(urls)}] Downloading: {url}")
        try:
            cli_download(document_url=url, output=str(output_dir), force=force)
            succeeded += 1
        except typer.Abort:
            typer.echo("  Skipped.")
        except typer.Exit as exc:
            if exc.exit_code == 0:
                succeeded += 1
            else:
                failed += 1
        except Exception as e:
            typer.echo(f"  Failed: {e}", err=True)
            failed += 1
        typer.echo()

    typer.echo(f"Done: {succeeded} succeeded, {failed} failed.")
    if failed:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
