#!/usr/bin/env python3
"""
Download Google Docs as JSON.

This script uses GoogleDocsTransport to fetch documents from the Google Docs API
and save them as JSON files in the test resources directory.

Supports downloading a single document by URL/ID, or batch-downloading all URLs
listed in a file via --urls-file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from google_docs_markdown.transport import GoogleDocsTransport

app = typer.Typer()

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "resources" / "document_jsons"


def download_document(
    client: GoogleDocsTransport,
    document: str,
    *,
    output: str | None = None,
    output_dir_path: Path = DEFAULT_OUTPUT_DIR,
    pretty: bool = False,
    overwrite: bool = False,
) -> None:
    """Download a single Google Doc and save it as JSON."""
    typer.echo(f"Extracting document ID from: {document}")
    doc_id = client.extract_document_id(document)
    typer.echo(f"Document ID: {doc_id}")

    typer.echo("Fetching document...")
    doc = client.get_document(doc_id)

    if output:
        output_filename = output
    else:
        title = doc.get("title", "Untitled Document")
        safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title)
        safe_title = safe_title.replace(" ", "_")
        output_filename = f"{safe_title}.json"

    output_path = output_dir_path / output_filename

    if output_path.exists() and not overwrite:
        if not typer.confirm(f"File already exists at {output_path}. Overwrite?"):
            typer.echo("Aborted. File not overwritten.")
            raise typer.Exit()

    typer.echo(f"Saving to: {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        if pretty:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        else:
            json.dump(doc, f, ensure_ascii=False)

    typer.echo(f"✓ Successfully downloaded document: {doc.get('title', 'Untitled')}")
    typer.echo(f"  Saved to: {output_path}")
    typer.echo(f"  Document ID: {doc.get('documentId', 'N/A')}")
    if "tabs" in doc:
        typer.echo(f"  Tabs: {len(doc['tabs'])}")


@app.command()
def main(
    document: Annotated[
        str | None,
        typer.Argument(help="Google Docs URL or document ID", show_default=False),
    ] = None,
    urls_file: Annotated[
        Path | None,
        typer.Option(
            "-f",
            "--urls-file",
            help="File containing Google Docs URLs (one per line). Overrides DOCUMENT.",
        ),
    ] = None,
    output: Annotated[
        str,
        typer.Option(
            "-o",
            "--output",
            help="Output filename (default: uses document title). Ignored with --urls-file.",
        ),
    ] = " ",
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            help="Output directory (default: tests/resources/document_jsons)",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty/--no-pretty",
            help="Pretty-print JSON with indentation",
        ),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite/--no-overwrite",
            help="Overwrite existing file without prompting",
        ),
    ] = False,
) -> None:
    """
    Download Google Docs as JSON files.

    Provide either a DOCUMENT (URL or ID) or --urls-file with a file of URLs.

    Examples:

    \b
        download_test_doc.py https://docs.google.com/document/d/DOC_ID/edit
        download_test_doc.py DOC_ID --output my-document.json
        download_test_doc.py --urls-file tests/resources/document_jsons/doc_urls.txt
    """
    if document and urls_file:
        typer.echo("Error: provide either DOCUMENT or --urls-file, not both.", err=True)
        raise typer.Exit(1)
    if not document and not urls_file:
        typer.echo("Error: provide either DOCUMENT or --urls-file.", err=True)
        raise typer.Exit(1)

    output_name = output.strip() if output else None

    output_dir_path = output_dir if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_dir_path.mkdir(parents=True, exist_ok=True)

    typer.echo("Connecting to Google Docs API...")
    client = GoogleDocsTransport()

    if urls_file:
        if not urls_file.exists():
            typer.echo(f"Error: URLs file not found: {urls_file}", err=True)
            raise typer.Exit(1)

        urls = [
            line.strip()
            for line in urls_file.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        if not urls:
            typer.echo("No URLs found in file.")
            raise typer.Exit()

        typer.echo(f"Found {len(urls)} URL(s) in {urls_file}\n")
        succeeded, failed = 0, 0

        for i, url in enumerate(urls, 1):
            typer.echo(f"[{i}/{len(urls)}] Processing: {url}")
            try:
                download_document(
                    client,
                    url,
                    output_dir_path=output_dir_path,
                    pretty=pretty,
                    overwrite=True,
                )
                succeeded += 1
            except typer.Exit:
                raise
            except Exception as e:
                typer.echo(f"  ✗ Failed: {e}", err=True)
                failed += 1
            typer.echo()

        typer.echo(f"Done: {succeeded} succeeded, {failed} failed.")
        if failed:
            raise typer.Exit(1)
    else:
        assert document is not None
        try:
            download_document(
                client,
                document,
                output=output_name,
                output_dir_path=output_dir_path,
                pretty=pretty,
                overwrite=overwrite,
            )
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e
        except typer.Exit:
            raise
        except Exception as e:
            typer.echo(f"Error downloading document: {e}", err=True)
            raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
