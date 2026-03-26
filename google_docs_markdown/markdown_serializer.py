"""Markdown serializer for Google Docs Pydantic models.

Converts DocumentTab Pydantic models into Markdown text using a visitor-style
traversal of the document tree.

Phase 1 scope: text, headings, paragraphs, bold, italic, line breaks.
Phase 2.1 scope: links, strikethrough, underline, rich links, horizontal
rules, footnote references and footnote content.
Phase 2.2 scope: lists (ordered, unordered, nested) via block grouper
pre-processing pass.
Phase 2.3 scope: tables (pipe tables with header detection, formatted cell
content, multi-paragraph cells via <br>, pipe escaping).
Phase 2.4 scope: code blocks (U+E907 boundary detection, monospace font,
fenced code blocks).
Phase 2.5 scope: images (InlineObjectElement → ![alt](url)).
Phase 2.6 scope: non-Markdown elements (Person, DateElement, AutoText,
Equation, SectionBreak, ColumnBreak, TableOfContents, suggestions,
style annotations, headers/footers, embedded metadata).
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
from google_docs_markdown.comment_tags import TagType, opening_tag, wrap_tag
from google_docs_markdown.models.common import (
    Footer,
    Footnote,
    Header,
    OptionalColor,
)
from google_docs_markdown.models.document import DocumentTab
from google_docs_markdown.models.elements import (
    AutoText,
    ColumnBreak,
    DateElement,
    Equation,
    FootnoteReference,
    HorizontalRule,
    InlineObjectElement,
    PageBreak,
    Paragraph,
    ParagraphElement,
    Person,
    RichLink,
    StructuralElement,
    Table,
    TableCell,
    TableOfContents,
    TextRun,
)
from google_docs_markdown.models.styles import TextStyle

_HEADING_PREFIX: dict[str, str] = {
    "TITLE": "#",
    "HEADING_1": "#",
    "HEADING_2": "##",
    "HEADING_3": "###",
    "HEADING_4": "####",
    "HEADING_5": "#####",
    "HEADING_6": "######",
}

_CHIP_PLACEHOLDER = "<!-- chip-placeholder -->"

_COMMON_GDOCS_FONTS = frozenset(
    {
        "Arial",
        "Proxima Nova",
        "Roboto",
        "Times New Roman",
        "Georgia",
        "Verdana",
        "Trebuchet MS",
        "Calibri",
    }
)


class MarkdownSerializer:
    """Serialize a DocumentTab Pydantic model into Markdown text.

    Traverses DocumentTab -> Body -> StructuralElement -> Paragraph ->
    ParagraphElement -> TextRun, emitting Markdown along the way.
    """

    def __init__(self) -> None:
        self._footnote_refs: list[tuple[str, str]] = []
        self._inline_objects: dict[str, Any] | None = None
        self._default_font: str | None = None
        self._default_font_size: float | None = None
        self._default_fg_hex: str | None = None
        self._named_style_sizes: dict[str, float] = {}
        self._current_para_style: str | None = None

    def serialize(self, document_tab: DocumentTab) -> str:
        """Convert a DocumentTab to Markdown.

        Args:
            document_tab: The DocumentTab Pydantic model to serialize.

        Returns:
            Markdown text ending with a single trailing newline.
            Returns empty string for documents with no content.
        """
        if not document_tab.body or not document_tab.body.content:
            return ""

        self._footnote_refs = []
        self._inline_objects = document_tab.inlineObjects
        self._extract_default_styles(document_tab)

        blocks = group_elements(document_tab.body.content, document_tab.lists)

        paragraphs: list[str] = []
        for block in blocks:
            result = self._visit_block(block)
            if result is not None:
                paragraphs.append(result)

        footnote_defs = self._serialize_footnotes(document_tab.footnotes)
        if footnote_defs:
            paragraphs.extend(footnote_defs)

        header_blocks = self._serialize_headers(document_tab.headers)
        footer_blocks = self._serialize_footers(document_tab.footers)

        all_parts = header_blocks + paragraphs + footer_blocks
        return _join_paragraphs(all_parts)

    def _visit_block(self, block: Block) -> str | None:
        """Dispatch a Block to the appropriate visitor."""
        if isinstance(block, ListBlock):
            return self._visit_list_block(block)
        if isinstance(block, CodeBlock):
            return self._visit_code_block(block)
        return self._visit_structural_element(block)

    def _visit_code_block(self, block: CodeBlock) -> str:
        """Render a CodeBlock as a fenced Markdown code block."""
        lines: list[str] = []
        for para in block.paragraphs:
            line_parts: list[str] = []
            for elem in para.elements or []:
                if elem.textRun and elem.textRun.content:
                    line_parts.append(elem.textRun.content)
            raw = "".join(line_parts)
            raw = raw.replace("\ue907", "")
            raw = raw.rstrip("\n")
            if raw:
                lines.append(raw)
        return "```\n" + "\n".join(lines) + "\n```"

    def _visit_list_block(self, block: ListBlock) -> str:
        """Render a ListBlock as a Markdown list."""
        lines: list[str] = []
        for item in block.items:
            text = self._collect_paragraph_text(item.paragraph.elements or [])
            indent = "    " * item.nesting_level
            marker = "1." if item.is_ordered else "-"
            lines.append(f"{indent}{marker} {text}")
        return "\n".join(lines)

    def _serialize_footnotes(self, footnotes: dict[str, Any] | None) -> list[str]:
        """Render collected footnote references as Markdown definitions."""
        if not self._footnote_refs or not footnotes:
            return []

        defs: list[str] = []
        for footnote_id, footnote_number in self._footnote_refs:
            raw = footnotes.get(footnote_id)
            if raw is None:
                continue

            footnote = raw if isinstance(raw, Footnote) else Footnote.model_validate(raw)

            content_parts: list[str] = []
            for element in footnote.content or []:
                result = self._visit_structural_element(element)
                if result is not None and result.strip():
                    content_parts.append(result.strip())

            if content_parts:
                first, *rest = content_parts
                lines = [f"[^{footnote_number}]: {first}"]
                for part in rest:
                    lines.append(f"    {part}")
                defs.append("\n".join(lines))

        return defs

    def _visit_structural_element(self, element: StructuralElement) -> str | None:
        """Return Markdown for a StructuralElement, or None to skip."""
        if element.paragraph:
            return self._visit_paragraph(element.paragraph)
        if element.table:
            return self._visit_table(element.table)
        if element.sectionBreak:
            return self._visit_section_break(element)
        if element.tableOfContents:
            return self._visit_table_of_contents(element.tableOfContents)
        return None

    def _visit_table(self, table: Table) -> str | None:
        """Render a Table as a Markdown pipe table."""
        if not table.tableRows:
            return None

        rows: list[list[str]] = []
        header_row_count = 0

        for row in table.tableRows:
            cells: list[str] = []
            for cell in row.tableCells or []:
                cells.append(self._serialize_cell_content(cell))
            rows.append(cells)

            if row.tableRowStyle and row.tableRowStyle.tableHeader:
                header_row_count += 1

        if not rows:
            return None

        col_count = table.columns or (max(len(r) for r in rows) if rows else 0)
        for r in rows:
            while len(r) < col_count:
                r.append("")

        separator = "| " + " | ".join("---" for _ in range(col_count)) + " |"

        lines: list[str] = []
        for i, r in enumerate(rows):
            line = "| " + " | ".join(r) + " |"
            lines.append(line)
            if i == max(header_row_count - 1, 0):
                lines.append(separator)

        return "\n".join(lines)

    def _serialize_cell_content(self, cell: TableCell) -> str:
        """Serialize a table cell's content into a single inline string."""
        if not cell.content:
            return ""

        parts: list[str] = []
        for element in cell.content:
            if element.paragraph:
                text = self._collect_paragraph_text(element.paragraph.elements or [])
                if text:
                    parts.append(text)

        result = "<br>".join(parts)
        return _escape_pipe(result)

    def _visit_paragraph(self, paragraph: Paragraph) -> str:
        """Return Markdown for a Paragraph (heading, subtitle, or body text)."""
        style_type = None
        if paragraph.paragraphStyle:
            style_type = paragraph.paragraphStyle.namedStyleType

        self._current_para_style = style_type
        text = self._collect_paragraph_text(paragraph.elements or [])
        self._current_para_style = None

        heading_prefix = _HEADING_PREFIX.get(style_type or "")
        if heading_prefix and text:
            rendered = f"{heading_prefix} {text}"
            if style_type == "TITLE":
                return f"{opening_tag(TagType.TITLE)}\n{rendered}"
            return rendered

        if style_type == "SUBTITLE" and text:
            return f"{opening_tag(TagType.SUBTITLE)}\n*{text}*"

        return text

    def _collect_paragraph_text(self, elements: list[ParagraphElement]) -> str:
        """Concatenate and format inline text from paragraph elements."""
        parts: list[str] = []
        for element in elements:
            result = self._visit_paragraph_element(element)
            if result is not None:
                parts.append(result)

        text = "".join(parts)
        return text.rstrip()

    def _visit_paragraph_element(self, element: ParagraphElement) -> str | None:
        """Return inline text for a ParagraphElement, or None to skip."""
        if element.textRun:
            return self._visit_text_run(element.textRun)
        if element.horizontalRule:
            return self._visit_horizontal_rule(element.horizontalRule)
        if element.richLink:
            return self._visit_rich_link(element.richLink)
        if element.footnoteReference:
            return self._visit_footnote_reference(element.footnoteReference)
        if element.inlineObjectElement:
            return self._visit_inline_object(element.inlineObjectElement)
        if element.person:
            return self._visit_person(element.person)
        if element.dateElement:
            return self._visit_date_element(element.dateElement)
        if element.autoText:
            return self._visit_auto_text(element.autoText)
        if element.equation:
            return self._visit_equation(element.equation)
        if element.pageBreak:
            return self._visit_page_break(element.pageBreak)
        if element.columnBreak:
            return self._visit_column_break(element.columnBreak)
        return None

    def _visit_text_run(self, text_run: TextRun) -> str | None:
        """Return text content with Markdown formatting applied."""
        content = text_run.content
        if content is None:
            return None

        content = content.replace("\ue907", _CHIP_PLACEHOLDER)
        if not content:
            return None

        has_chip = _CHIP_PLACEHOLDER in content

        style = text_run.textStyle
        bold = style and style.bold
        italic = style and style.italic
        strikethrough = style and style.strikethrough
        link = style and style.link
        underline = style and style.underline and not link

        has_formatting = bold or italic or strikethrough or underline
        if has_formatting and not has_chip:
            content = _apply_inline_formatting(
                content,
                bold=bool(bold),
                italic=bool(italic),
                strikethrough=bool(strikethrough),
                underline=bool(underline),
            )
        elif has_formatting and has_chip:
            parts = content.split(_CHIP_PLACEHOLDER)
            formatted_parts = []
            for part in parts:
                if part:
                    part = _apply_inline_formatting(
                        part,
                        bold=bool(bold),
                        italic=bool(italic),
                        strikethrough=bool(strikethrough),
                        underline=bool(underline),
                    )
                formatted_parts.append(part)
            content = _CHIP_PLACEHOLDER.join(formatted_parts)

        if link and link.url:
            content = _apply_link(content, link.url)

        style_props = self._extract_non_default_style(style)
        if style_props:
            content = wrap_tag(TagType.STYLE, content, style_props)

        if text_run.suggestedInsertionIds:
            suggestion_id = text_run.suggestedInsertionIds[0]
            content = wrap_tag(
                TagType.SUGGESTION,
                content,
                {"id": suggestion_id, "type": "insertion"},
            )
        elif text_run.suggestedDeletionIds:
            suggestion_id = text_run.suggestedDeletionIds[0]
            content = wrap_tag(
                TagType.SUGGESTION,
                content,
                {"id": suggestion_id, "type": "deletion"},
            )

        return content

    def _visit_horizontal_rule(self, _rule: HorizontalRule) -> str:
        return "---"

    def _visit_rich_link(self, rich_link: RichLink) -> str | None:
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

    def _visit_inline_object(self, obj: InlineObjectElement) -> str | None:
        """Render an InlineObjectElement as a Markdown image reference."""
        if not obj.inlineObjectId or not self._inline_objects:
            return None

        raw = self._inline_objects.get(obj.inlineObjectId)
        if raw is None:
            return None

        from google_docs_markdown.models.common import InlineObject

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

    def _visit_footnote_reference(self, ref: FootnoteReference) -> str | None:
        if not ref.footnoteNumber:
            return None
        if ref.footnoteId:
            self._footnote_refs.append((ref.footnoteId, ref.footnoteNumber))
        return f"[^{ref.footnoteNumber}]"

    def _visit_person(self, person: Person) -> str | None:
        props = person.personProperties
        if not props:
            return None
        name = props.name or props.email or ""
        data: dict[str, Any] = {}
        if props.email:
            data["email"] = props.email
        return wrap_tag(TagType.PERSON, name, data)

    def _visit_date_element(self, date_elem: DateElement) -> str | None:
        props = date_elem.dateElementProperties
        if not props:
            return None
        display = props.displayText or ""
        data: dict[str, Any] = {}
        if props.dateFormat:
            data["format"] = props.dateFormat
        if props.locale:
            data["locale"] = props.locale
        if props.timeFormat:
            data["timeFormat"] = props.timeFormat
        if props.timeZoneId:
            data["timeZoneId"] = props.timeZoneId
        if props.timestamp:
            data["timestamp"] = props.timestamp
        return wrap_tag(TagType.DATE, display, data)

    def _visit_auto_text(self, auto_text: AutoText) -> str | None:
        data: dict[str, Any] = {}
        if auto_text.type:
            data["type"] = auto_text.type
        return opening_tag(TagType.AUTO_TEXT, data or None)

    def _visit_equation(self, _eq: Equation) -> str:
        return opening_tag(TagType.EQUATION)

    def _visit_page_break(self, _pb: PageBreak) -> str:
        return opening_tag(TagType.PAGE_BREAK)

    def _visit_column_break(self, _cb: ColumnBreak) -> str:
        return opening_tag(TagType.COLUMN_BREAK)

    def _visit_section_break(self, element: StructuralElement) -> str | None:
        is_leading = (element.startIndex is None and (element.endIndex is None or element.endIndex <= 1)) or (
            element.startIndex is not None and element.startIndex == 0
        )
        if is_leading:
            return None
        sb = element.sectionBreak
        if not sb:
            return None
        data: dict[str, Any] = {}
        if sb.sectionStyle and sb.sectionStyle.sectionType:
            data["type"] = sb.sectionStyle.sectionType
        return opening_tag(TagType.SECTION_BREAK, data or None)

    def _visit_table_of_contents(self, _toc: TableOfContents) -> str:
        return opening_tag(TagType.TABLE_OF_CONTENTS)

    # ------------------------------------------------------------------
    # Style extraction
    # ------------------------------------------------------------------

    def _extract_default_styles(self, document_tab: DocumentTab) -> None:
        """Extract default font, size, and color from the NORMAL_TEXT named style."""
        self._default_font = None
        self._default_font_size = None
        self._default_fg_hex = "#000000"
        self._named_style_sizes = {}

        if not document_tab.namedStyles or not document_tab.namedStyles.styles:
            return
        for ns in document_tab.namedStyles.styles:
            if ns.textStyle and ns.textStyle.fontSize and ns.textStyle.fontSize.magnitude is not None:
                if ns.namedStyleType:
                    self._named_style_sizes[ns.namedStyleType] = ns.textStyle.fontSize.magnitude
            if ns.namedStyleType == "NORMAL_TEXT" and ns.textStyle:
                ts = ns.textStyle
                if ts.weightedFontFamily and ts.weightedFontFamily.fontFamily:
                    self._default_font = ts.weightedFontFamily.fontFamily
                if ts.fontSize and ts.fontSize.magnitude is not None:
                    self._default_font_size = ts.fontSize.magnitude
                fg = _optional_color_to_hex(ts.foregroundColor)
                if fg:
                    self._default_fg_hex = fg

    def _extract_non_default_style(self, style: TextStyle | None) -> dict[str, Any] | None:
        """Return a dict of non-default style properties, or None if all defaults."""
        if not style:
            return None

        props: dict[str, Any] = {}

        fg = _optional_color_to_hex(style.foregroundColor)
        if fg and fg != self._default_fg_hex:
            props["color"] = fg

        bg = _optional_color_to_hex(style.backgroundColor)
        if bg:
            props["background-color"] = bg

        if style.fontSize and style.fontSize.magnitude is not None:
            expected_size = self._default_font_size
            if self._current_para_style and self._current_para_style in self._named_style_sizes:
                expected_size = self._named_style_sizes[self._current_para_style]
            if style.fontSize.magnitude != expected_size:
                props["font-size"] = style.fontSize.magnitude

        if style.weightedFontFamily and style.weightedFontFamily.fontFamily:
            font = style.weightedFontFamily.fontFamily
            if font != self._default_font and font not in _COMMON_GDOCS_FONTS:
                props["font-family"] = font

        if style.baselineOffset and style.baselineOffset not in ("BASELINE_OFFSET_UNSPECIFIED", "NONE"):
            props["baseline-offset"] = style.baselineOffset

        if style.smallCaps:
            props["small-caps"] = True

        return props or None

    # ------------------------------------------------------------------
    # Headers and Footers
    # ------------------------------------------------------------------

    def _serialize_headers(self, headers: dict[str, Any] | None) -> list[str]:
        """Serialize document headers as comment-wrapped blocks."""
        if not headers:
            return []
        result: list[str] = []
        for header_id, raw in headers.items():
            header = raw if isinstance(raw, Header) else Header.model_validate(raw)
            if not header.content:
                continue
            blocks = group_elements(header.content)
            parts: list[str] = []
            for block in blocks:
                r = self._visit_block(block)
                if r is not None and r.strip():
                    parts.append(r)
            if parts:
                inner = "\n\n".join(parts)
                data: dict[str, Any] = {"id": header_id}
                result.append(f"{opening_tag(TagType.HEADER, data)}\n{inner}\n{_closing_tag_str(TagType.HEADER)}")
        return result

    def _serialize_footers(self, footers: dict[str, Any] | None) -> list[str]:
        """Serialize document footers as comment-wrapped blocks."""
        if not footers:
            return []
        result: list[str] = []
        for footer_id, raw in footers.items():
            footer = raw if isinstance(raw, Footer) else Footer.model_validate(raw)
            if not footer.content:
                continue
            blocks = group_elements(footer.content)
            parts: list[str] = []
            for block in blocks:
                r = self._visit_block(block)
                if r is not None and r.strip():
                    parts.append(r)
            if parts:
                inner = "\n\n".join(parts)
                data: dict[str, Any] = {"id": footer_id}
                result.append(f"{opening_tag(TagType.FOOTER, data)}\n{inner}\n{_closing_tag_str(TagType.FOOTER)}")
        return result


def _closing_tag_str(tag_type: TagType | str) -> str:
    """Generate a closing comment tag string."""
    return f"<!-- /{tag_type} -->"


def _optional_color_to_hex(color: OptionalColor | None) -> str | None:
    """Convert an OptionalColor to a hex string like ``#FF0000``.

    Returns ``None`` if the color is unset, transparent, or has no RGB values.
    """
    if not color or not color.color or not color.color.rgbColor:
        return None
    rgb = color.color.rgbColor
    r = int((rgb.red or 0) * 255)
    g = int((rgb.green or 0) * 255)
    b = int((rgb.blue or 0) * 255)
    if r == 0 and g == 0 and b == 0:
        return None
    return f"#{r:02X}{g:02X}{b:02X}"


def _escape_pipe(text: str) -> str:
    """Escape literal pipe characters so they don't break table structure."""
    return text.replace("|", "\\|")


def _apply_inline_formatting(
    text: str,
    *,
    bold: bool,
    italic: bool,
    strikethrough: bool = False,
    underline: bool = False,
) -> str:
    """Wrap text in Markdown formatting markers, preserving surrounding whitespace.

    Leading and trailing whitespace is kept outside the markers so that
    ``" hello "`` with bold becomes ``" **hello** "`` rather than
    ``"** hello **"`` (which is invalid Markdown).
    """
    if not text or (not bold and not italic and not strikethrough and not underline):
        return text

    stripped = text.lstrip()
    leading = text[: len(text) - len(stripped)]
    inner = stripped.rstrip()
    trailing = stripped[len(inner) :]

    if not inner:
        return text

    if bold and italic:
        inner = f"***{inner}***"
    elif bold:
        inner = f"**{inner}**"
    elif italic:
        inner = f"*{inner}*"

    if strikethrough:
        inner = f"~~{inner}~~"

    if underline:
        inner = f"<u>{inner}</u>"

    return f"{leading}{inner}{trailing}"


def _apply_link(text: str, url: str) -> str:
    """Wrap text in a Markdown link, preserving surrounding whitespace."""
    if not text:
        return text

    stripped = text.lstrip()
    leading = text[: len(text) - len(stripped)]
    inner = stripped.rstrip()
    trailing = stripped[len(inner) :]

    if not inner:
        return text

    return f"{leading}[{inner}]({url}){trailing}"


def _join_paragraphs(paragraphs: list[str]) -> str:
    """Join serialized paragraphs with blank-line separation.

    Runs of three or more consecutive newlines (from empty paragraphs) are
    collapsed to exactly two (one blank line). The result always ends with
    a single trailing newline.
    """
    if not paragraphs:
        return ""

    result = "\n\n".join(paragraphs)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.rstrip("\n") + "\n"
