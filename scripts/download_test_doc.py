#!/usr/bin/env python3
"""
Download a Google Doc as JSON.

This script uses the GoogleDocsAPIClient to fetch a document from the Google Docs API
and save it as a JSON file in the test resources directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from google_docs_markdown.api_client import GoogleDocsAPIClient

app = typer.Typer()


@app.command()
def main(
    document: Annotated[str, typer.Argument(help="Google Docs URL or document ID")],
    output: Annotated[
        str,
        typer.Option(
            "-o",
            "--output",
            help="Output filename (default: uses document title)",
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
    Download a Google Doc as JSON file.

    DOCUMENT can be a Google Docs URL or document ID.

    Examples:

    \b
        download_doc_json.py https://docs.google.com/document/d/DOC_ID/edit
        download_doc_json.py DOC_ID --output my-document.json
        download_doc_json.py DOC_ID --output-dir /path/to/output
    """
    # Normalize empty strings to None
    output = output.strip() if output else None

    # Determine output directory
    if str(output_dir).strip():
        output_dir_path = output_dir
    else:
        # Default to test resources directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        output_dir_path = project_root / "tests" / "resources" / "document_jsons"

    # Create output directory if it doesn't exist
    output_dir_path.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize client and fetch document
        typer.echo("Connecting to Google Docs API...")
        client = GoogleDocsAPIClient()

        typer.echo(f"Extracting document ID from: {document}")
        doc_id = client.extract_document_id(document)
        typer.echo(f"Document ID: {doc_id}")

        typer.echo("Fetching document...")
        doc = client.get_document(doc_id)

        # Determine output filename
        if output:
            output_filename = output
        else:
            # Use document title, sanitized for filename
            title = doc.get("title", "Untitled Document")
            # Replace invalid filename characters
            safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title)
            safe_title = safe_title.replace(" ", "_")
            output_filename = f"{safe_title}.json"

        output_path = output_dir_path / output_filename

        # Check if file exists and handle overwrite logic
        if output_path.exists():
            if not overwrite:
                if not typer.confirm(f"File already exists at {output_path}. Overwrite?"):
                    typer.echo("Aborted. File not overwritten.")
                    raise typer.Exit()

        # Write JSON file
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

    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error downloading document: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
