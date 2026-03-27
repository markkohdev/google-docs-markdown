#!/usr/bin/env python3
"""Round-trip test CLI: serialize a fixture JSON to markdown, then deserialize back to requests.

Usage::

    uv run python scripts/roundtrip_test.py tests/resources/document_jsons/Markdown_Conversion_Example_-_Single-Tab.json
    uv run python scripts/roundtrip_test.py tests/resources/document_jsons/Markdown_Conversion_Example_-_Multi-Tab.json

Live doc URL mode (requires Google API credentials)::

    uv run python scripts/roundtrip_test.py https://docs.google.com/document/d/DOC_ID/edit
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import typer

from google_docs_markdown.markdown_deserializer import deserialize
from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.models.document import Document
from google_docs_markdown.models.requests import Request

app = typer.Typer(help="Round-trip test for Google Docs ↔ Markdown conversion.")


def _request_type_counts(requests: list[Request]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for r in requests:
        for field_name in Request.model_fields:
            if getattr(r, field_name, None) is not None:
                counts[field_name] += 1
    return counts


def _all_insert_text(requests: list[Request]) -> str:
    parts = []
    for r in requests:
        if r.insertText and r.insertText.text:
            parts.append(r.insertText.text)
    return "".join(parts)


def _content_coverage(markdown: str, requests: list[Request]) -> float:
    """Compute fraction of markdown words that appear in insert text requests."""
    insert_text = _all_insert_text(requests).lower()
    words = [w for w in markdown.split() if len(w) >= 3 and w.isalpha()]
    if not words:
        return 1.0
    found = sum(1 for w in words if w.lower() in insert_text)
    return found / len(words)


def _run_json_roundtrip(fixture_path: Path) -> None:
    """Run roundtrip on a local JSON fixture file."""
    doc = Document.model_validate(json.loads(fixture_path.read_text()))
    if not doc.tabs:
        typer.echo(f"Error: No tabs found in {fixture_path}", err=True)
        raise typer.Exit(1)

    serializer = MarkdownSerializer()

    for tab_idx, tab in enumerate(doc.tabs):
        if not tab.documentTab:
            continue

        tab_title = "?"
        tab_id = "?"
        if tab.tabProperties:
            tab_title = tab.tabProperties.title or f"Tab {tab_idx}"
            tab_id = tab.tabProperties.tabId or "?"

        markdown = serializer.serialize(
            tab.documentTab,
            document_id=doc.documentId,
            tab_id=tab_id if tab_id != "?" else None,
        )
        requests = deserialize(markdown, tab_id=tab_id if tab_id != "?" else "")
        counts = _request_type_counts(requests)
        coverage = _content_coverage(markdown, requests)

        md_lines = markdown.count("\n")
        md_chars = len(markdown)

        typer.echo(f"Round-trip test: {fixture_path}")
        typer.echo(f"  Tab: {tab_title} (id={tab_id})")
        typer.echo(f"  Serialization: {md_lines} lines, {md_chars} chars")
        typer.echo(f"  Deserialization: {len(requests)} requests")

        summary_parts = []
        for rtype, count in counts.most_common():
            summary_parts.append(f"{rtype}({count})")
        typer.echo(f"  Request types: {', '.join(summary_parts)}")
        typer.echo(f"  Content coverage: {coverage * 100:.1f}% of markdown text appears in insert requests")
        typer.echo()


def _run_url_roundtrip(url: str) -> None:
    """Placeholder for live API roundtrip (requires credentials)."""
    typer.echo(f"Live API round-trip not yet implemented for: {url}")
    typer.echo("This mode requires Google API credentials and will:")
    typer.echo("  1. Download the document via API")
    typer.echo("  2. Serialize to markdown")
    typer.echo("  3. Deserialize to requests")
    typer.echo("  4. Create a new document with those requests")
    typer.echo("  5. Download the new document and diff")
    raise typer.Exit(1)


@app.command()
def main(
    source: str = typer.Argument(
        help="Path to a document JSON fixture file, or a Google Docs URL.",
    ),
) -> None:
    """Run a round-trip test on a Google Docs fixture or live document."""
    if source.startswith("http://") or source.startswith("https://"):
        _run_url_roundtrip(source)
    else:
        path = Path(source)
        if not path.exists():
            typer.echo(f"Error: File not found: {path}", err=True)
            raise typer.Exit(1)
        if not path.suffix == ".json":
            typer.echo(f"Error: Expected a .json file, got: {path}", err=True)
            raise typer.Exit(1)
        _run_json_roundtrip(path)


if __name__ == "__main__":
    app()
