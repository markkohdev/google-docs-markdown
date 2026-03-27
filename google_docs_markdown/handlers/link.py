"""LinkHandler — ``[text](url)`` hyperlinks."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.handlers.base import ElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class LinkHandler(ElementHandler):
    """Provides link knowledge for both serialization and deserialization.

    For serialization, the orchestrator uses link detection on TextStyle.
    The handler is primarily used for deserialization dispatch.
    """

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
