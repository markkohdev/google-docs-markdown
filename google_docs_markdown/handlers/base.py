"""Abstract base classes for per-element handlers.

Each handler owns both serialization (Pydantic model → Markdown) and
deserialization (Markdown → API requests) for a single element concept.

Handler categories:

* ``TagElementHandler`` — HTML comment tag elements (person, date, style, …)
* ``BlockElementHandler`` — structural blocks (heading, list, table, code)
* ``InlineFormatHandler`` — composable inline formatting (bold, italic, …)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from google_docs_markdown.comment_tags import TagType
from google_docs_markdown.handlers.context import DeserContext, SerContext


class ElementHandler(ABC):
    """Base class for all element handlers."""

    @abstractmethod
    def serialize_match(self, element: Any) -> bool:
        """Return True if this handler handles the given API element for serialization."""

    @abstractmethod
    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        """Convert an API element to Markdown text."""

    @abstractmethod
    def deserialize_match(self, token: Any) -> bool:
        """Return True if this handler handles the given Markdown token for deserialization."""

    @abstractmethod
    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        """Convert a Markdown token back to API requests."""


class TagElementHandler(ElementHandler):
    """Handler for elements serialized as ``<!-- type: {json} -->content<!-- /type -->``."""

    TAG_TYPE: TagType

    def deserialize_match(self, token: Any) -> bool:
        if hasattr(token, "tag_type"):
            return bool(token.tag_type == str(self.TAG_TYPE))
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []


class BlockElementHandler(ElementHandler):
    """Handler for structural block elements (heading, list, table, code block)."""

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []


class InlineFormatHandler(ElementHandler):
    """Handler for composable inline formatting (bold, italic, strikethrough, …).

    ``MARKER`` is the Markdown delimiter (e.g. ``**`` for bold).
    ``STYLE_FIELD`` is the ``TextStyle`` attribute name (e.g. ``"bold"``).
    """

    MARKER: str
    STYLE_FIELD: str

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
