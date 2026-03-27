"""Embedded metadata block for Google Docs Markdown files.

Each markdown file contains a metadata block at the bottom as an HTML
comment.  This module handles serialization and parsing of that block.

Format::

    <!-- google-docs-metadata
    {
      "documentId": "...",
      "tabId": "t.0",
      ...
    }
    -->

Safety: ``>`` is escaped as ``\\u003e`` in JSON string values to prevent
a premature ``-->`` from closing the HTML comment.
"""

from __future__ import annotations

import json
import re
from typing import Any

_METADATA_START = "<!-- google-docs-metadata"
_METADATA_END = "-->"
_METADATA_RE = re.compile(
    r"<!-- google-docs-metadata\s*\n(.*?)\n-->",
    re.DOTALL,
)


class _SafeEncoder(json.JSONEncoder):
    """JSON encoder that escapes all ``>`` characters in output to prevent premature ``-->`` comment close."""

    def encode(self, o: Any) -> str:  # noqa: ANN401
        result = super().encode(o)
        return result.replace(">", "\\u003e")


def serialize_metadata(
    *,
    document_id: str | None = None,
    tab_id: str | None = None,
    revision_id: str | None = None,
    default_styles: dict[str, Any] | None = None,
    named_styles: Any = None,
    lists: Any = None,
) -> str:
    """Produce the ``<!-- google-docs-metadata ... -->`` block.

    Returns a string suitable for appending to the end of a markdown file.
    """
    payload: dict[str, Any] = {}
    if document_id is not None:
        payload["documentId"] = document_id
    if tab_id is not None:
        payload["tabId"] = tab_id
    if revision_id is not None:
        payload["revisionId"] = revision_id
    if default_styles is not None:
        payload["defaultStyles"] = default_styles
    if named_styles is not None:
        payload["namedStyles"] = named_styles
    if lists is not None:
        payload["lists"] = lists

    json_str = json.dumps(payload, indent=2, cls=_SafeEncoder, ensure_ascii=False)
    return f"{_METADATA_START}\n{json_str}\n{_METADATA_END}"


def parse_metadata(markdown_text: str) -> dict[str, Any] | None:
    """Extract and parse the metadata block from a markdown string.

    Returns ``None`` if no metadata block is found.  The ``\\u003e``
    escapes are transparently decoded by the JSON parser.
    """
    m = _METADATA_RE.search(markdown_text)
    if not m:
        return None
    json_str = m.group(1)
    return json.loads(json_str)  # type: ignore[no-any-return]


def strip_metadata(markdown_text: str) -> str:
    """Return *markdown_text* with the metadata block removed.

    Useful for diffing content without metadata.
    """
    return _METADATA_RE.sub("", markdown_text).rstrip("\n") + "\n"
