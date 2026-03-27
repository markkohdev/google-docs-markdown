"""SuggestionHandler — ``<!-- suggestion: {...} -->text<!-- /suggestion -->``."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class SuggestionHandler(TagElementHandler):
    TAG_TYPE = TagType.SUGGESTION

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
