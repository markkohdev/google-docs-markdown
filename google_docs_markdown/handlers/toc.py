"""TableOfContentsHandler — ``<!-- table-of-contents -->``."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, opening_tag
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class TableOfContentsHandler(TagElementHandler):
    TAG_TYPE = TagType.TABLE_OF_CONTENTS

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "tableOfContents") and element.tableOfContents is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return opening_tag(TagType.TABLE_OF_CONTENTS)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        from google_docs_markdown.models.common import Location
        from google_docs_markdown.models.requests import InsertTextRequest, Request

        text = "[TOC]\n"
        req = Request(
            insertText=InsertTextRequest(
                text=text,
                location=Location(
                    index=ctx.index,
                    segmentId=ctx.segment_id or None,
                    tabId=ctx.tab_id or None,
                ),
            )
        )
        ctx.advance(len(text))
        return [req]
