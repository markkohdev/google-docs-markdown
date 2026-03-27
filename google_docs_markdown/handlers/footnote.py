"""FootnoteRefHandler — ``[^N]`` inline references."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.handlers.base import ElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class FootnoteRefHandler(ElementHandler):
    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "footnoteReference") and element.footnoteReference is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        ref = element.footnoteReference
        if not ref.footnoteNumber:
            return None
        if ref.footnoteId:
            ctx.footnote_refs.append((ref.footnoteId, ref.footnoteNumber))
        return f"[^{ref.footnoteNumber}]"

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
