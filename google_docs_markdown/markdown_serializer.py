"""Markdown serializer for Google Docs Pydantic models.

Slim orchestrator that walks the ``DocumentTab`` Pydantic tree and delegates
element-level serialization to per-element handlers via
:class:`~google_docs_markdown.handlers.registry.HandlerRegistry`.

Handles:
- Document structure traversal (body, paragraphs, blocks)
- Paragraph text collection with style segment merging
- Heading / subtitle / normal paragraph formatting
- Footnote definitions, headers, footers, embedded metadata block
- Paragraph joining and whitespace normalization
"""

from __future__ import annotations

import re
from typing import Any

from google_docs_markdown.block_grouper import (
    Block,
    CodeBlock,
    ListBlock,
    group_elements,
)
from google_docs_markdown.comment_tags import TagType, wrap_tag
from google_docs_markdown.element_registry import DEFAULT_LINK_COLOR
from google_docs_markdown.handlers.context import DocumentContext, SerContext
from google_docs_markdown.handlers.header_footer import FooterHandler, HeaderHandler
from google_docs_markdown.handlers.heading import HeadingHandler
from google_docs_markdown.handlers.registry import HandlerRegistry
from google_docs_markdown.metadata import serialize_metadata
from google_docs_markdown.models.common import Footnote
from google_docs_markdown.models.document import DocumentTab
from google_docs_markdown.models.elements import (
    ParagraphElement,
    StructuralElement,
)
from google_docs_markdown.source_map import SourceMap, SourceMapBuilder, SpanKind


class MarkdownSerializer:
    """Serialize a DocumentTab Pydantic model into Markdown text.

    Traverses DocumentTab -> Body -> StructuralElement -> Paragraph ->
    ParagraphElement -> TextRun, delegating to per-element handlers.
    """

    def __init__(self) -> None:
        self._registry = HandlerRegistry.default()
        self._heading_handler = HeadingHandler()

    def serialize(
        self,
        document_tab: DocumentTab,
        *,
        document_id: str | None = None,
        tab_id: str | None = None,
    ) -> str:
        """Convert a DocumentTab to Markdown.

        Args:
            document_tab: The DocumentTab Pydantic model to serialize.
            document_id: Optional document ID to embed in the metadata block.
            tab_id: Optional tab ID to embed in the metadata block.

        Returns:
            Markdown text ending with a single trailing newline.
            Returns empty string for documents with no content.
        """
        if not document_tab.body or not document_tab.body.content:
            return ""

        doc_ctx = DocumentContext.from_document_tab(document_tab, document_id=document_id, tab_id=tab_id)
        ctx = SerContext(
            doc=doc_ctx,
            inline_objects=document_tab.inlineObjects,
            document_id=document_id,
            tab_id=tab_id,
            body_content=document_tab.body.content,
            lists_context=document_tab.lists,
        )
        ctx.collect_paragraph_text = lambda elems: self._collect_paragraph_text(elems, ctx)
        ctx.visit_block = lambda block: self._visit_block(block, ctx)

        blocks = group_elements(document_tab.body.content, document_tab.lists)

        paragraphs: list[str] = []
        for block in blocks:
            result = self._visit_block(block, ctx)
            if result is not None:
                paragraphs.append(result)

        footnote_defs = self._serialize_footnotes(document_tab.footnotes, ctx)
        if footnote_defs:
            paragraphs.extend(footnote_defs)

        header_blocks = HeaderHandler.serialize_headers(document_tab.headers, ctx)
        footer_blocks = FooterHandler.serialize_footers(document_tab.footers, ctx)
        metadata_block = self._build_metadata_block(document_tab, ctx)

        all_parts = paragraphs + header_blocks + footer_blocks
        if metadata_block:
            all_parts.append(metadata_block)
        return _join_paragraphs(all_parts)

    def serialize_with_source_map(
        self,
        document_tab: DocumentTab,
        *,
        document_id: str | None = None,
        tab_id: str | None = None,
    ) -> tuple[str, SourceMap]:
        """Serialize and return both the Markdown text and a source map.

        The source map records which Markdown character ranges correspond
        to which Google Docs API indices, enabling the diff engine to
        generate surgical ``batchUpdate`` requests.
        """
        if not document_tab.body or not document_tab.body.content:
            return "", SourceMapBuilder(tab_id=tab_id or "", segment_id="").build()

        builder = SourceMapBuilder(tab_id=tab_id or "", segment_id="")

        doc_ctx = DocumentContext.from_document_tab(document_tab, document_id=document_id, tab_id=tab_id)
        ctx = SerContext(
            doc=doc_ctx,
            inline_objects=document_tab.inlineObjects,
            document_id=document_id,
            tab_id=tab_id,
            body_content=document_tab.body.content,
            lists_context=document_tab.lists,
            source_map=builder,
        )
        ctx.collect_paragraph_text = lambda elems: self._collect_paragraph_text(elems, ctx)
        ctx.visit_block = lambda block: self._visit_block(block, ctx)

        blocks = group_elements(document_tab.body.content, document_tab.lists)

        paragraphs: list[str] = []
        for block in blocks:
            result = self._visit_block(block, ctx)
            if result is not None:
                paragraphs.append(result)

        footnote_defs = self._serialize_footnotes(document_tab.footnotes, ctx)
        if footnote_defs:
            paragraphs.extend(footnote_defs)

        header_blocks = HeaderHandler.serialize_headers(document_tab.headers, ctx)
        footer_blocks = FooterHandler.serialize_footers(document_tab.footers, ctx)
        metadata_block = self._build_metadata_block(document_tab, ctx)

        all_parts = paragraphs + header_blocks + footer_blocks
        if metadata_block:
            all_parts.append(metadata_block)

        markdown = _join_paragraphs(all_parts)

        self._record_structural_spans(builder, document_tab, markdown)

        return markdown, builder.build()

    def _record_structural_spans(self, builder: SourceMapBuilder, document_tab: DocumentTab, markdown: str) -> None:
        """Walk body content and record coarse structural spans.

        This post-pass maps top-level structural elements to their Markdown
        positions using the API ``startIndex``/``endIndex`` values.
        """
        if not document_tab.body or not document_tab.body.content:
            return

        for element in document_tab.body.content:
            api_start = element.startIndex
            api_end = element.endIndex
            if api_start is None or api_end is None:
                continue

            kind = SpanKind.TEXT
            if element.paragraph and element.paragraph.paragraphStyle:
                style_type = element.paragraph.paragraphStyle.namedStyleType
                if style_type and style_type.startswith("HEADING"):
                    kind = SpanKind.HEADING
            elif element.table:
                kind = SpanKind.TABLE_CELL
            elif element.sectionBreak:
                continue

            builder.record(
                "",
                api_start=api_start,
                api_end=api_end,
                kind=kind,
                handler_type="structural",
            )

    # ------------------------------------------------------------------
    # Block / structural element dispatch
    # ------------------------------------------------------------------

    def _visit_block(self, block: Block, ctx: SerContext) -> str | None:
        handler = self._registry.match_block(block)
        if handler:
            return handler.serialize(block, ctx)
        if isinstance(block, (ListBlock, CodeBlock)):
            return None
        return self._visit_structural_element(block, ctx)

    def _visit_structural_element(self, element: StructuralElement, ctx: SerContext) -> str | None:
        handler = self._registry.match_structural(element)
        if handler:
            return handler.serialize(element, ctx)
        if element.paragraph:
            return self._visit_paragraph(element, ctx)
        return None

    # ------------------------------------------------------------------
    # Paragraph processing
    # ------------------------------------------------------------------

    def _visit_paragraph(self, element: StructuralElement, ctx: SerContext) -> str:
        paragraph = element.paragraph
        assert paragraph is not None
        style_type = None
        if paragraph.paragraphStyle:
            style_type = paragraph.paragraphStyle.namedStyleType

        ctx.current_para_style = style_type
        text = self._collect_paragraph_text(paragraph.elements or [], ctx)
        ctx.current_para_style = None

        return self._heading_handler.format_paragraph(text, style_type, ctx)

    def _collect_paragraph_text(self, elements: list[ParagraphElement], ctx: SerContext) -> str:
        """Concatenate and format inline text from paragraph elements.

        Style wrapping is deferred to this level so adjacent text runs
        sharing the same non-default style can be merged into a single tag.
        """
        segments: list[tuple[str, dict[str, Any] | None]] = []
        for element in elements:
            ctx.pending_style_props = None
            handler = self._registry.match_paragraph_element(element)
            if handler:
                result = handler.serialize(element, ctx)
            else:
                result = None
            if result is not None:
                segments.append((result, ctx.pending_style_props))

        merged = _merge_style_segments(segments)

        parts: list[str] = []
        for content, style_props in merged:
            if style_props:
                parts.append(wrap_tag(TagType.STYLE, content.rstrip(), style_props))
            else:
                parts.append(content)

        text = "".join(parts)
        return text.rstrip()

    # ------------------------------------------------------------------
    # Footnotes
    # ------------------------------------------------------------------

    def _serialize_footnotes(self, footnotes: dict[str, Any] | None, ctx: SerContext) -> list[str]:
        if not ctx.footnote_refs or not footnotes:
            return []

        defs: list[str] = []
        for footnote_id, footnote_number in ctx.footnote_refs:
            raw = footnotes.get(footnote_id)
            if raw is None:
                continue
            footnote = raw if isinstance(raw, Footnote) else Footnote.model_validate(raw)
            content_parts: list[str] = []
            for element in footnote.content or []:
                result = self._visit_structural_element(element, ctx)
                if result is not None and result.strip():
                    content_parts.append(result.strip())
            if content_parts:
                first, *rest = content_parts
                lines = [f"[^{footnote_number}]: {first}"]
                for part in rest:
                    lines.append(f"    {part}")
                defs.append("\n".join(lines))

        return defs

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _build_metadata_block(self, document_tab: DocumentTab, ctx: SerContext) -> str | None:
        doc = ctx.doc
        default_styles: dict[str, Any] = {}
        if doc.default_font:
            default_styles["font"] = doc.default_font
        if doc.default_font_size is not None:
            default_styles["fontSize"] = doc.default_font_size
        if doc.default_fg_color != "#000000":
            default_styles["fgColor"] = doc.default_fg_color

        heading_styles: dict[str, dict[str, Any]] = {}
        for style_name in (
            "TITLE",
            "SUBTITLE",
            "HEADING_1",
            "HEADING_2",
            "HEADING_3",
            "HEADING_4",
            "HEADING_5",
            "HEADING_6",
        ):
            entry: dict[str, Any] = {}
            if style_name in doc.named_style_sizes:
                entry["fontSize"] = doc.named_style_sizes[style_name]
            color = doc.named_style_colors.get(style_name)
            if color:
                entry["color"] = color
            font = doc.named_style_fonts.get(style_name)
            if font and font != doc.default_font:
                entry["font"] = font
            if entry:
                heading_styles[style_name] = entry

        if heading_styles:
            default_styles["headingStyles"] = heading_styles

        if doc.default_link_color != DEFAULT_LINK_COLOR:
            default_styles["linkColor"] = doc.default_link_color

        if ctx.date_defaults:
            default_styles["dateDefaults"] = ctx.date_defaults

        if not default_styles and not ctx.document_id and not ctx.tab_id:
            return None

        return serialize_metadata(
            document_id=ctx.document_id,
            tab_id=ctx.tab_id,
            default_styles=default_styles or None,
        )


# ------------------------------------------------------------------
# Utility functions (kept here for backward compatibility with tests)
# ------------------------------------------------------------------


def _optional_color_to_hex(color: Any) -> str | None:
    """Convert an OptionalColor to hex. Re-exported from context module."""
    from google_docs_markdown.handlers.context import optional_color_to_hex

    return optional_color_to_hex(color)


def _merge_style_segments(
    segments: list[tuple[str, dict[str, Any] | None]],
) -> list[tuple[str, dict[str, Any] | None]]:
    """Merge adjacent paragraph segments that share identical style props."""
    if len(segments) <= 1:
        return segments

    result: list[tuple[str, dict[str, Any] | None]] = []
    i = 0
    while i < len(segments):
        content, props = segments[i]
        if props is None:
            result.append((content, props))
            i += 1
            continue

        group_content = content
        group_props = props
        i += 1

        while i < len(segments):
            next_content, next_props = segments[i]
            if next_props == group_props:
                group_content += next_content
                i += 1
            elif (
                next_props is None
                and next_content.strip() == ""
                and i + 1 < len(segments)
                and segments[i + 1][1] == group_props
            ):
                group_content += next_content
                i += 1
            else:
                break

        result.append((group_content, group_props))

    return result


def _is_inline_code_style(style: Any) -> bool:
    """Re-exported for backward compatibility."""
    from google_docs_markdown.handlers.inline_format import InlineCodeHandler

    return InlineCodeHandler.is_inline_code_style(style)


def _split_whitespace(text: str) -> tuple[str, str, str]:
    """Split *text* into ``(leading_ws, inner, trailing_ws)``."""
    from google_docs_markdown.handlers.text_run import (
        _split_whitespace as _sw,
    )

    return _sw(text)


def _apply_backtick_wrap(text: str) -> str:
    """Re-exported for backward compatibility."""
    from google_docs_markdown.handlers.text_run import (
        _apply_backtick_wrap as _bw,
    )

    return _bw(text)


def _escape_pipe(text: str) -> str:
    """Escape literal pipe characters."""
    return text.replace("|", "\\|")


def _apply_inline_formatting(
    text: str,
    *,
    bold: bool,
    italic: bool,
    strikethrough: bool = False,
    underline: bool = False,
) -> str:
    """Wrap text in Markdown formatting markers, preserving surrounding whitespace."""
    from google_docs_markdown.handlers.text_run import (
        _apply_inline_formatting as _aif,
    )

    return _aif(
        text,
        bold=bold,
        italic=italic,
        strikethrough=strikethrough,
        underline=underline,
    )


def _apply_link(text: str, url: str) -> str:
    """Wrap text in a Markdown link, preserving surrounding whitespace."""
    from google_docs_markdown.handlers.text_run import _apply_link as _al

    return _al(text, url)


def _join_paragraphs(paragraphs: list[str]) -> str:
    """Join serialized paragraphs with blank-line separation.

    Runs of three or more consecutive newlines are collapsed to exactly two.
    The result always ends with a single trailing newline.
    """
    if not paragraphs:
        return ""
    result = "\n\n".join(paragraphs)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.rstrip("\n") + "\n"
