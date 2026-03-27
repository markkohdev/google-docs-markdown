"""RichLinkHandler — ``[title](uri)`` with optional ``<!-- rich-link -->`` wrapper."""

from __future__ import annotations

import re
from typing import Any

from google_docs_markdown.comment_tags import TagType, wrap_tag
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import Link, Location, Range
from google_docs_markdown.models.requests import (
    InsertTextRequest,
    Request,
    UpdateTextStyleRequest,
)
from google_docs_markdown.models.styles import TextStyle

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


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
        content = getattr(token, "content", "") or ""
        m = _LINK_RE.search(content)
        if not m:
            return []
        title = m.group(1)
        url = m.group(2)
        if not title or not url:
            return []

        start_index = ctx.index
        requests: list[Any] = [
            Request(
                insertText=InsertTextRequest(
                    text=title,
                    location=Location(
                        index=start_index,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                )
            ),
            Request(
                updateTextStyle=UpdateTextStyleRequest(
                    range=Range(
                        startIndex=start_index,
                        endIndex=start_index + len(title),
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                    textStyle=TextStyle(link=Link(url=url)),
                    fields="link",
                )
            ),
        ]
        ctx.advance(len(title))
        return requests
