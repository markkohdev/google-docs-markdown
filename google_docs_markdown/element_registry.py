"""Shared constants for Google Docs ↔ Markdown element conversion.

Centralizes magic values used by both serialization handlers and the
deserialization orchestrator so they stay in sync.
"""

from __future__ import annotations

from enum import StrEnum

# ---------------------------------------------------------------------------
# Heading / paragraph style mappings
# ---------------------------------------------------------------------------

HEADING_PREFIX: dict[str, str] = {
    "TITLE": "#",
    "HEADING_1": "#",
    "HEADING_2": "##",
    "HEADING_3": "###",
    "HEADING_4": "####",
    "HEADING_5": "#####",
    "HEADING_6": "######",
}

HEADING_STYLES = frozenset(
    {"TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6"}
)

MD_HEADING_LEVEL_TO_STYLE: dict[int, str] = {
    1: "HEADING_1",
    2: "HEADING_2",
    3: "HEADING_3",
    4: "HEADING_4",
    5: "HEADING_5",
    6: "HEADING_6",
}

# ---------------------------------------------------------------------------
# List glyph types
# ---------------------------------------------------------------------------

ORDERED_GLYPH_TYPES = frozenset({"DECIMAL", "ZERO_DECIMAL", "UPPER_ALPHA", "ALPHA", "UPPER_ROMAN", "ROMAN"})

# ---------------------------------------------------------------------------
# Code / monospace constants
# ---------------------------------------------------------------------------

CODE_BLOCK_MARKER = "\ue907"
MONOSPACE_FONT = "Roboto Mono"
MONOSPACE_FONTS = frozenset({"Roboto Mono", "Courier New", "Consolas", "Source Code Pro"})
INLINE_CODE_COLOR = "#188037"

# ---------------------------------------------------------------------------
# Inline formatting markers (Markdown delimiter → TextStyle field)
# ---------------------------------------------------------------------------


class InlineMarker(StrEnum):
    """Markdown inline formatting delimiters."""

    BOLD = "**"
    ITALIC = "*"
    STRIKETHROUGH = "~~"
    UNDERLINE = "<u>"
    INLINE_CODE = "`"


INLINE_MARKER_TO_STYLE_FIELD: dict[str, str] = {
    InlineMarker.BOLD: "bold",
    InlineMarker.ITALIC: "italic",
    InlineMarker.STRIKETHROUGH: "strikethrough",
    InlineMarker.UNDERLINE: "underline",
    InlineMarker.INLINE_CODE: "inline_code",
}

# ---------------------------------------------------------------------------
# Default link color (Google Docs standard)
# ---------------------------------------------------------------------------

DEFAULT_LINK_COLOR = "#1155CC"

# ---------------------------------------------------------------------------
# Comment-tag type → batchUpdate request field mapping
# ---------------------------------------------------------------------------

TAG_TO_REQUEST_FIELD: dict[str, str] = {
    "person": "insertPerson",
    "date": "insertDate",
    "page-break": "insertPageBreak",
    "section-break": "insertSectionBreak",
    "table-of-contents": "insertText",
    "auto-text": "insertText",
    "equation": "insertText",
    "column-break": "insertText",
    "style": "updateTextStyle",
    "suggestion": "insertText",
    "rich-link": "insertText",
}
