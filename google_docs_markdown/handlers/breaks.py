"""Break and opaque element handlers.

Covers HorizontalRule, PageBreak, ColumnBreak, SectionBreak, AutoText, Equation,
and ChipPlaceholder — all rendered as self-closing or opening comment tags.
"""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, opening_tag
from google_docs_markdown.handlers.base import ElementHandler, TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import Location
from google_docs_markdown.models.requests import (
    InsertPageBreakRequest,
    InsertSectionBreakRequest,
    InsertTextRequest,
    Request,
)


class HorizontalRuleHandler(ElementHandler):
    """HR produces ``---``, not a comment tag — extends ElementHandler directly."""

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "horizontalRule") and element.horizontalRule is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return "---"

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []


class PageBreakHandler(TagElementHandler):
    TAG_TYPE = TagType.PAGE_BREAK

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "pageBreak") and element.pageBreak is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return opening_tag(TagType.PAGE_BREAK)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        req = Request(
            insertPageBreak=InsertPageBreakRequest(
                location=Location(
                    index=ctx.index,
                    segmentId=ctx.segment_id or None,
                    tabId=ctx.tab_id or None,
                )
            )
        )
        ctx.advance(1)
        return [req]


class ColumnBreakHandler(TagElementHandler):
    TAG_TYPE = TagType.COLUMN_BREAK

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "columnBreak") and element.columnBreak is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return opening_tag(TagType.COLUMN_BREAK)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        req = Request(
            insertText=InsertTextRequest(
                text="\v",
                location=Location(
                    index=ctx.index,
                    segmentId=ctx.segment_id or None,
                    tabId=ctx.tab_id or None,
                ),
            )
        )
        ctx.advance(1)
        return [req]


class SectionBreakHandler(TagElementHandler):
    TAG_TYPE = TagType.SECTION_BREAK

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "sectionBreak") and element.sectionBreak is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        is_leading = element.startIndex is None or element.startIndex == 0
        is_trailing = False
        if ctx.body_content and element is ctx.body_content[-1]:
            is_trailing = True
        if is_leading or is_trailing:
            return None
        sb = element.sectionBreak
        if not sb:
            return None
        data: dict[str, Any] = {}
        if sb.sectionStyle and sb.sectionStyle.sectionType:
            data["type"] = sb.sectionStyle.sectionType
        return opening_tag(TagType.SECTION_BREAK, data or None)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        data = getattr(token, "data", None) or {}
        section_type = data.get("type", "NEXT_PAGE")
        req = Request(
            insertSectionBreak=InsertSectionBreakRequest(
                location=Location(
                    index=ctx.index,
                    segmentId=ctx.segment_id or None,
                    tabId=ctx.tab_id or None,
                ),
                sectionType=section_type,
            )
        )
        ctx.advance(1)
        return [req]


class AutoTextHandler(TagElementHandler):
    TAG_TYPE = TagType.AUTO_TEXT

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "autoText") and element.autoText is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        auto_text = element.autoText
        data: dict[str, Any] = {}
        if auto_text.type:
            data["type"] = auto_text.type
        return opening_tag(TagType.AUTO_TEXT, data or None)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []


class EquationHandler(TagElementHandler):
    TAG_TYPE = TagType.EQUATION

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "equation") and element.equation is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return opening_tag(TagType.EQUATION)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
