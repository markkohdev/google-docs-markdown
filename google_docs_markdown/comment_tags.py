"""Comment tag system for non-Markdown Google Docs elements.

Provides serialization and parsing for wrapping HTML comment annotations:

    <!-- type: {json_data} -->visible content<!-- /type -->

Self-closing variant (no visible content):

    <!-- type: {json_data} -->
    <!-- type -->

Supported tag types: person, date, style, suggestion, rich-link,
section-break, page-break, column-break, table-of-contents, auto-text,
equation, chip-placeholder, title, subtitle, header, footer.

The embedded metadata block at the bottom of each markdown file uses a
separate format handled by :mod:`google_docs_markdown.metadata`.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Any


class TagType(StrEnum):
    """Supported comment tag types."""

    PERSON = "person"
    DATE = "date"
    STYLE = "style"
    SUGGESTION = "suggestion"
    RICH_LINK = "rich-link"
    SECTION_BREAK = "section-break"
    PAGE_BREAK = "page-break"
    COLUMN_BREAK = "column-break"
    TABLE_OF_CONTENTS = "table-of-contents"
    AUTO_TEXT = "auto-text"
    EQUATION = "equation"
    CHIP_PLACEHOLDER = "chip-placeholder"
    TITLE = "title"
    SUBTITLE = "subtitle"
    HEADER = "header"
    FOOTER = "footer"


def opening_tag(tag_type: TagType | str, data: dict[str, Any] | None = None) -> str:
    """Generate an opening comment tag.

    Args:
        tag_type: The tag type name.
        data: Optional JSON-serializable dict to include in the tag.

    Returns:
        ``<!-- type: {json} -->`` or ``<!-- type -->`` when *data* is None/empty.
    """
    tag = str(tag_type)
    if data:
        json_str = json.dumps(data, separators=(",", ": "), ensure_ascii=False)
        return f"<!-- {tag}: {json_str} -->"
    return f"<!-- {tag} -->"


def closing_tag(tag_type: TagType | str) -> str:
    """Generate a closing comment tag: ``<!-- /type -->``."""
    return f"<!-- /{tag_type} -->"


def wrap_tag(
    tag_type: TagType | str,
    content: str,
    data: dict[str, Any] | None = None,
) -> str:
    """Wrap *content* in an opening/closing comment tag pair.

    Returns:
        ``<!-- type: {json} -->content<!-- /type -->``
    """
    return f"{opening_tag(tag_type, data)}{content}{closing_tag(tag_type)}"


def self_closing_tag(tag_type: TagType | str, data: dict[str, Any] | None = None) -> str:
    """Generate a self-closing comment tag (alias for :func:`opening_tag`).

    Used for structural markers with no visible content (page breaks, etc.).
    """
    return opening_tag(tag_type, data)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_OPEN_RE = re.compile(
    r"<!--\s*"
    r"(?P<type>[a-z][a-z0-9-]*)"
    r"(?::\s*(?P<json>\{.*?\}))?"
    r"\s*-->",
)

_CLOSE_RE = re.compile(
    r"<!--\s*/(?P<type>[a-z][a-z0-9-]*)\s*-->",
)


class ParsedTag:
    """A parsed comment tag extracted from markdown text."""

    __slots__ = ("tag_type", "data", "content", "start", "end")

    def __init__(
        self,
        tag_type: str,
        data: dict[str, Any] | None,
        content: str | None,
        start: int,
        end: int,
    ) -> None:
        self.tag_type = tag_type
        self.data = data
        self.content = content
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return (
            f"ParsedTag(type={self.tag_type!r}, data={self.data!r}, "
            f"content={self.content!r}, span=({self.start}, {self.end}))"
        )


def parse_tags(text: str) -> list[ParsedTag]:
    """Extract all comment tags from *text*.

    Returns both wrapping tags (with content between open/close) and
    self-closing tags (opening tag with no corresponding close).

    Note: same-type tags are assumed not to nest.  Behaviour is undefined
    for inputs like ``<!-- style --><!-- style -->inner<!-- /style -->
    outer<!-- /style -->`` — the inner opening tag will be consumed as
    content of the first match.
    """
    tags: list[ParsedTag] = []
    used_closes: set[int] = set()

    for open_m in _OPEN_RE.finditer(text):
        tag_type = open_m.group("type")
        json_str = open_m.group("json")
        data = json.loads(json_str) if json_str else None

        close_pattern = re.compile(
            r"<!--\s*/" + re.escape(tag_type) + r"\s*-->",
        )
        close_m = close_pattern.search(text, open_m.end())

        if close_m and close_m.start() not in used_closes:
            used_closes.add(close_m.start())
            content = text[open_m.end() : close_m.start()]
            tags.append(ParsedTag(tag_type, data, content, open_m.start(), close_m.end()))
        else:
            tags.append(ParsedTag(tag_type, data, None, open_m.start(), open_m.end()))

    return tags
