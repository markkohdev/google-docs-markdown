#!/usr/bin/env python3
# /// script
# dependencies = ["requests", "beautifulsoup4"]
# ///
"""Download the Google Docs API reference page as plain text.

Fetches the HTML from the google-api-python-client documentation site,
extracts the visible text content (equivalent to CMD+A, CMD+C in a browser),
and writes it to resources/google_docs_api_reference.txt.
"""

from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://googleapis.github.io/google-api-python-client/docs/dyn/docs_v1.documents.html"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "resources" / "google_docs_api_reference.txt"
REQUEST_TIMEOUT_SECONDS = 120


def fetch_and_extract_text(url: str) -> str:
    """Fetch the HTML page and return its visible text content."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Collapse runs of 3+ blank lines down to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    print(f"Fetching {URL} (timeout={REQUEST_TIMEOUT_SECONDS}s) ...")
    text = fetch_and_extract_text(URL)

    header = f"# Copied and pasted from {URL}"
    content = f"{header}\n\n{text}\n"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")

    line_count = content.count("\n")
    print(f"Wrote {line_count} lines to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
