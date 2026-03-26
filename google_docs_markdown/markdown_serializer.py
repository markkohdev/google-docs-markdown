"""Markdown serializer for Google Docs Pydantic models.

Converts DocumentTab Pydantic models into Markdown text using a visitor-style
traversal of the document tree.

Phase 1 scope: text, headings, paragraphs, bold, italic, line breaks.
Phase 2.1 scope: links, strikethrough, underline, rich links, horizontal
rules, footnote references and footnote content.
Phase 2.2 scope: lists (ordered, unordered, nested) via block grouper
pre-processing pass.

Unsupported element types (tables, images, code blocks, etc.) are silently
skipped and will be added in later phases.
"""

from __future__ import annotations

import re
from typing import Any

from google_docs_markdown.block_grouper import (
    Block,
    ListBlock,
    group_elements,
)
from google_docs_markdown.models.common import Footnote
from google_docs_markdown.models.document import DocumentTab
from google_docs_markdown.models.elements import (
    FootnoteReference,
    HorizontalRule,
    Paragraph,
    ParagraphElement,
    RichLink,
    StructuralElement,
    TextRun,
)

_HEADING_PREFIX: dict[str, str] = {
    "TITLE": "#",
    "HEADING_1": "#",
    "HEADING_2": "##",
    "HEADING_3": "###",
    "HEADING_4": "####",
    "HEADING_5": "#####",
    "HEADING_6": "######",
}


class MarkdownSerializer:
    """Serialize a DocumentTab Pydantic model into Markdown text.

    Traverses DocumentTab -> Body -> StructuralElement -> Paragraph ->
    ParagraphElement -> TextRun, emitting Markdown along the way.
    """

    def __init__(self) -> None:
        self._footnote_refs: list[tuple[str, str]] = []

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

        blocks = group_elements(document_tab.body.content, document_tab.lists)

        paragraphs: list[str] = []
        for block in blocks:
            result = self._visit_block(block)
            if result is not None:
                paragraphs.append(result)

        footnote_defs = self._serialize_footnotes(document_tab.footnotes)
        if footnote_defs:
            paragraphs.extend(footnote_defs)

        return _join_paragraphs(paragraphs)

    def _visit_block(self, block: Block) -> str | None:
        """Dispatch a Block to the appropriate visitor."""
        if isinstance(block, ListBlock):
            return self._visit_list_block(block)
        return self._visit_structural_element(block)

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
        return None

    def _visit_paragraph(self, paragraph: Paragraph) -> str:
        """Return Markdown for a Paragraph (heading, subtitle, or body text)."""
        style_type = None
        if paragraph.paragraphStyle:
            style_type = paragraph.paragraphStyle.namedStyleType

        text = self._collect_paragraph_text(paragraph.elements or [])

        heading_prefix = _HEADING_PREFIX.get(style_type or "")
        if heading_prefix and text:
            return f"{heading_prefix} {text}"

        if style_type == "SUBTITLE" and text:
            return f"*{text}*"

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
        return None

    def _visit_text_run(self, text_run: TextRun) -> str | None:
        """Return text content with Markdown formatting applied."""
        content = text_run.content
        if content is None:
            return None

        style = text_run.textStyle
        bold = style and style.bold
        italic = style and style.italic
        strikethrough = style and style.strikethrough
        link = style and style.link
        underline = style and style.underline and not link

        has_formatting = bold or italic or strikethrough or underline
        if has_formatting:
            content = _apply_inline_formatting(
                content,
                bold=bool(bold),
                italic=bool(italic),
                strikethrough=bool(strikethrough),
                underline=bool(underline),
            )

        if link and link.url:
            content = _apply_link(content, link.url)

        return content

    def _visit_horizontal_rule(self, _rule: HorizontalRule) -> str:
        return "---"

    def _visit_rich_link(self, rich_link: RichLink) -> str | None:
        props = rich_link.richLinkProperties
        if not props or not props.uri:
            return None
        title = props.title or props.uri
        return f"[{title}]({props.uri})"

    def _visit_footnote_reference(self, ref: FootnoteReference) -> str | None:
        if not ref.footnoteNumber:
            return None
        if ref.footnoteId:
            self._footnote_refs.append((ref.footnoteId, ref.footnoteNumber))
        return f"[^{ref.footnoteNumber}]"


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
