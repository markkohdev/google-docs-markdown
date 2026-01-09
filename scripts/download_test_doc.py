#!/usr/bin/env python3
"""
Download a Google Doc as JSON.

This script uses the GoogleDocsAPIClient to fetch a document from the Google Docs API
and save it as a JSON file in the test resources directory.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from google_docs_markdown.api_client import GoogleDocsAPIClient


@click.command()
@click.argument("document", required=True)
@click.option(
    "-o",
    "--output",
    default=" ",
    help="Output filename (default: uses document title)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=" ",
    help="Output directory (default: tests/resources/document_jsons)",
)
@click.option(
    "--pretty",
    type=bool,
    default=False,
    help="Pretty-print JSON with indentation",
)
@click.option(
    "--overwrite",
    type=bool,
    default=False,
    help="Overwrite existing file without prompting",
)
def main(document: str, output: str | None, output_dir: Path | None, pretty: bool, overwrite: bool) -> None:
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
    output = output.strip()
    output_dir = str(output_dir).strip()

    if not output:
        output = None
    if not output_dir:
        output_dir = None

    # Determine output directory
    if output_dir:
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
        click.echo("Connecting to Google Docs API...")
        client = GoogleDocsAPIClient()

        click.echo(f"Extracting document ID from: {document}")
        doc_id = client.extract_document_id(document)
        click.echo(f"Document ID: {doc_id}")

        click.echo("Fetching document...")
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
                if not click.confirm(f"File already exists at {output_path}. Overwrite?"):
                    click.echo("Aborted. File not overwritten.")
                    return

        # Write JSON file
        click.echo(f"Saving to: {output_path}")
        with output_path.open("w", encoding="utf-8") as f:
            if pretty:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            else:
                json.dump(doc, f, ensure_ascii=False)

        click.echo(f"✓ Successfully downloaded document: {doc.get('title', 'Untitled')}")
        click.echo(f"  Saved to: {output_path}")
        click.echo(f"  Document ID: {doc.get('documentId', 'N/A')}")
        if "tabs" in doc:
            click.echo(f"  Tabs: {len(doc['tabs'])}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Error downloading document: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    main()
