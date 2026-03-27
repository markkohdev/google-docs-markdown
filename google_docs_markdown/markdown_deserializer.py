"""Markdown deserializer — converts Markdown text into Google Docs API batchUpdate requests.

Parses Markdown using ``markdown-it-py``, then walks the AST token stream,
dispatching to per-element handlers via
:class:`~google_docs_markdown.handlers.registry.HandlerRegistry`.

Comment-tag annotations (``<!-- type: {json} -->content<!-- /type -->``) are
parsed separately via :func:`~google_docs_markdown.comment_tags.parse_tags`
and dispatched through the handler registry's ``match_deserialize``.

The output is a ``list[Request]`` suitable for passing to
:meth:`~google_docs_markdown.client.GoogleDocsClient.batch_update`.
"""

from __future__ import annotations

import re
from typing import Any, Literal, cast

from markdown_it import MarkdownIt
from markdown_it.token import Token

from google_docs_markdown.comment_tags import ParsedTag, parse_tags
from google_docs_markdown.element_registry import (
    INLINE_CODE_COLOR,
    MD_HEADING_LEVEL_TO_STYLE,
    MONOSPACE_FONT,
)
from google_docs_markdown.handlers.context import DeserContext, DocumentContext
from google_docs_markdown.handlers.registry import HandlerRegistry
from google_docs_markdown.metadata import parse_metadata, strip_metadata
from google_docs_markdown.models.common import (
    Color,
    Dimension,
    Link,
    Location,
    OptionalColor,
    Range,
    RgbColor,
    WeightedFontFamily,
)
from google_docs_markdown.models.requests import (
    CreateParagraphBulletsRequest,
    InsertInlineImageRequest,
    InsertPageBreakRequest,
    InsertSectionBreakRequest,
    InsertTableRequest,
    InsertTextRequest,
    Request,
    UpdateParagraphStyleRequest,
    UpdateTextStyleRequest,
)
from google_docs_markdown.models.styles import ParagraphStyle, TextStyle

_NamedStyleType = Literal[
    "NAMED_STYLE_TYPE_UNSPECIFIED",
    "NORMAL_TEXT",
    "TITLE",
    "SUBTITLE",
    "HEADING_1",
    "HEADING_2",
    "HEADING_3",
    "HEADING_4",
    "HEADING_5",
    "HEADING_6",
]

_BulletPreset = Literal[
    "BULLET_DISC_CIRCLE_SQUARE",
    "NUMBERED_DECIMAL_ALPHA_ROMAN",
]

_TITLE_TAG_RE = re.compile(r"<!--\s*title\s*-->\s*\n?")
_SUBTITLE_TAG_RE = re.compile(r"<!--\s*subtitle\s*-->\s*\n?")


class MarkdownDeserializer:
    """Deserialize Markdown text into Google Docs API requests."""

    def __init__(self) -> None:
        self._registry = HandlerRegistry.default()
        self._md = MarkdownIt().enable("strikethrough").enable("table")

    def deserialize(
        self,
        markdown_text: str,
        *,
        tab_id: str = "",
        segment_id: str = "",
    ) -> list[Request]:
        """Parse *markdown_text* and return a list of ``Request`` objects.

        Args:
            markdown_text: The Markdown source text to deserialize.
            tab_id: Target tab ID for multi-tab documents.
            segment_id: Target segment ID (body, header, footer).

        Returns:
            Ordered list of Request objects for ``batchUpdate``.
        """
        metadata = parse_metadata(markdown_text)
        doc_ctx = DocumentContext.from_metadata(metadata) if metadata else DocumentContext()

        content = strip_metadata(markdown_text) if metadata else markdown_text

        ctx = DeserContext(
            doc=doc_ctx,
            index=1,
            tab_id=tab_id or doc_ctx.tab_id or "",
            segment_id=segment_id,
        )

        self._process_content(content, ctx)
        return [r for r in ctx.requests if isinstance(r, Request)]

    def _process_content(self, content: str, ctx: DeserContext) -> None:
        """Process Markdown content via markdown-it AST and comment-tag dispatch.

        Block-level comment tags (``html_block``) and inline comment tags
        (``html_inline``) are dispatched inside ``_walk_tokens`` as
        markdown-it discovers them, so no separate tag pass is needed.
        """
        tokens = self._md.parse(content)
        self._walk_tokens(tokens, ctx)

    def _walk_tokens(self, tokens: list[Token], ctx: DeserContext) -> None:
        """Walk top-level markdown-it tokens and dispatch to handlers."""
        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                i = self._handle_heading(tokens, i, ctx)
            elif token.type == "paragraph_open":
                i = self._handle_paragraph(tokens, i, ctx)
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                i = self._handle_list(tokens, i, ctx)
            elif token.type == "fence":
                self._handle_code_fence(token, ctx)
                i += 1
            elif token.type == "table_open":
                i = self._handle_table(tokens, i, ctx)
            elif token.type == "hr":
                self._handle_hr(ctx)
                i += 1
            elif token.type == "html_block":
                self._handle_html_block(token, ctx)
                i += 1
            else:
                i += 1

    # ------------------------------------------------------------------
    # Block-level handlers
    # ------------------------------------------------------------------

    def _handle_heading(self, tokens: list[Token], start: int, ctx: DeserContext) -> int:
        """Process heading_open .. inline .. heading_close."""
        open_token = tokens[start]
        level = int(open_token.tag[1])
        style_name = cast(_NamedStyleType, MD_HEADING_LEVEL_TO_STYLE.get(level, "NORMAL_TEXT"))

        inline_token = tokens[start + 1] if start + 1 < len(tokens) else None
        text = self._extract_inline_text(inline_token) if inline_token else ""

        if text:
            insert_text = text + "\n"
            start_index = ctx.index
            self._emit_insert_text(ctx, insert_text)

            end_index = ctx.index - 1
            self._emit_paragraph_style(ctx, start_index, end_index, style_name)
            self._apply_inline_formatting_from_token(inline_token, ctx, start_index)

        return start + 3

    def _handle_paragraph(self, tokens: list[Token], start: int, ctx: DeserContext) -> int:
        """Process paragraph_open .. inline .. paragraph_close."""
        inline_token = tokens[start + 1] if start + 1 < len(tokens) else None

        if inline_token and inline_token.type == "inline":
            raw_content = inline_token.content or ""

            title_m = _TITLE_TAG_RE.match(raw_content)
            if title_m:
                remaining = raw_content[title_m.end() :]
                if remaining.startswith("# "):
                    remaining = remaining[2:]
                if remaining:
                    insert_text = remaining + "\n"
                    start_index = ctx.index
                    self._emit_insert_text(ctx, insert_text)
                    end_index = ctx.index - 1
                    self._emit_paragraph_style(ctx, start_index, end_index, "TITLE")
                return start + 3

            subtitle_m = _SUBTITLE_TAG_RE.match(raw_content)
            if subtitle_m:
                remaining = raw_content[subtitle_m.end() :]
                if remaining.startswith("*") and remaining.endswith("*"):
                    remaining = remaining[1:-1]
                if remaining:
                    insert_text = remaining + "\n"
                    start_index = ctx.index
                    self._emit_insert_text(ctx, insert_text)
                    end_index = ctx.index - 1
                    self._emit_paragraph_style(ctx, start_index, end_index, "SUBTITLE")
                return start + 3

            has_comment_tags = self._inline_has_comment_tags(inline_token)
            if has_comment_tags:
                self._handle_inline_with_tags(inline_token, ctx)
            else:
                text = self._extract_inline_text(inline_token)
                if text:
                    start_index = ctx.index
                    self._emit_insert_text(ctx, text + "\n")
                    self._apply_inline_formatting_from_token(inline_token, ctx, start_index)

        return start + 3

    def _handle_list(self, tokens: list[Token], start: int, ctx: DeserContext) -> int:
        """Process bullet_list_open/ordered_list_open .. list_item .. close."""
        is_ordered = tokens[start].type == "ordered_list_open"
        close_type = "ordered_list_close" if is_ordered else "bullet_list_close"

        items: list[tuple[str, int, Token | None]] = []
        i = start + 1
        nesting = 0
        while i < len(tokens) and tokens[i].type != close_type:
            if tokens[i].type == "list_item_open":
                item_text, item_inline, i = self._extract_list_item(tokens, i)
                items.append((item_text, nesting, item_inline))
            elif tokens[i].type in ("bullet_list_open", "ordered_list_open"):
                nesting += 1
                i += 1
            elif tokens[i].type in ("bullet_list_close", "ordered_list_close"):
                nesting = max(0, nesting - 1)
                i += 1
            else:
                i += 1

        bullet_preset: _BulletPreset = "NUMBERED_DECIMAL_ALPHA_ROMAN" if is_ordered else "BULLET_DISC_CIRCLE_SQUARE"

        for item_text, _nesting, item_inline in items:
            if item_text:
                start_index = ctx.index
                self._emit_insert_text(ctx, item_text + "\n")
                end_index = ctx.index - 1

                ctx.emit(
                    Request(
                        createParagraphBullets=CreateParagraphBulletsRequest(
                            range=Range(
                                startIndex=start_index,
                                endIndex=end_index,
                                segmentId=ctx.segment_id or None,
                                tabId=ctx.tab_id or None,
                            ),
                            bulletPreset=bullet_preset,
                        )
                    )
                )

                if item_inline:
                    self._apply_inline_formatting_from_token(item_inline, ctx, start_index)

        return i + 1

    def _extract_list_item(self, tokens: list[Token], start: int) -> tuple[str, Token | None, int]:
        """Extract text and inline token from a list item, returning the next index."""
        i = start + 1
        text = ""
        inline_token = None
        while i < len(tokens) and tokens[i].type != "list_item_close":
            if tokens[i].type == "inline":
                text = self._extract_inline_text(tokens[i])
                inline_token = tokens[i]
            elif tokens[i].type == "paragraph_open":
                pass
            elif tokens[i].type == "paragraph_close":
                pass
            i += 1
        return text, inline_token, i + 1

    def _handle_code_fence(self, token: Token, ctx: DeserContext) -> None:
        """Process a fenced code block."""
        code_text = token.content or ""
        if code_text and not code_text.endswith("\n"):
            code_text += "\n"

        start_index = ctx.index
        self._emit_insert_text(ctx, code_text)

        if code_text.strip():
            ctx.emit(
                Request(
                    updateTextStyle=UpdateTextStyleRequest(
                        range=Range(
                            startIndex=start_index,
                            endIndex=ctx.index - 1,
                            segmentId=ctx.segment_id or None,
                            tabId=ctx.tab_id or None,
                        ),
                        textStyle=TextStyle(
                            weightedFontFamily=WeightedFontFamily(fontFamily=MONOSPACE_FONT),
                            fontSize=Dimension(magnitude=10.0, unit="PT"),
                        ),
                        fields="weightedFontFamily,fontSize",
                    )
                )
            )

    def _handle_table(self, tokens: list[Token], start: int, ctx: DeserContext) -> int:
        """Process table_open .. rows .. table_close."""
        rows: list[list[str]] = []
        i = start + 1
        current_row: list[str] | None = None

        while i < len(tokens) and tokens[i].type != "table_close":
            if tokens[i].type == "tr_open":
                current_row = []
                i += 1
            elif tokens[i].type == "tr_close":
                if current_row is not None:
                    rows.append(current_row)
                current_row = None
                i += 1
            elif tokens[i].type in ("th_open", "td_open"):
                i += 1
            elif tokens[i].type in ("th_close", "td_close"):
                i += 1
            elif tokens[i].type == "inline" and current_row is not None:
                current_row.append(self._extract_inline_text(tokens[i]))
                i += 1
            elif tokens[i].type in ("thead_open", "thead_close", "tbody_open", "tbody_close"):
                i += 1
            else:
                i += 1

        if rows:
            num_rows = len(rows)
            num_cols = max(len(r) for r in rows) if rows else 1

            ctx.emit(
                Request(
                    insertTable=InsertTableRequest(
                        rows=num_rows,
                        columns=num_cols,
                        location=Location(
                            index=ctx.index,
                            segmentId=ctx.segment_id or None,
                            tabId=ctx.tab_id or None,
                        ),
                    )
                )
            )

            insert_index = ctx.index
            # InsertTable creates: 1 pre-paragraph + table body + trailing paragraph.
            # Table body = rows * (2*cols + 1) + 2 indices.
            # We advance past pre-paragraph + body; the trailing paragraph
            # becomes the insertion point for subsequent content.
            table_body_size = num_rows * (2 * num_cols + 1) + 2
            ctx.advance(1 + table_body_size)

            # Populate cells in REVERSE order so each insert doesn't shift
            # subsequent cell indices within the same batchUpdate.
            cell_inserts: list[tuple[int, str]] = []
            for row_idx, row in enumerate(rows):
                for col_idx, cell_text in enumerate(row):
                    if cell_text:
                        cell_index = insert_index + 4 + row_idx * (num_cols * 2 + 1) + col_idx * 2
                        cell_inserts.append((cell_index, cell_text))

            for cell_index, cell_text in reversed(cell_inserts):
                ctx.emit(
                    Request(
                        insertText=InsertTextRequest(
                            text=cell_text,
                            location=Location(
                                index=cell_index,
                                segmentId=ctx.segment_id or None,
                                tabId=ctx.tab_id or None,
                            ),
                        )
                    )
                )

            # Cell text inserts shift everything after the table by
            # the total length of all inserted cell content.
            total_cell_len = sum(len(text) for _, text in cell_inserts)
            ctx.advance(total_cell_len)

        return i + 1

    def _handle_hr(self, ctx: DeserContext) -> None:
        """Process horizontal rule."""
        self._emit_insert_text(ctx, "\n")

    def _handle_html_block(self, token: Token, ctx: DeserContext) -> None:
        """Process HTML block content — mainly comment tags."""
        content = (token.content or "").strip()
        tags = parse_tags(content)
        for tag in tags:
            self._dispatch_tag(tag, ctx)

    # ------------------------------------------------------------------
    # Inline comment-tag handling
    # ------------------------------------------------------------------

    def _inline_has_comment_tags(self, token: Token) -> bool:
        """Check if an inline token contains HTML comment tags."""
        if not token.children:
            return False
        return any(child.type == "html_inline" and child.content.strip().startswith("<!--") for child in token.children)

    def _handle_inline_with_tags(self, token: Token, ctx: DeserContext) -> None:
        """Process inline content that contains comment tags.

        Reassembles the raw content from inline children and dispatches
        comment tags through the handler registry.
        """
        if not token.children:
            return

        raw_parts: list[str] = []
        link_href: str | None = None
        for child in token.children:
            if child.type == "text":
                raw_parts.append(child.content)
            elif child.type == "html_inline":
                raw_parts.append(child.content)
            elif child.type in ("softbreak", "hardbreak"):
                raw_parts.append("\n")
            elif child.type == "link_open":
                link_href = str((child.attrs or {}).get("href", ""))
                raw_parts.append("[")
            elif child.type == "link_close":
                raw_parts.append(f"]({link_href})" if link_href else "]")
                link_href = None

        raw_content = "".join(raw_parts)
        if not raw_content.strip():
            return

        tags = parse_tags(raw_content)
        if not tags:
            text = self._extract_inline_text(token)
            if text:
                start_index = ctx.index
                self._emit_insert_text(ctx, text + "\n")
                self._apply_inline_formatting_from_token(token, ctx, start_index)
            return

        last_end = 0
        for tag in tags:
            before = raw_content[last_end : tag.start]
            if before.strip():
                start_index = ctx.index
                self._emit_insert_text(ctx, before)

            self._dispatch_tag(tag, ctx)
            last_end = tag.end

        after = raw_content[last_end:]
        if after.strip():
            self._emit_insert_text(ctx, after)

        self._emit_insert_text(ctx, "\n")

    # ------------------------------------------------------------------
    # Comment-tag dispatch
    # ------------------------------------------------------------------

    def _dispatch_tag(self, tag: ParsedTag, ctx: DeserContext) -> None:
        """Dispatch a single parsed tag to its handler or handle directly."""
        handler = self._registry.match_deserialize(tag)
        if handler:
            requests = handler.deserialize(tag, ctx)
            for req in requests:
                if isinstance(req, Request):
                    ctx.emit(req)
            return

        if tag.tag_type == "page-break":
            ctx.emit(
                Request(
                    insertPageBreak=InsertPageBreakRequest(
                        location=Location(
                            index=ctx.index,
                            segmentId=ctx.segment_id or None,
                            tabId=ctx.tab_id or None,
                        )
                    )
                )
            )
            ctx.advance(1)
        elif tag.tag_type == "section-break":
            section_type = (tag.data or {}).get("type", "NEXT_PAGE")
            ctx.emit(
                Request(
                    insertSectionBreak=InsertSectionBreakRequest(
                        location=Location(
                            index=ctx.index,
                            segmentId=ctx.segment_id or None,
                            tabId=ctx.tab_id or None,
                        ),
                        sectionType=section_type,
                    )
                )
            )
            ctx.advance(1)

    # ------------------------------------------------------------------
    # Inline formatting
    # ------------------------------------------------------------------

    def _extract_inline_text(self, token: Token | None) -> str:
        """Extract plain text from an inline token, stripping formatting markers."""
        if not token or not token.children:
            return token.content if token else ""
        parts: list[str] = []
        for child in token.children:
            if child.type == "text":
                parts.append(child.content)
            elif child.type == "code_inline":
                parts.append(child.content)
            elif child.type == "softbreak":
                parts.append("\n")
            elif child.type == "hardbreak":
                parts.append("\n")
            elif child.type == "image":
                pass
            elif child.type == "html_inline":
                pass
        return "".join(parts)

    def _apply_inline_formatting_from_token(self, token: Token | None, ctx: DeserContext, para_start: int) -> None:
        """Walk inline children and emit UpdateTextStyle requests for formatting."""
        if not token or not token.children:
            return

        formatting_stack: list[str] = []
        text_offset = para_start

        for child in token.children:
            if child.type == "text":
                text_len = len(child.content)
                if formatting_stack:
                    self._emit_text_style(ctx, text_offset, text_offset + text_len, formatting_stack)
                text_offset += text_len

            elif child.type == "code_inline":
                text_len = len(child.content)
                self._emit_code_inline_style(ctx, text_offset, text_offset + text_len)
                text_offset += text_len

            elif child.type in ("softbreak", "hardbreak"):
                text_offset += 1

            elif child.type == "strong_open":
                formatting_stack.append("bold")
            elif child.type == "strong_close":
                if "bold" in formatting_stack:
                    formatting_stack.remove("bold")

            elif child.type == "em_open":
                formatting_stack.append("italic")
            elif child.type == "em_close":
                if "italic" in formatting_stack:
                    formatting_stack.remove("italic")

            elif child.type == "s_open":
                formatting_stack.append("strikethrough")
            elif child.type == "s_close":
                if "strikethrough" in formatting_stack:
                    formatting_stack.remove("strikethrough")

            elif child.type == "html_inline":
                html = child.content.strip().lower()
                if html == "<u>":
                    formatting_stack.append("underline")
                elif html == "</u>":
                    if "underline" in formatting_stack:
                        formatting_stack.remove("underline")

            elif child.type == "link_open":
                url = (child.attrs or {}).get("href", "")
                formatting_stack.append(f"link:{url}")
            elif child.type == "link_close":
                formatting_stack[:] = [f for f in formatting_stack if not f.startswith("link:")]

            elif child.type == "image":
                src = str((child.attrs or {}).get("src", ""))
                if src:
                    ctx.emit(
                        Request(
                            insertInlineImage=InsertInlineImageRequest(
                                uri=src,
                                location=Location(
                                    index=text_offset,
                                    segmentId=ctx.segment_id or None,
                                    tabId=ctx.tab_id or None,
                                ),
                            )
                        )
                    )

    def _emit_text_style(self, ctx: DeserContext, start: int, end: int, formatting: list[str]) -> None:
        """Emit an UpdateTextStyleRequest for the given formatting stack."""
        if start >= end:
            return

        bold = "bold" in formatting
        italic = "italic" in formatting
        strikethrough = "strikethrough" in formatting
        underline = "underline" in formatting
        link_url = None
        for f in formatting:
            if f.startswith("link:"):
                link_url = f[5:]

        fields: list[str] = []
        style_kwargs: dict[str, Any] = {}

        if bold:
            style_kwargs["bold"] = True
            fields.append("bold")
        if italic:
            style_kwargs["italic"] = True
            fields.append("italic")
        if strikethrough:
            style_kwargs["strikethrough"] = True
            fields.append("strikethrough")
        if underline:
            style_kwargs["underline"] = True
            fields.append("underline")
        if link_url:
            style_kwargs["link"] = Link(url=link_url)
            fields.append("link")

        if not fields:
            return

        ctx.emit(
            Request(
                updateTextStyle=UpdateTextStyleRequest(
                    range=Range(
                        startIndex=start,
                        endIndex=end,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                    textStyle=TextStyle(**style_kwargs),
                    fields=",".join(fields),
                )
            )
        )

    def _emit_code_inline_style(self, ctx: DeserContext, start: int, end: int) -> None:
        """Emit style for inline code (monospace + green color)."""
        if start >= end:
            return

        r = int(INLINE_CODE_COLOR[1:3], 16) / 255.0
        g = int(INLINE_CODE_COLOR[3:5], 16) / 255.0
        b = int(INLINE_CODE_COLOR[5:7], 16) / 255.0

        ctx.emit(
            Request(
                updateTextStyle=UpdateTextStyleRequest(
                    range=Range(
                        startIndex=start,
                        endIndex=end,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                    textStyle=TextStyle(
                        weightedFontFamily=WeightedFontFamily(fontFamily=MONOSPACE_FONT),
                        foregroundColor=OptionalColor(color=Color(rgbColor=RgbColor(red=r, green=g, blue=b))),
                    ),
                    fields="weightedFontFamily,foregroundColor",
                )
            )
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _emit_insert_text(self, ctx: DeserContext, text: str) -> None:
        """Emit an InsertTextRequest and advance the context index."""
        ctx.emit(
            Request(
                insertText=InsertTextRequest(
                    text=text,
                    location=Location(
                        index=ctx.index,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                )
            )
        )
        ctx.advance(len(text))

    def _emit_paragraph_style(self, ctx: DeserContext, start: int, end: int, style_name: _NamedStyleType) -> None:
        """Emit an UpdateParagraphStyleRequest."""
        ctx.emit(
            Request(
                updateParagraphStyle=UpdateParagraphStyleRequest(
                    range=Range(
                        startIndex=start,
                        endIndex=end,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                    paragraphStyle=ParagraphStyle(namedStyleType=style_name),
                    fields="namedStyleType",
                )
            )
        )


def deserialize(
    markdown_text: str,
    *,
    tab_id: str = "",
    segment_id: str = "",
) -> list[Request]:
    """Convenience function: parse Markdown and return API requests.

    Args:
        markdown_text: Markdown source to deserialize.
        tab_id: Target tab ID for multi-tab documents.
        segment_id: Target segment ID (body, header, footer).

    Returns:
        List of ``Request`` objects for ``batchUpdate``.
    """
    return MarkdownDeserializer().deserialize(
        markdown_text,
        tab_id=tab_id,
        segment_id=segment_id,
    )
