"""Tests for the MarkdownSerializer.

Tests use both the real JSON fixtures and hand-crafted Pydantic models
to verify heading levels, formatting, whitespace, and determinism.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import pytest

from google_docs_markdown.markdown_serializer import (
    MarkdownSerializer,
    _apply_inline_formatting,
    _apply_link,
    _join_paragraphs,
)
from google_docs_markdown.models import Document
from google_docs_markdown.models.common import Footnote, Link, RichLinkProperties
from google_docs_markdown.models.document import Body, DocumentTab
from google_docs_markdown.models.elements import (
    FootnoteReference,
    HorizontalRule,
    Paragraph,
    ParagraphElement,
    RichLink,
    StructuralElement,
    TableCell,
    TableRow,
    TextRun,
)
from google_docs_markdown.models.styles import ParagraphStyle, TextStyle

RESOURCES_DIR = Path(__file__).parent / "resources" / "document_jsons"
SINGLE_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Single-Tab.json"
MULTI_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Multi-Tab.json"

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


@pytest.fixture
def serializer() -> MarkdownSerializer:
    return MarkdownSerializer()


def _load_document(path: Path) -> Document:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return Document.model_validate(raw)


def _make_doc_tab(
    paragraphs: list[tuple[str, _NamedStyleType | None]],
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

    def test_strikethrough(self) -> None:
        assert _apply_inline_formatting("hello", bold=False, italic=False, strikethrough=True) == "~~hello~~"

    def test_underline(self) -> None:
        assert _apply_inline_formatting("hello", bold=False, italic=False, underline=True) == "<u>hello</u>"

    def test_bold_strikethrough(self) -> None:
        result = _apply_inline_formatting("hello", bold=True, italic=False, strikethrough=True)
        assert result == "~~**hello**~~"

    def test_italic_underline(self) -> None:
        result = _apply_inline_formatting("hello", bold=False, italic=True, underline=True)
        assert result == "<u>*hello*</u>"

    def test_all_formatting(self) -> None:
        result = _apply_inline_formatting("hello", bold=True, italic=True, strikethrough=True, underline=True)
        assert result == "<u>~~***hello***~~</u>"

    def test_strikethrough_preserves_whitespace(self) -> None:
        assert _apply_inline_formatting(" hello ", bold=False, italic=False, strikethrough=True) == " ~~hello~~ "

    def test_underline_preserves_whitespace(self) -> None:
        assert _apply_inline_formatting(" hello ", bold=False, italic=False, underline=True) == " <u>hello</u> "


# ---------------------------------------------------------------------------
# Unit tests for _apply_link
# ---------------------------------------------------------------------------


class TestApplyLink:
    def test_basic_link(self) -> None:
        assert _apply_link("click here", "https://example.com") == "[click here](https://example.com)"

    def test_preserves_leading_whitespace(self) -> None:
        assert _apply_link("  click", "https://example.com") == "  [click](https://example.com)"

    def test_preserves_trailing_whitespace(self) -> None:
        assert _apply_link("click  ", "https://example.com") == "[click](https://example.com)  "

    def test_preserves_both_whitespace(self) -> None:
        assert _apply_link(" click ", "https://example.com") == " [click](https://example.com) "

    def test_empty_string(self) -> None:
        assert _apply_link("", "https://example.com") == ""

    def test_all_whitespace(self) -> None:
        assert _apply_link("   ", "https://example.com") == "   "

    def test_formatted_content(self) -> None:
        assert _apply_link("**bold**", "https://example.com") == "[**bold**](https://example.com)"


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
        assert result == "<!-- title -->\n# My Document\n"

    def test_subtitle(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([("A subtitle", "SUBTITLE")])
        result = serializer.serialize(doc_tab)
        assert result == "<!-- subtitle -->\n*A subtitle*\n"

    def test_all_heading_levels(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab(
            [
                ("Title", "TITLE"),
                ("H1", "HEADING_1"),
                ("H2", "HEADING_2"),
                ("H3", "HEADING_3"),
                ("H4", "HEADING_4"),
                ("H5", "HEADING_5"),
                ("H6", "HEADING_6"),
            ]
        )
        result = serializer.serialize(doc_tab)
        lines = result.strip().split("\n\n")
        assert lines[0] == "<!-- title -->\n# Title"
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
                ParagraphElement(textRun=TextRun(content="bold italic", textStyle=TextStyle(bold=True, italic=True))),
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
        from google_docs_markdown.models.elements import SectionBreak

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
                ]
            )
        )
        result = serializer.serialize(doc_tab)
        assert result == "Hello\n"

    def test_skips_unsupported_paragraph_elements(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import Person

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

    def test_link_text(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(
                    textRun=TextRun(
                        content="click here",
                        textStyle=TextStyle(link=Link(url="https://example.com")),
                    )
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "[click here](https://example.com)\n"

    def test_link_with_bold(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(
                    textRun=TextRun(
                        content="bold link",
                        textStyle=TextStyle(bold=True, link=Link(url="https://example.com")),
                    )
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "[**bold link**](https://example.com)\n"

    def test_link_ignores_underline(self, serializer: MarkdownSerializer) -> None:
        """Links in Google Docs automatically have underline=True; it should be ignored."""
        para = Paragraph(
            elements=[
                ParagraphElement(
                    textRun=TextRun(
                        content="my link",
                        textStyle=TextStyle(underline=True, link=Link(url="https://example.com")),
                    )
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "[my link](https://example.com)\n"
        assert "<u>" not in result

    def test_heading_link_no_url(self, serializer: MarkdownSerializer) -> None:
        """Links to headings (no URL) should not produce link syntax."""
        from google_docs_markdown.models.common import HeadingLink

        para = Paragraph(
            elements=[
                ParagraphElement(
                    textRun=TextRun(
                        content="section ref",
                        textStyle=TextStyle(link=Link(heading=HeadingLink(id="h.abc"))),
                    )
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "section ref\n"

    def test_strikethrough_text(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="deleted", textStyle=TextStyle(strikethrough=True))),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "~~deleted~~\n"

    def test_underline_text(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="underlined", textStyle=TextStyle(underline=True))),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "<u>underlined</u>\n"

    def test_horizontal_rule(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="Above\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(horizontalRule=HorizontalRule())],
                        )
                    ),
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="Below\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                ]
            )
        )
        result = serializer.serialize(doc_tab)
        assert "---" in result
        assert result == "Above\n\n---\n\nBelow\n"

    def test_rich_link(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(
                    richLink=RichLink(richLinkProperties=RichLinkProperties(title="Google", uri="https://google.com"))
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "[Google](https://google.com)\n"

    def test_rich_link_no_title_uses_uri(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(richLink=RichLink(richLinkProperties=RichLinkProperties(uri="https://google.com"))),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "[https://google.com](https://google.com)\n"

    def test_rich_link_no_uri_skipped(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(richLink=RichLink(richLinkProperties=RichLinkProperties(title="Missing"))),
                ParagraphElement(textRun=TextRun(content="text\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "text\n"

    def test_footnote_reference(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Some claim")),
                ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn1", footnoteNumber="1")),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        footnotes = {
            "fn1": {
                "footnoteId": "fn1",
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Source: Wikipedia\n"}}],
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        }
                    }
                ],
            }
        }
        doc_tab = DocumentTab(
            body=Body(content=[StructuralElement(paragraph=para)]),
            footnotes=footnotes,
        )
        result = serializer.serialize(doc_tab)
        assert "[^1]" in result
        assert "[^1]: Source: Wikipedia" in result

    def test_multiple_footnotes(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="First")),
                ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn1", footnoteNumber="1")),
                ParagraphElement(textRun=TextRun(content=" and second")),
                ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn2", footnoteNumber="2")),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        footnotes = {
            "fn1": {
                "footnoteId": "fn1",
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "First note\n"}}],
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        }
                    }
                ],
            },
            "fn2": {
                "footnoteId": "fn2",
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Second note\n"}}],
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                        }
                    }
                ],
            },
        }
        doc_tab = DocumentTab(
            body=Body(content=[StructuralElement(paragraph=para)]),
            footnotes=footnotes,
        )
        result = serializer.serialize(doc_tab)
        assert "First[^1] and second[^2]" in result
        assert "[^1]: First note" in result
        assert "[^2]: Second note" in result

    def test_footnote_no_content_no_crash(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Text")),
                ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn1", footnoteNumber="1")),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(
            body=Body(content=[StructuralElement(paragraph=para)]),
            footnotes={},
        )
        result = serializer.serialize(doc_tab)
        assert "Text[^1]" in result
        assert "[^1]:" not in result

    def test_footnote_with_pydantic_model(self, serializer: MarkdownSerializer) -> None:
        """Footnotes dict can contain pre-validated Pydantic Footnote objects."""
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Claim")),
                ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn1", footnoteNumber="1")),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        fn_content = StructuralElement(
            paragraph=Paragraph(
                elements=[ParagraphElement(textRun=TextRun(content="A Pydantic footnote\n"))],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        footnotes: dict[str, Any] = {
            "fn1": Footnote(footnoteId="fn1", content=[fn_content]),
        }
        doc_tab = DocumentTab(
            body=Body(content=[StructuralElement(paragraph=para)]),
            footnotes=footnotes,
        )
        result = serializer.serialize(doc_tab)
        assert "[^1]: A Pydantic footnote" in result

    def test_mixed_inline_with_link(self, serializer: MarkdownSerializer) -> None:
        """Bold + italic + strikethrough + link all combined."""
        para = Paragraph(
            elements=[
                ParagraphElement(
                    textRun=TextRun(
                        content="styled link",
                        textStyle=TextStyle(
                            bold=True,
                            italic=True,
                            strikethrough=True,
                            link=Link(url="https://example.com"),
                        ),
                    )
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert result == "[~~***styled link***~~](https://example.com)\n"

    def test_empty_paragraph_becomes_blank_line(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab(
            [
                ("Hello", "NORMAL_TEXT"),
                ("", "NORMAL_TEXT"),
                ("World", "NORMAL_TEXT"),
            ]
        )
        result = serializer.serialize(doc_tab)
        assert result == "Hello\n\nWorld\n"

    def test_deterministic_output(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab(
            [
                ("Title", "TITLE"),
                ("Some text", "NORMAL_TEXT"),
                ("Heading", "HEADING_2"),
            ]
        )
        result1 = serializer.serialize(doc_tab)
        result2 = serializer.serialize(doc_tab)
        assert result1 == result2


# ---------------------------------------------------------------------------
# List serialization tests (Phase 2.2)
# ---------------------------------------------------------------------------


def _list_para(text: str, list_id: str, nesting: int = 0) -> StructuralElement:
    """Build a StructuralElement for a list-item paragraph."""
    from google_docs_markdown.models.styles import Bullet

    return StructuralElement(
        paragraph=Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content=text + "\n"))],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            bullet=Bullet(listId=list_id, nestingLevel=nesting),
        )
    )


def _lists_ctx(entries: dict[str, str]) -> dict[str, Any]:
    """Build a lists context: listId -> glyphType (uniform across nesting levels)."""
    ctx: dict[str, Any] = {}
    for list_id, glyph_type in entries.items():
        ctx[list_id] = {
            "listProperties": {"nestingLevels": [{"glyphType": glyph_type, "startNumber": 1} for _ in range(9)]}
        }
    return ctx


class TestSerializerLists:
    def test_unordered_list(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    _list_para("Apple", "kix.a"),
                    _list_para("Banana", "kix.a"),
                    _list_para("Cherry", "kix.a"),
                ]
            ),
            lists=_lists_ctx({"kix.a": "GLYPH_TYPE_UNSPECIFIED"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "- Apple\n- Banana\n- Cherry\n"

    def test_ordered_list(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    _list_para("First", "kix.n"),
                    _list_para("Second", "kix.n"),
                    _list_para("Third", "kix.n"),
                ]
            ),
            lists=_lists_ctx({"kix.n": "DECIMAL"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "1. First\n1. Second\n1. Third\n"

    def test_nested_unordered_list(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    _list_para("Top", "kix.a"),
                    _list_para("Sub", "kix.a", nesting=1),
                    _list_para("SubSub", "kix.a", nesting=2),
                    _list_para("Back to top", "kix.a"),
                ]
            ),
            lists=_lists_ctx({"kix.a": "GLYPH_TYPE_UNSPECIFIED"}),
        )
        result = serializer.serialize(doc_tab)
        expected = "- Top\n    - Sub\n        - SubSub\n- Back to top\n"
        assert result == expected

    def test_list_between_paragraphs(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="Before list\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                    _list_para("Item 1", "kix.a"),
                    _list_para("Item 2", "kix.a"),
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="After list\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                ]
            ),
            lists=_lists_ctx({"kix.a": "GLYPH_TYPE_UNSPECIFIED"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "Before list\n\n- Item 1\n- Item 2\n\nAfter list\n"

    def test_two_separate_lists(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    _list_para("Bullet 1", "kix.a"),
                    _list_para("Bullet 2", "kix.a"),
                    _list_para("Number 1", "kix.b"),
                    _list_para("Number 2", "kix.b"),
                ]
            ),
            lists=_lists_ctx({"kix.a": "GLYPH_TYPE_UNSPECIFIED", "kix.b": "DECIMAL"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "- Bullet 1\n- Bullet 2\n\n1. Number 1\n1. Number 2\n"

    def test_list_with_formatted_text(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.styles import Bullet

        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Normal and ")),
                ParagraphElement(textRun=TextRun(content="bold", textStyle=TextStyle(bold=True))),
                ParagraphElement(textRun=TextRun(content=" text\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            bullet=Bullet(listId="kix.a"),
        )
        doc_tab = DocumentTab(
            body=Body(content=[StructuralElement(paragraph=para)]),
            lists=_lists_ctx({"kix.a": "GLYPH_TYPE_UNSPECIFIED"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "- Normal and **bold** text\n"

    def test_list_under_heading(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="My Heading\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="HEADING_2"),
                        )
                    ),
                    _list_para("Item A", "kix.a"),
                    _list_para("Item B", "kix.a"),
                ]
            ),
            lists=_lists_ctx({"kix.a": "GLYPH_TYPE_UNSPECIFIED"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "## My Heading\n\n- Item A\n- Item B\n"

    def test_mixed_nesting_ordered_unordered(self, serializer: MarkdownSerializer) -> None:
        """Unordered at level 0, ordered at level 1 (same listId)."""
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    _list_para("Top", "kix.mix"),
                    _list_para("Nested num", "kix.mix", nesting=1),
                    _list_para("Top again", "kix.mix"),
                ]
            ),
            lists={
                "kix.mix": {
                    "listProperties": {
                        "nestingLevels": [
                            {"glyphType": "GLYPH_TYPE_UNSPECIFIED", "startNumber": 1},
                            {"glyphType": "DECIMAL", "startNumber": 1},
                        ]
                    }
                }
            },
        )
        result = serializer.serialize(doc_tab)
        assert result == "- Top\n    1. Nested num\n- Top again\n"

    def test_no_lists_context_still_renders(self, serializer: MarkdownSerializer) -> None:
        """If lists context is None, default to unordered."""
        doc_tab = DocumentTab(
            body=Body(content=[_list_para("Orphan item", "kix.a")]),
        )
        result = serializer.serialize(doc_tab)
        assert result == "- Orphan item\n"

    def test_alpha_ordered_list(self, serializer: MarkdownSerializer) -> None:
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    _list_para("Alpha A", "kix.alpha"),
                    _list_para("Alpha B", "kix.alpha"),
                ]
            ),
            lists=_lists_ctx({"kix.alpha": "UPPER_ALPHA"}),
        )
        result = serializer.serialize(doc_tab)
        assert result == "1. Alpha A\n1. Alpha B\n"


# ---------------------------------------------------------------------------
# Table serialization tests (Phase 2.3)
# ---------------------------------------------------------------------------


def _table_cell(text: str, bold: bool = False) -> TableCell:
    """Build a TableCell containing a single paragraph with optional bold."""
    style = TextStyle(bold=True) if bold else None
    return TableCell(
        content=[
            StructuralElement(
                paragraph=Paragraph(
                    elements=[
                        ParagraphElement(textRun=TextRun(content=text + "\n", textStyle=style)),
                    ],
                    paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                )
            )
        ]
    )


def _table_row(cells: list[TableCell], header: bool = False) -> TableRow:
    """Build a TableRow with optional header flag."""
    from google_docs_markdown.models.styles import TableRowStyle

    style = TableRowStyle(tableHeader=True) if header else None
    return TableRow(tableCells=cells, tableRowStyle=style)


class TestSerializerTables:
    def test_basic_table_with_header(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import Table

        table = Table(
            rows=3,
            columns=2,
            tableRows=[
                _table_row([_table_cell("H1"), _table_cell("H2")], header=True),
                _table_row([_table_cell("A1"), _table_cell("A2")]),
                _table_row([_table_cell("B1"), _table_cell("B2")]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        expected = "| H1 | H2 |\n| --- | --- |\n| A1 | A2 |\n| B1 | B2 |\n"
        assert result == expected

    def test_table_without_explicit_header(self, serializer: MarkdownSerializer) -> None:
        """First row is used as header when no row has tableHeader=True."""
        from google_docs_markdown.models.elements import Table

        table = Table(
            rows=2,
            columns=2,
            tableRows=[
                _table_row([_table_cell("A1"), _table_cell("A2")]),
                _table_row([_table_cell("B1"), _table_cell("B2")]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        expected = "| A1 | A2 |\n| --- | --- |\n| B1 | B2 |\n"
        assert result == expected

    def test_table_with_bold_header_cells(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import Table

        table = Table(
            rows=2,
            columns=2,
            tableRows=[
                _table_row(
                    [_table_cell("Name", bold=True), _table_cell("Value", bold=True)],
                    header=True,
                ),
                _table_row([_table_cell("foo"), _table_cell("42")]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        assert "| **Name** | **Value** |" in result
        assert "| --- | --- |" in result
        assert "| foo | 42 |" in result

    def test_table_with_formatted_cell_content(self, serializer: MarkdownSerializer) -> None:
        """Cells with italic and link formatting."""
        from google_docs_markdown.models.elements import Table, TableCell, TableRow

        cell_with_italic = TableCell(
            content=[
                StructuralElement(
                    paragraph=Paragraph(
                        elements=[
                            ParagraphElement(textRun=TextRun(content="emphasis", textStyle=TextStyle(italic=True))),
                            ParagraphElement(textRun=TextRun(content="\n")),
                        ],
                        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                    )
                )
            ]
        )
        cell_with_link = TableCell(
            content=[
                StructuralElement(
                    paragraph=Paragraph(
                        elements=[
                            ParagraphElement(
                                textRun=TextRun(
                                    content="click",
                                    textStyle=TextStyle(link=Link(url="https://example.com")),
                                )
                            ),
                            ParagraphElement(textRun=TextRun(content="\n")),
                        ],
                        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                    )
                )
            ]
        )
        table = Table(
            rows=2,
            columns=2,
            tableRows=[
                _table_row([_table_cell("H1"), _table_cell("H2")], header=True),
                TableRow(tableCells=[cell_with_italic, cell_with_link]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        assert "| *emphasis* | [click](https://example.com) |" in result

    def test_table_with_multi_paragraph_cell(self, serializer: MarkdownSerializer) -> None:
        """Multiple paragraphs in a cell are joined with <br>."""
        from google_docs_markdown.models.elements import Table, TableCell, TableRow

        multi_para_cell = TableCell(
            content=[
                StructuralElement(
                    paragraph=Paragraph(
                        elements=[ParagraphElement(textRun=TextRun(content="Line 1\n"))],
                        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                    )
                ),
                StructuralElement(
                    paragraph=Paragraph(
                        elements=[ParagraphElement(textRun=TextRun(content="Line 2\n"))],
                        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                    )
                ),
            ]
        )
        table = Table(
            rows=2,
            columns=1,
            tableRows=[
                _table_row([_table_cell("Header")], header=True),
                TableRow(tableCells=[multi_para_cell]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        assert "| Line 1<br>Line 2 |" in result

    def test_table_with_pipe_in_content(self, serializer: MarkdownSerializer) -> None:
        """Pipe characters in cell text are escaped."""
        from google_docs_markdown.models.elements import Table

        table = Table(
            rows=2,
            columns=1,
            tableRows=[
                _table_row([_table_cell("Header")], header=True),
                _table_row([_table_cell("a | b")]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        assert "| a \\| b |" in result

    def test_single_row_table(self, serializer: MarkdownSerializer) -> None:
        """A table with only a header row and no data rows."""
        from google_docs_markdown.models.elements import Table

        table = Table(
            rows=1,
            columns=2,
            tableRows=[
                _table_row([_table_cell("Col A"), _table_cell("Col B")], header=True),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        expected = "| Col A | Col B |\n| --- | --- |\n"
        assert result == expected

    def test_table_with_empty_cells(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import Table, TableCell, TableRow

        table = Table(
            rows=2,
            columns=2,
            tableRows=[
                _table_row([_table_cell("H1"), _table_cell("H2")], header=True),
                TableRow(tableCells=[TableCell(content=[]), _table_cell("data")]),
            ],
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        assert "|  | data |" in result

    def test_table_no_rows_returns_empty(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.elements import Table

        table = Table(rows=0, columns=2, tableRows=[])
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(table=table)]))
        result = serializer.serialize(doc_tab)
        assert result == ""

    def test_table_between_paragraphs(self, serializer: MarkdownSerializer) -> None:
        """Table surrounded by regular paragraphs gets blank-line separation."""
        from google_docs_markdown.models.elements import Table

        table = Table(
            rows=2,
            columns=1,
            tableRows=[
                _table_row([_table_cell("H")], header=True),
                _table_row([_table_cell("D")]),
            ],
        )
        doc_tab = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="Before\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                    StructuralElement(table=table),
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="After\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    ),
                ]
            )
        )
        result = serializer.serialize(doc_tab)
        assert result == "Before\n\n| H |\n| --- |\n| D |\n\nAfter\n"


# ---------------------------------------------------------------------------
# Image tests
# ---------------------------------------------------------------------------


def _make_image_doc(
    object_id: str = "kix.img1",
    content_uri: str = "https://example.com/image.png",
    description: str | None = None,
    title: str | None = None,
) -> DocumentTab:
    """Build a DocumentTab with an inline image."""
    from google_docs_markdown.models.elements import InlineObjectElement

    elements: list[StructuralElement] = [
        StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        inlineObjectElement=InlineObjectElement(inlineObjectId=object_id),
                    ),
                    ParagraphElement(textRun=TextRun(content="\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
    ]

    embedded_obj: dict[str, Any] = {
        "imageProperties": {"contentUri": content_uri},
    }
    if description:
        embedded_obj["description"] = description
    if title:
        embedded_obj["title"] = title

    inline_objects = {
        object_id: {
            "objectId": object_id,
            "inlineObjectProperties": {"embeddedObject": embedded_obj},
        }
    }

    return DocumentTab(body=Body(content=elements), inlineObjects=inline_objects)


class TestSerializerImages:
    def test_image_basic(self, serializer: MarkdownSerializer) -> None:
        doc = _make_image_doc()
        result = serializer.serialize(doc)
        assert "![](https://example.com/image.png)" in result

    def test_image_with_description(self, serializer: MarkdownSerializer) -> None:
        doc = _make_image_doc(description="A cat photo")
        result = serializer.serialize(doc)
        assert "![A cat photo](https://example.com/image.png)" in result

    def test_image_with_title_fallback(self, serializer: MarkdownSerializer) -> None:
        doc = _make_image_doc(title="My Image")
        result = serializer.serialize(doc)
        assert "![My Image](https://example.com/image.png)" in result

    def test_image_description_preferred_over_title(self, serializer: MarkdownSerializer) -> None:
        doc = _make_image_doc(description="Alt text", title="Title text")
        result = serializer.serialize(doc)
        assert "![Alt text](https://example.com/image.png)" in result

    def test_image_no_inline_objects(self, serializer: MarkdownSerializer) -> None:
        """InlineObjectElement with no matching inlineObjects dict skips."""
        from google_docs_markdown.models.elements import InlineObjectElement

        doc = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[
                                ParagraphElement(
                                    inlineObjectElement=InlineObjectElement(inlineObjectId="missing"),
                                ),
                                ParagraphElement(textRun=TextRun(content="\n")),
                            ],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    )
                ]
            ),
        )
        result = serializer.serialize(doc)
        assert "![" not in result

    def test_image_with_properties_emits_tag(self, serializer: MarkdownSerializer) -> None:
        """Image with non-default size/crop/margins serializes an image-props comment tag."""
        from google_docs_markdown.models.elements import InlineObjectElement

        embedded_obj: dict[str, Any] = {
            "imageProperties": {
                "contentUri": "https://example.com/img.png",
                "cropProperties": {"offsetRight": 0.705},
            },
            "size": {"width": {"magnitude": 200.0, "unit": "PT"}, "height": {"magnitude": 100.0, "unit": "PT"}},
            "marginTop": {"magnitude": 18.0, "unit": "PT"},
            "marginBottom": {"magnitude": 9.0, "unit": "PT"},
            "marginLeft": {"magnitude": 9.0, "unit": "PT"},
            "marginRight": {"magnitude": 9.0, "unit": "PT"},
        }
        inline_objects = {
            "kix.img1": {
                "objectId": "kix.img1",
                "inlineObjectProperties": {"embeddedObject": embedded_obj},
            }
        }
        doc = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[
                                ParagraphElement(
                                    inlineObjectElement=InlineObjectElement(inlineObjectId="kix.img1"),
                                ),
                                ParagraphElement(textRun=TextRun(content="\n")),
                            ],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    )
                ]
            ),
            inlineObjects=inline_objects,
        )
        result = serializer.serialize(doc)
        assert "![](https://example.com/img.png)" in result
        assert "<!-- image-props:" in result
        assert '"width": 200.0' in result
        assert '"height": 100.0' in result
        assert '"offsetRight": 0.705' in result
        assert '"marginTop": 18.0' in result

    def test_image_default_properties_no_tag(self, serializer: MarkdownSerializer) -> None:
        """Image with only default margins and no cropping should NOT emit the tag."""
        from google_docs_markdown.models.elements import InlineObjectElement

        embedded_obj: dict[str, Any] = {
            "imageProperties": {"contentUri": "https://example.com/img.png"},
            "marginTop": {"magnitude": 9.0, "unit": "PT"},
            "marginBottom": {"magnitude": 9.0, "unit": "PT"},
            "marginLeft": {"magnitude": 9.0, "unit": "PT"},
            "marginRight": {"magnitude": 9.0, "unit": "PT"},
        }
        inline_objects = {
            "kix.img1": {
                "objectId": "kix.img1",
                "inlineObjectProperties": {"embeddedObject": embedded_obj},
            }
        }
        doc = DocumentTab(
            body=Body(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[
                                ParagraphElement(
                                    inlineObjectElement=InlineObjectElement(inlineObjectId="kix.img1"),
                                ),
                                ParagraphElement(textRun=TextRun(content="\n")),
                            ],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    )
                ]
            ),
            inlineObjects=inline_objects,
        )
        result = serializer.serialize(doc)
        assert "![](https://example.com/img.png)" in result
        assert "<!-- image-props:" not in result

    def test_fixture_single_tab_image(self, serializer: MarkdownSerializer) -> None:
        """Verify real fixture produces an image reference."""
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        assert "![" in result
        assert "](https://lh7-rt.googleusercontent.com/" in result


# ---------------------------------------------------------------------------
# Code block tests
# ---------------------------------------------------------------------------


def _mono_run(content: str) -> ParagraphElement:
    """Build a ParagraphElement with a Roboto Mono text run."""
    from google_docs_markdown.models.common import WeightedFontFamily

    return ParagraphElement(
        textRun=TextRun(
            content=content,
            textStyle=TextStyle(
                weightedFontFamily=WeightedFontFamily(fontFamily="Roboto Mono", weight=400),
            ),
        )
    )


def _plain_run(content: str) -> ParagraphElement:
    """Build a ParagraphElement with a plain (Arial) text run."""
    from google_docs_markdown.models.common import WeightedFontFamily

    return ParagraphElement(
        textRun=TextRun(
            content=content,
            textStyle=TextStyle(
                weightedFontFamily=WeightedFontFamily(fontFamily="Arial", weight=400),
            ),
        )
    )


def _make_code_block_doc(
    code_lines: list[str],
    *,
    before_text: str | None = None,
    after_text: str | None = None,
) -> DocumentTab:
    """Build a DocumentTab with a code block surrounded by optional text."""
    elements: list[StructuralElement] = []

    if before_text:
        elements.append(
            StructuralElement(
                paragraph=Paragraph(
                    elements=[ParagraphElement(textRun=TextRun(content=before_text + "\n"))],
                    paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                )
            )
        )

    start_para = Paragraph(
        elements=[_plain_run("\ue907"), _mono_run(code_lines[0] + "\n")],
        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
    )
    elements.append(StructuralElement(paragraph=start_para))

    for line in code_lines[1:-1] if len(code_lines) > 2 else []:
        mid_para = Paragraph(
            elements=[_mono_run(line + "\n")],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        elements.append(StructuralElement(paragraph=mid_para))

    if len(code_lines) > 1:
        end_para = Paragraph(
            elements=[_mono_run(code_lines[-1]), _plain_run("\ue907\n")],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        elements.append(StructuralElement(paragraph=end_para))

    if after_text:
        elements.append(
            StructuralElement(
                paragraph=Paragraph(
                    elements=[ParagraphElement(textRun=TextRun(content=after_text + "\n"))],
                    paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                )
            )
        )

    return DocumentTab(body=Body(content=elements))


class TestSerializerCodeBlocks:
    def test_simple_code_block(self, serializer: MarkdownSerializer) -> None:
        doc = _make_code_block_doc(["def foo():", "    pass"])
        result = serializer.serialize(doc)
        assert "```\ndef foo():\n    pass\n```" in result

    def test_code_block_strips_ue907(self, serializer: MarkdownSerializer) -> None:
        doc = _make_code_block_doc(["x = 1", "print(x)"])
        result = serializer.serialize(doc)
        assert "\ue907" not in result

    def test_code_block_between_paragraphs(self, serializer: MarkdownSerializer) -> None:
        doc = _make_code_block_doc(
            ["hello()", "world()"],
            before_text="Before",
            after_text="After",
        )
        result = serializer.serialize(doc)
        assert "Before" in result
        assert "After" in result
        assert "```\nhello()\nworld()\n```" in result

    def test_code_block_multiline(self, serializer: MarkdownSerializer) -> None:
        doc = _make_code_block_doc(["line1", "line2", "line3"])
        result = serializer.serialize(doc)
        assert "```\nline1\nline2\nline3\n```" in result

    def test_code_block_single_line(self, serializer: MarkdownSerializer) -> None:
        """A single-line code block with start+end markers on same paragraph."""
        para = Paragraph(
            elements=[
                _plain_run("\ue907"),
                _mono_run("single_line()"),
                _plain_run("\ue907\n"),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc)
        assert "```\nsingle_line()\n```" in result
        assert "\ue907" not in result

    def test_fixture_single_tab_code_block(self, serializer: MarkdownSerializer) -> None:
        """Verify that the real single-tab fixture produces a fenced code block."""
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        assert "```\n" in result
        assert "def calculate_markdown_conversion(doc_content):" in result
        assert "\ue907" not in result


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

        assert "<!-- title -->" in result
        assert "Markdown Conversion Example - Single Tab" in result
        assert "<!-- subtitle -->" in result
        assert "Document Subtitle" in result
        assert "# " in result and "Project Overview: Markdown Tool Testing (Heading 1)" in result
        assert "## " in result and "Section 1: Headings and Structure (Heading 2)" in result
        assert "### " in result and "Subsection 1.1: Lower Level Headings (Heading 3)" in result
        assert "#### " in result and "Sub-Subsection 1.1.1: Deeper Dive (Heading 4)" in result
        assert "##### " in result and "Sub-Sub-Subsection 1.1.1.1: Specific Detail (Heading 5)" in result
        assert "###### " in result and "Sub-Sub-Sub-Subsection 1.1.1.1.1: Very detailed Level (Heading 6)" in result

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

    def test_single_tab_fixture_lists(self, serializer: MarkdownSerializer) -> None:
        """Verify lists in the single-tab fixture are rendered with bullet markers."""
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]
        assert "\n- " in result

    def test_multi_tab_first_tab_structure(self, serializer: MarkdownSerializer) -> None:
        """The first tab of multi-tab has the same structure as single-tab (different title)."""
        multi = _load_document(MULTI_TAB_JSON)
        result = serializer.serialize(multi.tabs[0].documentTab)  # type: ignore

        assert "<!-- title -->" in result
        assert "Markdown Conversion Example - Multi-Tab" in result
        assert "**should be bold**" in result
        assert "*should be italic*" in result
        assert "## " in result and "Section 1: Headings and Structure (Heading 2)" in result

    def test_multi_tab_fixture_link(self, serializer: MarkdownSerializer) -> None:
        """Verify the fixture's hyperlink to the Child Tab renders as a Markdown link."""
        doc = _load_document(MULTI_TAB_JSON)
        result = serializer.serialize(doc.tabs[0].documentTab)  # type: ignore
        assert "[This is a link to the \u201cChild Tab\u201d](https://docs.google.com/document/d/" in result

    def test_single_tab_fixture_table(self, serializer: MarkdownSerializer) -> None:
        """Verify the single-tab fixture table renders as a Markdown pipe table."""
        doc = _load_document(SINGLE_TAB_JSON)
        tab = doc.tabs[0]  # type: ignore[index]
        result = serializer.serialize(tab.documentTab)  # type: ignore[arg-type]

        assert "**Header 1**" in result
        assert "**Header 2**" in result
        assert "**Header 3**" in result
        assert "| --- | --- | --- |" in result
        assert "Data A1" in result
        assert "Data B1" in result
        assert "Data C1" in result
        assert "Data A2" in result
        assert "Data B2" in result
        assert "Data C3" in result

    def test_multi_tab_fixture_table(self, serializer: MarkdownSerializer) -> None:
        """Verify the multi-tab fixture table renders as a Markdown pipe table."""
        doc = _load_document(MULTI_TAB_JSON)
        result = serializer.serialize(doc.tabs[0].documentTab)  # type: ignore

        assert "**Header 1**" in result
        assert "| --- | --- | --- |" in result
        assert "Data A1" in result
        assert "Data B1" in result

    def test_multi_tab_fixture_rich_link(self, serializer: MarkdownSerializer) -> None:
        """Verify the fixture's rich link chip renders as [title](uri)."""
        doc = _load_document(MULTI_TAB_JSON)
        result = serializer.serialize(doc.tabs[0].documentTab)  # type: ignore
        assert "[Markdown Conversion Example - Single-Tab](https://docs.google.com/document/d/" in result

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


class TestSerializerReuse:
    """Verify that reusing a MarkdownSerializer instance across documents produces clean state."""

    def test_no_state_cross_contamination(self) -> None:
        """Serializing two different documents with the same instance must not leak state."""
        serializer = MarkdownSerializer()

        doc1 = _make_doc_tab([("Doc one title", "TITLE"), ("Body one", "NORMAL_TEXT")])
        doc1.footnotes = {
            "fn1": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Footnote from doc 1\n"}}],
                        },
                    }
                ],
                "footnoteId": "fn1",
            },
        }
        doc1.body.content[1].paragraph.elements.append(  # type: ignore[union-attr,index]
            ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn1", footnoteNumber="1")),
        )

        result1 = serializer.serialize(doc1)
        assert "[^1]" in result1
        assert "Footnote from doc 1" in result1

        doc2 = _make_doc_tab([("Doc two title", "TITLE"), ("Body two", "NORMAL_TEXT")])
        result2 = serializer.serialize(doc2)

        assert "Doc two title" in result2
        assert "Footnote from doc 1" not in result2
        assert "[^1]" not in result2

    def test_default_styles_reset(self) -> None:
        """Default font/size/color from doc 1 must not bleed into doc 2."""
        from google_docs_markdown.models.common import Dimension, WeightedFontFamily
        from google_docs_markdown.models.document import NamedStyle, NamedStyles

        serializer = MarkdownSerializer()

        doc1 = _make_doc_tab([("Hello", "NORMAL_TEXT")])
        doc1.namedStyles = NamedStyles(
            styles=[
                NamedStyle(
                    namedStyleType="NORMAL_TEXT",
                    textStyle=TextStyle(
                        weightedFontFamily=WeightedFontFamily(fontFamily="Courier New"),
                        fontSize=Dimension(magnitude=14, unit="PT"),
                    ),
                ),
            ]
        )
        result1 = serializer.serialize(doc1)
        assert "Courier New" in result1

        doc2 = _make_doc_tab([("World", "NORMAL_TEXT")])
        result2 = serializer.serialize(doc2)
        assert "Courier New" not in result2


# ---------------------------------------------------------------------------
# Paragraph alignment serialization tests (Feature 2)
# ---------------------------------------------------------------------------


class TestSerializerAlignment:
    def test_center_alignment(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content="Centered text\n"))],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT", alignment="CENTER"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert '<!-- align: {"value": "center"} -->' in result
        assert "Centered text" in result

    def test_end_alignment(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content="Right aligned\n"))],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT", alignment="END"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert '<!-- align: {"value": "right"} -->' in result

    def test_justified_alignment(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content="Justified text\n"))],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT", alignment="JUSTIFIED"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert '<!-- align: {"value": "justify"} -->' in result

    def test_start_alignment_no_tag(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content="Normal text\n"))],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT", alignment="START"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert "<!-- align:" not in result

    def test_no_alignment_no_tag(self, serializer: MarkdownSerializer) -> None:
        doc_tab = _make_doc_tab([("Plain text", "NORMAL_TEXT")])
        result = serializer.serialize(doc_tab)
        assert "<!-- align:" not in result


# ---------------------------------------------------------------------------
# Superscript/subscript serialization tests (Feature 3)
# ---------------------------------------------------------------------------


class TestSerializerSuperSubscript:
    def test_superscript(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="E=mc")),
                ParagraphElement(textRun=TextRun(content="2", textStyle=TextStyle(baselineOffset="SUPERSCRIPT"))),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert "<sup>2</sup>" in result
        assert "E=mc" in result

    def test_subscript(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="H")),
                ParagraphElement(textRun=TextRun(content="2", textStyle=TextStyle(baselineOffset="SUBSCRIPT"))),
                ParagraphElement(textRun=TextRun(content="O\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert "<sub>2</sub>" in result
        assert "H" in result
        assert "O" in result

    def test_no_baseline_offset_no_tag(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="Normal\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert "<sup>" not in result
        assert "<sub>" not in result

    def test_superscript_with_bold(self, serializer: MarkdownSerializer) -> None:
        para = Paragraph(
            elements=[
                ParagraphElement(textRun=TextRun(content="x")),
                ParagraphElement(
                    textRun=TextRun(
                        content="n",
                        textStyle=TextStyle(bold=True, baselineOffset="SUPERSCRIPT"),
                    )
                ),
                ParagraphElement(textRun=TextRun(content="\n")),
            ],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
        doc_tab = DocumentTab(body=Body(content=[StructuralElement(paragraph=para)]))
        result = serializer.serialize(doc_tab)
        assert "<sup>**n**</sup>" in result
