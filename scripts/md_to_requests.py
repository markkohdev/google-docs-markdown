#!/usr/bin/env python3
"""Deserialize a directory of Markdown files back into a Google Docs API requests JSON.

Walks a markdown output directory (e.g. ``test_outputs/Markdown Conversion Example - Multi-Tab/``),
deserializes each ``.md`` tab file into API requests, and writes a JSON file next to
the directory containing the full ``batchUpdate`` request payload per tab.

Usage::

    uv run python scripts/md_to_requests.py "test_outputs/Markdown Conversion Example - Multi-Tab/"
    uv run python scripts/md_to_requests.py "test_outputs/Markdown Conversion Example - Single-Tab/"

The output file is written as ``<directory_name>.requests.json`` next to the input directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google_docs_markdown.markdown_deserializer import deserialize
from google_docs_markdown.metadata import parse_metadata


def collect_md_files(directory: Path) -> list[tuple[Path, str]]:
    """Recursively collect .md files with their relative paths as tab names."""
    results: list[tuple[Path, str]] = []
    for md_file in sorted(directory.rglob("*.md")):
        rel = md_file.relative_to(directory)
        tab_name = str(rel.with_suffix(""))
        results.append((md_file, tab_name))
    return results


def deserialize_tab(md_path: Path) -> dict:
    """Deserialize a single markdown file and return a summary dict."""
    text = md_path.read_text(encoding="utf-8")
    metadata = parse_metadata(text)

    tab_id = (metadata or {}).get("tabId", "")
    doc_id = (metadata or {}).get("documentId", "")

    requests = deserialize(text, tab_id=tab_id)
    request_dicts = [r.model_dump(exclude_none=True) for r in requests]

    return {
        "tabName": md_path.stem,
        "tabId": tab_id,
        "documentId": doc_id,
        "markdownChars": len(text),
        "markdownLines": text.count("\n"),
        "requestCount": len(requests),
        "requests": request_dicts,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/md_to_requests.py <markdown_directory>")
        print()
        print("Example:")
        print('  uv run python scripts/md_to_requests.py "test_outputs/Markdown Conversion Example - Multi-Tab/"')
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    md_files = collect_md_files(input_dir)
    if not md_files:
        print(f"No .md files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_file = input_dir.parent / f"{input_dir.name}.requests.json"

    print(f"Input:  {input_dir}")
    print(f"Output: {output_file}")
    print(f"Found {len(md_files)} tab(s):")
    print()

    tabs = []
    total_requests = 0

    for md_path, tab_name in md_files:
        tab_data = deserialize_tab(md_path)
        tabs.append(tab_data)
        total_requests += tab_data["requestCount"]

        req_summary: dict[str, int] = {}
        for r in tab_data["requests"]:
            for key in r:
                req_summary[key] = req_summary.get(key, 0) + 1

        print(f"  {tab_name}")
        print(f"    tabId: {tab_data['tabId'] or '(none)'}")
        print(f"    {tab_data['markdownLines']} lines → {tab_data['requestCount']} requests")
        for rtype, count in sorted(req_summary.items(), key=lambda x: -x[1]):
            print(f"      {rtype}: {count}")
        print()

    doc_id = next((t["documentId"] for t in tabs if t["documentId"]), None)

    output = {
        "documentId": doc_id,
        "tabCount": len(tabs),
        "totalRequests": total_requests,
        "tabs": tabs,
    }

    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output_file} ({total_requests} total requests across {len(tabs)} tab(s))")


if __name__ == "__main__":
    main()
