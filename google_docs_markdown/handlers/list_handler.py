"""ListHandler — ordered, unordered, and nested lists."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.block_grouper import ListBlock
from google_docs_markdown.handlers.base import BlockElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class ListHandler(BlockElementHandler):
    def serialize_match(self, element: Any) -> bool:
        return isinstance(element, ListBlock)

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        block: ListBlock = element
        if ctx.collect_paragraph_text is None:
            return None
        lines: list[str] = []
        for item in block.items:
            text = ctx.collect_paragraph_text(item.paragraph.elements or [])
            indent = "    " * item.nesting_level
            marker = "1." if item.is_ordered else "-"
            lines.append(f"{indent}{marker} {text}")
        return "\n".join(lines)

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
