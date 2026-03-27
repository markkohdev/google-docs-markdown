"""RichLinkHandler — ``[title](uri)`` with optional ``<!-- rich-link -->`` wrapper."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, wrap_tag
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class RichLinkHandler(TagElementHandler):
    TAG_TYPE = TagType.RICH_LINK

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "richLink") and element.richLink is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        rich_link = element.richLink
        props = rich_link.richLinkProperties
        if not props or not props.uri:
            return None
        title = props.title or props.uri
        link_md = f"[{title}]({props.uri})"
        meta: dict[str, Any] = {}
        if props.mimeType:
            meta["mimeType"] = props.mimeType
        if meta:
            return wrap_tag(TagType.RICH_LINK, link_md, meta)
        return link_md

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
