"""Markdown serializer for Google Docs Pydantic models.

Converts DocumentTab Pydantic models into Markdown text using a visitor-style
traversal of the document tree.

Phase 1 scope: handles text, headings, paragraphs, bold, italic, and line
breaks. Unsupported element types (tables, images, lists, etc.) are silently
skipped and will be added in Phase 2.
"""

from __future__ import annotations

import re

from google_docs_markdown.models.document import DocumentTab
from google_docs_markdown.models.elements import (
    Paragraph,
    ParagraphElement,
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

        paragraphs: list[str] = []
        for element in document_tab.body.content:
            result = self._visit_structural_element(element)
            if result is not None:
                paragraphs.append(result)

        return _join_paragraphs(paragraphs)

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
        # Strip the trailing newline the API uses as a paragraph terminator,
        # plus any orphaned trailing whitespace.
        return text.rstrip()

    def _visit_paragraph_element(self, element: ParagraphElement) -> str | None:
        """Return inline text for a ParagraphElement, or None to skip."""
        if element.textRun:
            return self._visit_text_run(element.textRun)
        return None

    def _visit_text_run(self, text_run: TextRun) -> str | None:
        """Return text content with bold/italic Markdown markers applied."""
        content = text_run.content
        if content is None:
            return None

        bold = text_run.textStyle and text_run.textStyle.bold
        italic = text_run.textStyle and text_run.textStyle.italic

        if not bold and not italic:
            return content

        return _apply_inline_formatting(content, bold=bool(bold), italic=bool(italic))


def _apply_inline_formatting(text: str, *, bold: bool, italic: bool) -> str:
    """Wrap text in Markdown bold/italic markers, preserving surrounding whitespace.

    Leading and trailing whitespace is kept outside the markers so that
    ``" hello "`` with bold becomes ``" **hello** "`` rather than
    ``"** hello **"`` (which is invalid Markdown).
    """
    if not text or (not bold and not italic):
        return text

    stripped = text.lstrip()
    leading = text[: len(text) - len(stripped)]
    inner = stripped.rstrip()
    trailing = stripped[len(inner) :]

    if not inner:
        return text

    if bold and italic:
        return f"{leading}***{inner}***{trailing}"
    if bold:
        return f"{leading}**{inner}**{trailing}"
    return f"{leading}*{inner}*{trailing}"


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
