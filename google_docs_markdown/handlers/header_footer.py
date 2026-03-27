"""HeaderHandler / FooterHandler — header and footer block serialization."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.block_grouper import group_elements
from google_docs_markdown.comment_tags import TagType, closing_tag, opening_tag
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import Footer, Header, Location
from google_docs_markdown.models.requests import (
    CreateFooterRequest,
    CreateHeaderRequest,
    Request,
)


class HeaderHandler(TagElementHandler):
    TAG_TYPE = TagType.HEADER

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    @staticmethod
    def serialize_headers(headers: dict[str, Any] | None, ctx: SerContext) -> list[str]:
        """Serialize document headers as comment-wrapped blocks."""
        if not headers or ctx.visit_block is None:
            return []
        result: list[str] = []
        for header_id, raw in sorted(headers.items()):
            header = raw if isinstance(raw, Header) else Header.model_validate(raw)
            if not header.content:
                continue
            blocks = group_elements(header.content)
            parts: list[str] = []
            for block in blocks:
                r = ctx.visit_block(block)
                if r is not None and r.strip():
                    parts.append(r)
            if parts:
                inner = "\n\n".join(parts)
                data: dict[str, Any] = {"id": header_id}
                result.append(f"{opening_tag(TagType.HEADER, data)}\n{inner}\n{closing_tag(TagType.HEADER)}")
        return result

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        # Emit a CreateHeaderRequest targeting the leading section break (index 0).
        # Inserting content into the header requires a two-pass approach: the
        # header ID is only known after the API responds to this request, so
        # content InsertTextRequests must be issued in a subsequent batch.
        req = Request(
            createHeader=CreateHeaderRequest(
                type="DEFAULT",
                sectionBreakLocation=Location(
                    index=0,
                    segmentId=ctx.segment_id or None,
                    tabId=ctx.tab_id or None,
                ),
            )
        )
        return [req]


class FooterHandler(TagElementHandler):
    TAG_TYPE = TagType.FOOTER

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    @staticmethod
    def serialize_footers(footers: dict[str, Any] | None, ctx: SerContext) -> list[str]:
        """Serialize document footers as comment-wrapped blocks."""
        if not footers or ctx.visit_block is None:
            return []
        result: list[str] = []
        for footer_id, raw in sorted(footers.items()):
            footer = raw if isinstance(raw, Footer) else Footer.model_validate(raw)
            if not footer.content:
                continue
            blocks = group_elements(footer.content)
            parts: list[str] = []
            for block in blocks:
                r = ctx.visit_block(block)
                if r is not None and r.strip():
                    parts.append(r)
            if parts:
                inner = "\n\n".join(parts)
                data: dict[str, Any] = {"id": footer_id}
                result.append(f"{opening_tag(TagType.FOOTER, data)}\n{inner}\n{closing_tag(TagType.FOOTER)}")
        return result

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        # Emit a CreateFooterRequest targeting the leading section break (index 0).
        # Same two-pass caveat as HeaderHandler: content insertion requires
        # the footer ID returned by the API response.
        req = Request(
            createFooter=CreateFooterRequest(
                type="DEFAULT",
                sectionBreakLocation=Location(
                    index=0,
                    segmentId=ctx.segment_id or None,
                    tabId=ctx.tab_id or None,
                ),
            )
        )
        return [req]
