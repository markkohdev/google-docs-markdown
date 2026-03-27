"""Inline format handlers — bold, italic, strikethrough, underline, inline code.

These compose/stack rather than standing alone.  The orchestrator applies
matching handlers as a composition on ``TextRun`` content.
"""

from __future__ import annotations

from typing import Any

from google_docs_markdown.element_registry import INLINE_CODE_COLOR, MONOSPACE_FONT
from google_docs_markdown.handlers.base import InlineFormatHandler
from google_docs_markdown.handlers.context import SerContext
from google_docs_markdown.models.styles import TextStyle


class BoldHandler(InlineFormatHandler):
    MARKER = "**"
    STYLE_FIELD = "bold"

    def serialize_match(self, element: Any) -> bool:
        if isinstance(element, TextStyle):
            return bool(element.bold)
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None


class ItalicHandler(InlineFormatHandler):
    MARKER = "*"
    STYLE_FIELD = "italic"

    def serialize_match(self, element: Any) -> bool:
        if isinstance(element, TextStyle):
            return bool(element.italic)
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None


class StrikethroughHandler(InlineFormatHandler):
    MARKER = "~~"
    STYLE_FIELD = "strikethrough"

    def serialize_match(self, element: Any) -> bool:
        if isinstance(element, TextStyle):
            return bool(element.strikethrough)
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None


class UnderlineHandler(InlineFormatHandler):
    MARKER = "<u>"
    STYLE_FIELD = "underline"

    def serialize_match(self, element: Any) -> bool:
        if isinstance(element, TextStyle):
            return bool(element.underline)
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None


class InlineCodeHandler(InlineFormatHandler):
    MARKER = "`"
    STYLE_FIELD = "inline_code"

    FONT = MONOSPACE_FONT
    COLOR = INLINE_CODE_COLOR

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    @classmethod
    def is_inline_code_style(cls, style: TextStyle | None) -> bool:
        """Check if a TextStyle represents Google Docs' inline code styling."""
        if not style:
            return False
        has_mono = bool(style.weightedFontFamily and style.weightedFontFamily.fontFamily == cls.FONT)
        from google_docs_markdown.handlers.context import optional_color_to_hex

        fg = optional_color_to_hex(style.foregroundColor)
        return has_mono and fg == cls.COLOR
