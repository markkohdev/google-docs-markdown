"""ImageHandler — ``![alt](contentUri)``."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.handlers.base import ElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import InlineObject


class ImageHandler(ElementHandler):
    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "inlineObjectElement") and element.inlineObjectElement is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        obj = element.inlineObjectElement
        if not obj.inlineObjectId or not ctx.inline_objects:
            return None

        raw = ctx.inline_objects.get(obj.inlineObjectId)
        if raw is None:
            return None

        inline_obj = raw if isinstance(raw, InlineObject) else InlineObject.model_validate(raw)

        props = inline_obj.inlineObjectProperties
        if not props or not props.embeddedObject:
            return None

        embedded = props.embeddedObject
        image_props = embedded.imageProperties
        if not image_props or not image_props.contentUri:
            return None

        alt = embedded.description or embedded.title or ""
        return f"![{alt}]({image_props.contentUri})"

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
