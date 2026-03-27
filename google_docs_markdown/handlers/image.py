"""ImageHandler — ``![alt](contentUri)``."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, self_closing_tag
from google_docs_markdown.handlers.base import ElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import InlineObject

_DEFAULT_MARGIN_PT = 9.0


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
        md = f"![{alt}]({image_props.contentUri})"

        tag_data = _build_image_props_data(embedded, image_props)
        if tag_data:
            md += self_closing_tag(TagType.IMAGE_PROPS, tag_data)

        return md

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        from google_docs_markdown.models.common import Location
        from google_docs_markdown.models.requests import InsertInlineImageRequest, Request

        src = getattr(token, "src", None) or (getattr(token, "attrs", None) or {}).get("src")
        if not src:
            return []
        return [
            Request(
                insertInlineImage=InsertInlineImageRequest(
                    uri=src,
                    location=Location(
                        index=ctx.index,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                )
            )
        ]


def _build_image_props_data(
    embedded: Any,
    image_props: Any,
) -> dict[str, Any] | None:
    """Build a dict of non-default image properties for the comment tag.

    Returns ``None`` when all properties are at their defaults (9 PT margins,
    no cropping, no explicit size).
    """
    data: dict[str, Any] = {}

    if embedded.size:
        if embedded.size.width and embedded.size.width.magnitude is not None:
            data["width"] = embedded.size.width.magnitude
        if embedded.size.height and embedded.size.height.magnitude is not None:
            data["height"] = embedded.size.height.magnitude

    crop = image_props.cropProperties
    if crop:
        crop_data: dict[str, float] = {}
        for field in ("offsetTop", "offsetBottom", "offsetLeft", "offsetRight", "angle"):
            val = getattr(crop, field, None)
            if val is not None and val != 0:
                crop_data[field] = val
        if crop_data:
            data["crop"] = crop_data

    margins: dict[str, float] = {}
    for field in ("marginTop", "marginBottom", "marginLeft", "marginRight"):
        dim = getattr(embedded, field, None)
        if dim and dim.magnitude is not None and dim.magnitude != _DEFAULT_MARGIN_PT:
            margins[field] = dim.magnitude
    if margins:
        data["margins"] = margins

    return data or None
