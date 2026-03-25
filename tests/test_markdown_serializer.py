"""Tests for the MarkdownSerializer.

Tests use both the real JSON fixtures and hand-crafted Pydantic models
to verify heading levels, formatting, whitespace, and determinism.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from google_docs_markdown.markdown_serializer import (
    MarkdownSerializer,
    _apply_inline_formatting,
    _join_paragraphs,
)
from google_docs_markdown.models import Document
from google_docs_markdown.models.document import Body, DocumentTab
from google_docs_markdown.models.elements import (
    Paragraph,
    ParagraphElement,
    StructuralElement,
    TextRun,
)
from google_docs_markdown.models.styles import ParagraphStyle, TextStyle

RESOURCES_DIR = Path(__file__).parent / "resources" / "document_jsons"
SINGLE_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Single-Tab.json"
MULTI_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Multi-Tab.json"


@pytest.fixture
def serializer() -> MarkdownSerializer:
    return MarkdownSerializer()


def _load_document(path: Path) -> Document:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return Document.model_validate(raw)


def _make_doc_tab(
    paragraphs: list[tuple[str, str | None]],
) -> DocumentTab:
    """Build a minimal DocumentTab from (text, namedStyleType) pairs."""
    elements: list[StructuralElement] = []
    for text, style_type in paragraphs:
        para_style = ParagraphStyle(namedStyleType=style_type) if style_type else None
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content=text + "\n")),
            ],
            paragraphStyle=para_style,
        )
        elements.append(StructuralElement(paragraph=para))
    return DocumentTab(body=Body(content=elements))


# ---------------------------------------------------------------------------
# Unit tests for _apply_inline_formatting
# ---------------------------------------------------------------------------


class TestApplyInlineFormatting:
    def test_bold(self) -> None:
        assert _apply_inline_formatting("hello", bold=True, italic=False) == "**hello**"

    def test_italic(self) -> None:
        assert _apply_inline_formatting("hello", bold=False, italic=True) == "*hello*"

    def test_bold_italic(self) -> None:
        assert _apply_inline_formatting("hello", bold=True, italic=True) == "***hello***"

    def test_preserves_leading_whitespace(self) -> None:
        assert _apply_inline_formatting("  hello", bold=True, italic=False) == "  **hello**"

    def test_preserves_trailing_whitespace(self) -> None:
        assert _apply_inline_formatting("hello  ", bold=True, italic=False) == "**hello**  "

    def test_preserves_both_whitespace(self) -> None:
        assert _apply_inline_formatting(" hello ", bold=False, italic=True) == " *hello* "

    def test_all_whitespace_returns_unchanged(self) -> None:
        assert _apply_inline_formatting("   ", bold=True, italic=False) == "   "

    def test_empty_string(self) -> None:
        assert _apply_inline_formatting("", bold=True, italic=False) == ""

    def test_no_formatting(self) -> None:
        assert _apply_inline_formatting("hello", bold=False, italic=False) == "hello"


# ---------------------------------------------------------------------------
# Unit tests for _join_paragraphs
# ---------------------------------------------------------------------------


class TestJoinParagraphs:
    def test_empty(self) -> None:
        assert _join_paragraphs([]) == ""

    def test_single(self) -> None:
        assert _join_paragraphs(["Hello"]) == "Hello\n"

    def test_two_paragraphs(self) -> None:
        assert _join_paragraphs(["A", "B"]) == "A\n\nB\n"

    def test_collapses_empty_paragraphs(self) -> None:
        result = _join_paragraphs(["A", "", "B"])
        assert result == "A\n\nB\n"

    def test_collapses_multiple_empty_paragraphs(self) -> None:
        result = _join_paragraphs(["A", "", "", "B"])
        assert result == "A\n\nB\n"

    def test_trailing_newline(self) -> None:
        result = _join_paragraphs(["Hello"])
        assert result.endswith("\n")
        assert not result.endswith("\n\n")


# ---------------------------------------------------------------------------
# MarkdownSerializer unit tests with hand-crafted models
# ---------------------------------------------------------------------------


class TestSerializerBasic:
    def test_empty_document_tab(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab()
        assert serializer.serialize(doc_tab) == ""

    def test_empty_body(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(body=Body(content=[]))
        assert serializer.serialize(doc_tab) == ""

    def test_normal_text(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([("Hello world", "NORMAL_TEXT")])
        result = serializer.serialize(doc_tab)
        assert result == "Hello world\n"

    def test_title(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([("My Document", "TITLE")])
        result = serializer.serialize(doc_tab)
        assert result == "# My Document\n"

    def test_subtitle(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([("A subtitle", "SUBTITLE")])
        result = serializer.serialize(doc_tab)
        assert result == "*A subtitle*\n"

    def test_all_heading_levels(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([
            ("Title", "TITLE"),
            ("H1", "HEADING_1"),
            ("H2", "HEADING_2"),
            ("H3", "HEADING_3"),
            ("H4", "HEADING_4"),
            ("H5", "HEADING_5"),
            ("H6", "HEADING_6"),
        ])
        result = serializer.serialize(doc_tab)
        lines = result.strip().split("\n\n")
        assert lines[0] == "# Title"
        assert lines[1] == "# H1"
        assert lines[2] == "## H2"
        assert lines[3] == "### H3"
        assert lines[4] == "#### H4"
        assert lines[5] == "##### H5"
        assert lines[6] == "###### H6"

    def test_bold_text(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="bold text", textStyle=TextStyle(bold=True))),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "**bold text**\n"

    def test_italic_text(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="italic text", textStyle=TextStyle(italic=True))),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "*italic text*\n"

    def test_bold_italic_text(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(
                    textRun=TextRun(content="bold italic", textStyle=TextStyle(bold=True, italic=True))
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "***bold italic***\n"

    def test_mixed_formatting_inline(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Normal ")),
                ParagraphElement(textRun=TextRun(content="bold", textStyle=TextStyle(bold=True))),
                ParagraphElement(textRun=TextRun(content=" and ")),
                ParagraphElement(textRun=TextRun(content="italic", textStyle=TextStyle(italic=True))),
                ParagraphElement(textRun=TextRun(content=" text\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "Normal **bold** and *italic* text\n"

    def test_skips_unsupported_structural_elements(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import SectionBreak, Table

        doc_tab = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(sectionBreak=SectionBreak()),
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="Hello\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                    StructuralElement(table=Table(rows=1, columns=1)),
                ]
            )
        )
        result = serializer.serialize(doc_tab)
        assert result == "Hello\n"

    def test_skips_unsupported_paragraph_elements(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import InlineObjectElement, Person

        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Before ")),
                ParagraphElement(person=Person(personId="p1")),
                ParagraphElement(textRun=TextRun(content=" after\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "Before  after\n"

    def test_empty_paragraph_becomes_blank_line(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([
            ("Hello", "NORMAL_TEXT"),
            ("", "NORMAL_TEXT"),
            ("World", "NORMAL_TEXT"),
        ])
        result = serializer.serialize(doc_tab)
        assert result == "Hello\n\nWorld\n"

    def test_deterministic_output(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([
            ("Title", "TITLE"),
            ("Some text", "NORMAL_TEXT"),
            ("Heading", "HEADING_2"),
        ])
        result1 = serializer.serialize(doc_tab)
        result2 = serializer.serialize(doc_tab)
        assert result1 == result2


# ---------------------------------------------------------------------------
# Integration tests with real JSON fixtures
# ---------------------------------------------------------------------------


class TestSerializerFixtures:
    def test_single_tab_fixture_basic_structure(self, serializer: MarkdownSerializer) -> None:
        """Verify the single-tab fixture produces expected heading hierarchy."""
        doc = _load_document(SINGLE_TAB_JSON)
        assert doc.tabs and len(doc.tabs) == 1

        tab = doc.tabs[0]
        assert tab.documentTab is not None
        result = serializer.serialize(tab.documentTab)

        assert result.startswith("# Markdown Conversion Example - Single Tab\n")
        assert "\n\n*Document Subtitle*\n\n" in result
        assert "\n\n# Project Overview: Markdown Tool Testing (Heading 1)\n\n" in result
        assert "\n\n## Section 1: Headings and Structure (Heading 2)\n\n" in result
        assert "\n\n### Subsection 1.1: Lower Level Headings (Heading 3)\n\n" in result
        assert "\n\n#### Sub-Subsection 1.1.1: Deeper Dive (Heading 4)\n\n" in result
        assert "\n\n##### Sub-Sub-Subsection 1.1.1.1: Specific Detail (Heading 5)\n\n" in result
        assert "\n\n###### Sub-Sub-Sub-Subsection 1.1.1.1.1: Very detailed Level (Heading 6)\n\n" in result

    def test_single_tab_bold_italic(self, serializer: MarkdownSerializer) -> None:
        """Verify bold and italic formatting are applied in the fixture."""
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]

        assert "**should be bold**" in result
        assert "*should be italic*" in result

    def test_single_tab_deterministic(self, serializer: MarkdownSerializer) -> None:
        """Same fixture must produce identical output across multiple runs."""
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        r1 = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        r2 = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        assert r1 == r2

    def test_single_tab_ends_with_single_newline(self, serializer: MarkdownSerializer) -> None:
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_single_tab_no_triple_newlines(self, serializer: MarkdownSerializer) -> None:
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        assert "\n\n\n" not in result

    def test_multi_tab_first_tab_structure(self, serializer: MarkdownSerializer) -> None:
        """The first tab of multi-tab has the same structure as single-tab (different title)."""
        multi = _load_document(MULTI_TAB_JSON)
        result = serializer.serialize(multi.tabs[0].documentTab)  # type: ignore

        assert result.startswith("# Markdown Conversion Example - Multi-Tab\n")
        assert "**should be bold**" in result
        assert "*should be italic*" in result
        assert "\n\n## Section 1: Headings and Structure (Heading 2)\n\n" in result

    def test_multi_tab_nested_tabs(self, serializer: MarkdownSerializer) -> None:
        """The multi-tab fixture has nested child/grandchild tabs."""
        doc = _load_document(MULTI_TAB_JSON)
        assert doc.tabs and len(doc.tabs) == 2

        parent_tab = doc.tabs[1]
        assert parent_tab.tabProperties and parent_tab.tabProperties.title == "Tab with child tab"
        parent_result = serializer.serialize(parent_tab.documentTab)  # type: ignore[arg-type]
        assert "I am the content of the tab with the child tab" in parent_result

        assert parent_tab.childTabs and len(parent_tab.childTabs) == 1
        child_tab = parent_tab.childTabs[0]
        assert child_tab.tabProperties and child_tab.tabProperties.title == "Child tab"
        child_result = serializer.serialize(child_tab.documentTab)  # type: ignore[arg-type]
        assert "I am the content of the child tab which has a grandchild tab" in child_result

        assert child_tab.childTabs and len(child_tab.childTabs) == 1
        grandchild_tab = child_tab.childTabs[0]
        assert grandchild_tab.tabProperties and grandchild_tab.tabProperties.title == "Grandchild tab"
        grandchild_result = serializer.serialize(grandchild_tab.documentTab)  # type: ignore[arg-type]
        assert "I am the content of the grandchild tab" in grandchild_result
