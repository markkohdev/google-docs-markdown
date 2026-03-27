"""HeadingHandler — heading, title, and subtitle paragraph formatting."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, opening_tag
from google_docs_markdown.element_registry import HEADING_PREFIX
from google_docs_markdown.handlers.base import BlockElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class HeadingHandler(BlockElementHandler):
    """Formats paragraph text into headings, title, and subtitle."""

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    def format_paragraph(self, text: str, style_type: str | None, ctx: SerContext) -> str:
        """Apply heading/subtitle formatting to paragraph text.

        Called by the orchestrator after collecting paragraph text.
        """
        heading_prefix = HEADING_PREFIX.get(style_type or "")
        if heading_prefix and text:
            rendered = f"{heading_prefix} {text}"
            if style_type == "TITLE":
                return f"{opening_tag(TagType.TITLE)}\n{rendered}"
            return rendered

        if style_type == "SUBTITLE" and text:
            return f"{opening_tag(TagType.SUBTITLE)}\n*{text}*"

        return text

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
