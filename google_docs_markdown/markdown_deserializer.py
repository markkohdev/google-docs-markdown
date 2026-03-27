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
    Size,
    WeightedFontFamily,
)
from google_docs_markdown.models.requests import (
    CreateFootnoteRequest,
    CreateParagraphBulletsRequest,
    InsertInlineImageRequest,
    InsertTableRequest,
    InsertTextRequest,
    PinTableHeaderRowsRequest,
    Request,
    UpdateParagraphStyleRequest,
    UpdateTextStyleRequest,
)
from google_docs_markdown.models.styles import ParagraphStyle, TextStyle

_IMAGE_PROPS_RE = re.compile(r"<!--\s*image-props:\s*(\{.*?\})\s*-->")


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
    "BULLET_CHECKBOX",
    "NUMBERED_DECIMAL_ALPHA_ROMAN",
]

_TITLE_TAG_RE = re.compile(r"<!--\s*title\s*-->\s*\n?")
_SUBTITLE_TAG_RE = re.compile(r"<!--\s*subtitle\s*-->\s*\n?")
_ALIGN_TAG_RE = re.compile(r'<!--\s*align:\s*\{[^}]*"value"\s*:\s*"(center|right|justify)"[^}]*\}\s*-->')
_FOOTNOTE_REF_RE = re.compile(r"\[\^(\d+)\]")
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^\d+\]:.*$", re.MULTILINE)

_ALIGNMENT_VALUE_TO_API = {"center": "CENTER", "right": "END", "justify": "JUSTIFIED"}


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

        # TODO(future): Emit updateDocumentStyle request for page layout
        # (pageSize, margins) when metadata carries document-level style info.
        # Currently metadata stores text-style defaults (font, fontSize,
        # headingStyles) which map to namedStyles, not documentStyle.
        # When page-layout metadata is added, build a DocumentStyle here and
        # append an UpdateDocumentStyleRequest to ctx.requests.

        return [r for r in ctx.requests if isinstance(r, Request)]

    def _process_content(self, content: str, ctx: DeserContext) -> None:
        """Process Markdown content via markdown-it AST and comment-tag dispatch.

        Block-level comment tags (``html_block``) and inline comment tags
        (``html_inline``) are dispatched inside ``_walk_tokens`` as
        markdown-it discovers them, so no separate tag pass is needed.
        """
        # Strip footnote definitions — populating footnote content requires
        # a two-pass approach (create footnote → get ID from response →
        # insert text into footnote segment) which can't be done in a
        # single batchUpdate.
        content = _FOOTNOTE_DEF_RE.sub("", content)
        tokens = self._md.parse(content)
        self._walk_tokens(tokens, ctx)

    def _walk_tokens(self, tokens: list[Token], ctx: DeserContext) -> None:
        """Walk top-level markdown-it tokens and dispatch to handlers."""
        i = 0
        pending_style: _NamedStyleType | None = None
        pending_alignment: str | None = None
        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                start_index = ctx.index
                i = self._handle_heading(tokens, i, ctx, style_override=pending_style)
                if pending_alignment:
                    self._emit_alignment(ctx, start_index, ctx.index - 1, pending_alignment)
                    pending_alignment = None
                pending_style = None
            elif token.type == "paragraph_open":
                start_index = ctx.index
                i = self._handle_paragraph(tokens, i, ctx, style_override=pending_style)
                if pending_alignment:
                    self._emit_alignment(ctx, start_index, ctx.index - 1, pending_alignment)
                    pending_alignment = None
                pending_style = None
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                pending_style = None
                pending_alignment = None
                i = self._handle_list(tokens, i, ctx)
            elif token.type == "fence":
                pending_style = None
                pending_alignment = None
                self._handle_code_fence(token, ctx)
                i += 1
            elif token.type == "table_open":
                pending_style = None
                pending_alignment = None
                i = self._handle_table(tokens, i, ctx)
            elif token.type == "hr":
                pending_style = None
                pending_alignment = None
                self._handle_hr(ctx)
                i += 1
            elif token.type == "html_block":
                block_content = (token.content or "").strip()
                if _TITLE_TAG_RE.fullmatch(block_content + "\n") or block_content == "<!-- title -->":
                    pending_style = "TITLE"
                    i += 1
                elif _SUBTITLE_TAG_RE.fullmatch(block_content + "\n") or block_content == "<!-- subtitle -->":
                    pending_style = "SUBTITLE"
                    i += 1
                else:
                    align_m = _ALIGN_TAG_RE.match(block_content)
                    if align_m:
                        pending_alignment = _ALIGNMENT_VALUE_TO_API.get(align_m.group(1))
                        i += 1
                    else:
                        pending_style = None
                        pending_alignment = None
                        self._handle_html_block(token, ctx)
                        i += 1
            else:
                i += 1

    # ------------------------------------------------------------------
    # Block-level handlers
    # ------------------------------------------------------------------

    def _handle_heading(
        self,
        tokens: list[Token],
        start: int,
        ctx: DeserContext,
        *,
        style_override: _NamedStyleType | None = None,
    ) -> int:
        """Process heading_open .. inline .. heading_close."""
        open_token = tokens[start]
        level = int(open_token.tag[1])
        style_name = style_override or cast(_NamedStyleType, MD_HEADING_LEVEL_TO_STYLE.get(level, "NORMAL_TEXT"))

        inline_token = tokens[start + 1] if start + 1 < len(tokens) else None

        start_index = ctx.index
        if inline_token and self._inline_has_comment_tags(inline_token):
            self._emit_inline_with_tags(inline_token, ctx)
        else:
            text = self._extract_inline_text(inline_token) if inline_token else ""
            if text:
                self._emit_insert_text(ctx, text + "\n")
                self._apply_inline_formatting_from_token(inline_token, ctx, start_index)

        if ctx.index > start_index:
            end_index = ctx.index - 1
            self._emit_paragraph_style(ctx, start_index, end_index, style_name)

        return start + 3

    def _handle_paragraph(
        self,
        tokens: list[Token],
        start: int,
        ctx: DeserContext,
        *,
        style_override: _NamedStyleType | None = None,
    ) -> int:
        """Process paragraph_open .. inline .. paragraph_close."""
        inline_token = tokens[start + 1] if start + 1 < len(tokens) else None

        if style_override == "SUBTITLE" and inline_token and inline_token.type == "inline":
            raw_content = inline_token.content or ""
            text = raw_content
            if text.startswith("*") and text.endswith("*"):
                text = text[1:-1]
            if text:
                start_index = ctx.index
                self._emit_insert_text(ctx, text + "\n")
                end_index = ctx.index - 1
                self._emit_paragraph_style(ctx, start_index, end_index, "SUBTITLE")
            return start + 3

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
                self._emit_inline_with_tags(inline_token, ctx)
            else:
                text = self._extract_inline_text(inline_token)
                start_index = ctx.index
                if text:
                    self._emit_insert_text(ctx, text + "\n")
                self._apply_inline_formatting_from_token(inline_token, ctx, start_index)

        return start + 3

    def _handle_list(self, tokens: list[Token], start: int, ctx: DeserContext) -> int:
        """Process bullet_list_open/ordered_list_open .. list_item .. close."""
        is_ordered = tokens[start].type == "ordered_list_open"
        close_type = "ordered_list_close" if is_ordered else "bullet_list_close"

        items: list[tuple[str, int, Token | None, bool]] = []
        i = start + 1
        nesting = 0
        while i < len(tokens) and tokens[i].type != close_type:
            if tokens[i].type == "list_item_open":
                item_text, item_inline, i, is_checkbox = self._extract_list_item(tokens, i)
                items.append((item_text, nesting, item_inline, is_checkbox))
            elif tokens[i].type in ("bullet_list_open", "ordered_list_open"):
                nesting += 1
                i += 1
            elif tokens[i].type in ("bullet_list_close", "ordered_list_close"):
                nesting = max(0, nesting - 1)
                i += 1
            else:
                i += 1

        default_preset: _BulletPreset = "NUMBERED_DECIMAL_ALPHA_ROMAN" if is_ordered else "BULLET_DISC_CIRCLE_SQUARE"

        for item_text, _nesting, item_inline, is_checkbox in items:
            start_index = ctx.index

            if item_inline and self._inline_has_comment_tags(item_inline):
                self._emit_inline_with_tags(item_inline, ctx)
            elif item_text:
                self._emit_insert_text(ctx, item_text + "\n")
                if item_inline:
                    self._apply_inline_formatting_from_token(item_inline, ctx, start_index)
            else:
                continue

            bullet_preset: _BulletPreset = "BULLET_CHECKBOX" if is_checkbox else default_preset

            end_index = ctx.index - 1
            if end_index > start_index:
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

        return i + 1

    def _extract_list_item(self, tokens: list[Token], start: int) -> tuple[str, Token | None, int, bool]:
        """Extract text, inline token, next index, and checkbox flag from a list item.

        Returns:
            (text, inline_token, next_index, is_checkbox)
        """
        i = start + 1
        text = ""
        inline_token = None
        while i < len(tokens) and tokens[i].type != "list_item_close":
            if tokens[i].type == "inline":
                text = self._extract_inline_text(tokens[i])
                inline_token = tokens[i]
            elif tokens[i].type == "html_block":
                html_content = (tokens[i].content or "").strip()
                if html_content.startswith("<!--"):
                    fake = Token("inline", "", 0)
                    fake.content = html_content
                    child_html = Token("html_inline", "", 0)
                    child_html.content = html_content
                    fake.children = [child_html]
                    inline_token = fake
                    tags = parse_tags(html_content)
                    for tag in tags:
                        if tag.content:
                            text = tag.content
            elif tokens[i].type == "paragraph_open":
                pass
            elif tokens[i].type == "paragraph_close":
                pass
            i += 1

        is_checkbox = False
        if text.startswith("[ ] ") or text.startswith("[x] ") or text.startswith("[X] "):
            is_checkbox = True
            text = text[4:]
        elif text in ("[ ]", "[x]", "[X]"):
            is_checkbox = True
            text = ""

        return text, inline_token, i + 1, is_checkbox

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
        _CellInfo = tuple[str, Token | None, bool]
        rows: list[list[_CellInfo]] = []
        i = start + 1
        current_row: list[_CellInfo] | None = None
        in_th = False
        has_header = False

        while i < len(tokens) and tokens[i].type != "table_close":
            if tokens[i].type == "tr_open":
                current_row = []
                i += 1
            elif tokens[i].type == "tr_close":
                if current_row is not None:
                    rows.append(current_row)
                current_row = None
                i += 1
            elif tokens[i].type == "th_open":
                in_th = True
                has_header = True
                i += 1
            elif tokens[i].type == "th_close":
                in_th = False
                i += 1
            elif tokens[i].type == "td_open":
                i += 1
            elif tokens[i].type == "td_close":
                i += 1
            elif tokens[i].type == "inline" and current_row is not None:
                cell_token = tokens[i]
                cell_text = self._extract_inline_text(cell_token)
                is_bold = in_th and self._inline_is_fully_bold(cell_token)
                current_row.append((cell_text, cell_token, is_bold))
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
            cell_inserts: list[tuple[int, str, bool]] = []
            for row_idx, row in enumerate(rows):
                for col_idx, cell_info in enumerate(row):
                    cell_text, _cell_token, is_bold = cell_info
                    if cell_text:
                        cell_index = insert_index + 4 + row_idx * (num_cols * 2 + 1) + col_idx * 2
                        cell_inserts.append((cell_index, cell_text, is_bold))

            for cell_index, cell_text, is_bold in reversed(cell_inserts):
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
                if is_bold:
                    ctx.emit(
                        Request(
                            updateTextStyle=UpdateTextStyleRequest(
                                range=Range(
                                    startIndex=cell_index,
                                    endIndex=cell_index + len(cell_text),
                                    segmentId=ctx.segment_id or None,
                                    tabId=ctx.tab_id or None,
                                ),
                                textStyle=TextStyle(bold=True),
                                fields="bold",
                            )
                        )
                    )

            # Cell text inserts shift everything after the table by
            # the total length of all inserted cell content.
            total_cell_len = sum(len(text) for _, text, _ in cell_inserts)
            ctx.advance(total_cell_len)

            if has_header:
                ctx.emit(
                    Request(
                        pinTableHeaderRows=PinTableHeaderRowsRequest(
                            pinnedHeaderRowsCount=1,
                            tableStartLocation=Location(
                                index=insert_index + 1,
                                segmentId=ctx.segment_id or None,
                                tabId=ctx.tab_id or None,
                            ),
                        )
                    )
                )

        return i + 1

    def _inline_is_fully_bold(self, token: Token) -> bool:
        """Check if an inline token's entire content is wrapped in bold markers."""
        if not token.children:
            return False
        meaningful = [c for c in token.children if not (c.type == "text" and not c.content.strip())]
        return len(meaningful) >= 3 and meaningful[0].type == "strong_open" and meaningful[-1].type == "strong_close"

    def _handle_hr(self, ctx: DeserContext) -> None:
        """Process horizontal rule.

        The Google Docs API has no ``insertHorizontalRule`` request.  We
        approximate by inserting an empty paragraph with a bottom border
        to create a visible separator line.
        """
        start_index = ctx.index
        self._emit_insert_text(ctx, "\n")
        ctx.emit(
            Request(
                updateParagraphStyle=UpdateParagraphStyleRequest(
                    range=Range(
                        startIndex=start_index,
                        endIndex=ctx.index - 1,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                    paragraphStyle=ParagraphStyle(
                        borderBottom={  # type: ignore[arg-type]
                            "color": {"color": {"rgbColor": {"red": 0.8, "green": 0.8, "blue": 0.8}}},
                            "width": {"magnitude": 1, "unit": "PT"},
                            "dashStyle": "SOLID",
                            "padding": {"magnitude": 3, "unit": "PT"},
                        },
                        spaceBelow=Dimension(magnitude=6, unit="PT"),
                    ),
                    fields="borderBottom,spaceBelow",
                )
            )
        )

    def _handle_html_block(self, token: Token, ctx: DeserContext) -> None:
        """Process HTML block content — comment tags plus any inter-tag text.

        markdown-it treats lines starting with ``<!--`` as ``html_block``
        tokens, which bypasses inline parsing.  When the block contains
        both comment tags and plain text (or backtick code), we must emit
        the inter-tag text ourselves.
        """
        content = (token.content or "").strip()
        tags = parse_tags(content)
        if not tags:
            return

        last_end = 0
        for tag in tags:
            if tag.start > last_end:
                self._emit_html_block_text(content[last_end : tag.start], ctx)
            self._dispatch_tag(tag, ctx)
            last_end = tag.end

        if last_end < len(content):
            self._emit_html_block_text(content[last_end:], ctx)

        if tags:
            self._emit_insert_text(ctx, "\n")

    def _emit_html_block_text(self, text: str, ctx: DeserContext) -> None:
        """Emit plain text found between comment tags in an html_block.

        Handles backtick-delimited inline code by applying monospace styling.
        """
        text = text.strip()
        if not text:
            return

        backtick_re = re.compile(r"`([^`]+)`")
        last = 0
        for m in backtick_re.finditer(text):
            before = text[last : m.start()]
            if before:
                self._emit_insert_text(ctx, before)
            code_text = m.group(1)
            start_idx = ctx.index
            self._emit_insert_text(ctx, code_text)
            self._emit_code_inline_style(ctx, start_idx, ctx.index)
            last = m.end()

        remainder = text[last:]
        if remainder:
            self._emit_insert_text(ctx, remainder)

    # ------------------------------------------------------------------
    # Inline comment-tag handling
    # ------------------------------------------------------------------

    def _inline_has_comment_tags(self, token: Token) -> bool:
        """Check if an inline token contains HTML comment tags.

        ``image-props`` annotations are excluded — they are handled
        inline by ``_apply_inline_formatting_from_token`` alongside the
        ``image`` token they annotate.
        """
        if not token.children:
            return False
        for child in token.children:
            if child.type == "html_inline" and child.content.strip().startswith("<!--"):
                if not _IMAGE_PROPS_RE.match(child.content.strip()):
                    return True
        return False

    def _emit_inline_with_tags(self, token: Token, ctx: DeserContext) -> None:
        """Emit inline content with comment-tag dispatch AND formatting.

        Walks inline children tracking formatting state (bold, italic, etc.)
        while building a raw string that includes HTML comment text for tag
        parsing.  Text segments between tags are emitted with their active
        formatting applied; tags are dispatched to their handlers.

        A trailing newline is always appended.
        """
        if not token.children:
            return

        # Phase 1: walk children, build segments with formatting context
        _Segment = tuple[str, str, list[str]]  # (kind, content, formatting_stack)
        segments: list[_Segment] = []
        formatting: list[str] = []
        link_href: str | None = None

        for child in token.children:
            if child.type == "text":
                segments.append(("text", child.content, list(formatting)))
            elif child.type == "html_inline":
                html_lower = child.content.strip().lower()
                if html_lower == "<u>":
                    formatting.append("underline")
                elif html_lower == "</u>":
                    if "underline" in formatting:
                        formatting.remove("underline")
                elif html_lower == "<sup>":
                    formatting.append("superscript")
                elif html_lower == "</sup>":
                    if "superscript" in formatting:
                        formatting.remove("superscript")
                elif html_lower == "<sub>":
                    formatting.append("subscript")
                elif html_lower == "</sub>":
                    if "subscript" in formatting:
                        formatting.remove("subscript")
                else:
                    segments.append(("html", child.content, []))
            elif child.type == "strong_open":
                formatting.append("bold")
            elif child.type == "strong_close":
                if "bold" in formatting:
                    formatting.remove("bold")
            elif child.type == "em_open":
                formatting.append("italic")
            elif child.type == "em_close":
                if "italic" in formatting:
                    formatting.remove("italic")
            elif child.type == "s_open":
                formatting.append("strikethrough")
            elif child.type == "s_close":
                if "strikethrough" in formatting:
                    formatting.remove("strikethrough")
            elif child.type == "link_open":
                link_href = str((child.attrs or {}).get("href", ""))
                formatting.append(f"link:{link_href}")
            elif child.type == "link_close":
                formatting[:] = [f for f in formatting if not f.startswith("link:")]
                link_href = None
            elif child.type == "code_inline":
                segments.append(("code", child.content, []))
            elif child.type in ("softbreak", "hardbreak"):
                segments.append(("text", "\n", list(formatting)))

        raw_content = "".join(content for _, content, _ in segments)
        if not raw_content.strip():
            return

        # Phase 2: parse tags from the reassembled raw content
        tags = parse_tags(raw_content)
        if not tags:
            text = self._extract_inline_text(token)
            if text:
                start_index = ctx.index
                self._emit_insert_text(ctx, text + "\n")
                self._apply_inline_formatting_from_token(token, ctx, start_index)
            return

        # Phase 3: build a formatting map keyed by raw-content position
        seg_ranges: list[tuple[int, int, str, list[str]]] = []
        pos = 0
        for kind, content, fmt in segments:
            seg_ranges.append((pos, pos + len(content), kind, fmt))
            pos += len(content)

        # Phase 4: emit text between tags with formatting, dispatch tags
        last_end = 0
        for tag in tags:
            if tag.start > last_end:
                self._emit_text_range_with_formatting(raw_content, last_end, tag.start, seg_ranges, ctx)
            self._dispatch_tag(tag, ctx)
            last_end = tag.end

        if last_end < len(raw_content):
            self._emit_text_range_with_formatting(raw_content, last_end, len(raw_content), seg_ranges, ctx)

        self._emit_insert_text(ctx, "\n")

    def _emit_text_range_with_formatting(
        self,
        raw: str,
        start: int,
        end: int,
        seg_ranges: list[tuple[int, int, str, list[str]]],
        ctx: DeserContext,
    ) -> None:
        """Emit a slice of the raw content, applying formatting from segment metadata.

        Skips HTML segments (already handled as tags).  Consecutive characters
        sharing the same formatting are batched into a single insert + style request.
        """
        # Collect (char, formatting) pairs for the range, skipping HTML segments
        chars_with_fmt: list[tuple[str, list[str]]] = []
        for i in range(start, end):
            ch = raw[i]
            fmt: list[str] = []
            kind = "text"
            for seg_start, seg_end, seg_kind, seg_fmt in seg_ranges:
                if seg_start <= i < seg_end:
                    kind = seg_kind
                    fmt = seg_fmt
                    break
            if kind == "html":
                continue
            chars_with_fmt.append((ch, fmt))

        if not chars_with_fmt:
            return

        # Group into runs of identical formatting
        runs: list[tuple[str, list[str]]] = []
        current_text = chars_with_fmt[0][0]
        current_fmt = chars_with_fmt[0][1]
        for ch, fmt in chars_with_fmt[1:]:
            if fmt == current_fmt:
                current_text += ch
            else:
                runs.append((current_text, current_fmt))
                current_text = ch
                current_fmt = fmt
        runs.append((current_text, current_fmt))

        # Emit each run.  When a run has less formatting than its predecessor,
        # explicitly clear the dropped fields so Google Docs doesn't inherit
        # the adjacent style (e.g. bold leaking onto unformatted text).
        prev_fmt: list[str] = []
        for run_text, run_fmt in runs:
            if not run_text:
                continue
            run_start = ctx.index
            self._emit_insert_text(ctx, run_text)
            if run_fmt:
                is_code = any(f == "code_inline" for f in run_fmt)
                if is_code:
                    self._emit_code_inline_style(ctx, run_start, ctx.index)
                else:
                    self._emit_text_style(ctx, run_start, ctx.index, run_fmt)
            elif prev_fmt:
                self._emit_clear_formatting(ctx, run_start, ctx.index, prev_fmt)
            prev_fmt = run_fmt

    # ------------------------------------------------------------------
    # Comment-tag dispatch
    # ------------------------------------------------------------------

    def _dispatch_tag(self, tag: ParsedTag, ctx: DeserContext) -> None:
        """Dispatch a single parsed tag to its handler."""
        handler = self._registry.match_deserialize(tag)
        if handler:
            requests = handler.deserialize(tag, ctx)
            for req in requests:
                if isinstance(req, Request):
                    ctx.emit(req)

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
                parts.append(_FOOTNOTE_REF_RE.sub("", child.content))
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
        children = token.children

        for idx, child in enumerate(children):
            if child.type == "text":
                footnote_matches = list(_FOOTNOTE_REF_RE.finditer(child.content))
                if not footnote_matches:
                    text_len = len(child.content)
                    if formatting_stack:
                        self._emit_text_style(ctx, text_offset, text_offset + text_len, formatting_stack)
                    text_offset += text_len
                else:
                    last_end = 0
                    for m in footnote_matches:
                        before = child.content[last_end : m.start()]
                        if before:
                            if formatting_stack:
                                self._emit_text_style(ctx, text_offset, text_offset + len(before), formatting_stack)
                            text_offset += len(before)
                        ctx.emit(
                            Request(
                                createFootnote=CreateFootnoteRequest(
                                    location=Location(
                                        index=text_offset,
                                        segmentId=ctx.segment_id or None,
                                        tabId=ctx.tab_id or None,
                                    )
                                )
                            )
                        )
                        last_end = m.end()
                    after = child.content[last_end:]
                    if after:
                        if formatting_stack:
                            self._emit_text_style(ctx, text_offset, text_offset + len(after), formatting_stack)
                        text_offset += len(after)

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
                elif html == "<sup>":
                    formatting_stack.append("superscript")
                elif html == "</sup>":
                    if "superscript" in formatting_stack:
                        formatting_stack.remove("superscript")
                elif html == "<sub>":
                    formatting_stack.append("subscript")
                elif html == "</sub>":
                    if "subscript" in formatting_stack:
                        formatting_stack.remove("subscript")

            elif child.type == "link_open":
                url = (child.attrs or {}).get("href", "")
                formatting_stack.append(f"link:{url}")
            elif child.type == "link_close":
                formatting_stack[:] = [f for f in formatting_stack if not f.startswith("link:")]

            elif child.type == "image":
                src = str((child.attrs or {}).get("src", ""))
                if src:
                    object_size = self._parse_image_props_from_next_sibling(children, idx)
                    ctx.emit(
                        Request(
                            insertInlineImage=InsertInlineImageRequest(
                                uri=src,
                                objectSize=object_size,
                                location=Location(
                                    index=text_offset,
                                    segmentId=ctx.segment_id or None,
                                    tabId=ctx.tab_id or None,
                                ),
                            )
                        )
                    )

    @staticmethod
    def _parse_image_props_from_next_sibling(children: list[Token], current_idx: int) -> Size | None:
        """Check the next sibling token for an ``<!-- image-props: {...} -->`` tag.

        Returns a ``Size`` when width/height are found, otherwise ``None``.
        """
        import json as _json

        next_idx = current_idx + 1
        if next_idx >= len(children):
            return None
        sibling = children[next_idx]
        if sibling.type != "html_inline":
            return None
        m = _IMAGE_PROPS_RE.match(sibling.content.strip())
        if not m:
            return None
        try:
            data = _json.loads(m.group(1))
        except (ValueError, TypeError):
            return None
        width = data.get("width")
        height = data.get("height")
        if width is None and height is None:
            return None
        size_kwargs: dict[str, Dimension] = {}
        if width is not None:
            size_kwargs["width"] = Dimension(magnitude=float(width), unit="PT")
        if height is not None:
            size_kwargs["height"] = Dimension(magnitude=float(height), unit="PT")
        return Size(**size_kwargs)

    def _emit_text_style(self, ctx: DeserContext, start: int, end: int, formatting: list[str]) -> None:
        """Emit an UpdateTextStyleRequest for the given formatting stack."""
        if start >= end:
            return

        bold = "bold" in formatting
        italic = "italic" in formatting
        strikethrough = "strikethrough" in formatting
        underline = "underline" in formatting
        superscript = "superscript" in formatting
        subscript = "subscript" in formatting
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
        if superscript:
            style_kwargs["baselineOffset"] = "SUPERSCRIPT"
            fields.append("baselineOffset")
        elif subscript:
            style_kwargs["baselineOffset"] = "SUBSCRIPT"
            fields.append("baselineOffset")
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

    def _emit_clear_formatting(self, ctx: DeserContext, start: int, end: int, prev_fmt: list[str]) -> None:
        """Explicitly clear formatting fields that were active in the previous run.

        Google Docs inherits the style of adjacent text on insertion.
        This resets specific fields (bold, italic, etc.) to ``false`` so
        unformatted text doesn't inherit formatting from a preceding run.
        """
        if start >= end:
            return

        fields: list[str] = []
        style_kwargs: dict[str, Any] = {}
        for f in prev_fmt:
            if f == "bold":
                style_kwargs["bold"] = False
                fields.append("bold")
            elif f == "italic":
                style_kwargs["italic"] = False
                fields.append("italic")
            elif f == "strikethrough":
                style_kwargs["strikethrough"] = False
                fields.append("strikethrough")
            elif f == "underline":
                style_kwargs["underline"] = False
                fields.append("underline")

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

    _VALID_ALIGNMENTS = {"CENTER", "END", "JUSTIFIED", "START", "ALIGNMENT_UNSPECIFIED"}

    def _emit_alignment(self, ctx: DeserContext, start: int, end: int, alignment: str) -> None:
        """Emit an UpdateParagraphStyleRequest to set paragraph alignment."""
        if start >= end or alignment not in self._VALID_ALIGNMENTS:
            return
        ctx.emit(
            Request(
                updateParagraphStyle=UpdateParagraphStyleRequest(
                    range=Range(
                        startIndex=start,
                        endIndex=end,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                    paragraphStyle=ParagraphStyle(alignment=alignment),  # type: ignore[arg-type]
                    fields="alignment",
                )
            )
        )

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
