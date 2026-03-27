"""Tests for non-Markdown element serialization: annotations, chips, and metadata.

Tests person mentions, date elements, style comments, structural markers,
suggestions, rich link metadata, opaque elements, chip placeholders, and
the embedded metadata block.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import pytest

from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.models.common import (
    Color,
    Footer,
    Header,
    OptionalColor,
    PersonProperties,
    RgbColor,
    RichLinkProperties,
    WeightedFontFamily,
)
from google_docs_markdown.models.document import Body, DocumentTab, NamedStyle, NamedStyles
from google_docs_markdown.models.elements import (
    AutoText,
    ColumnBreak,
    DateElement,
    DateElementProperties,
    Equation,
    PageBreak,
    Paragraph,
    ParagraphElement,
    Person,
    RichLink,
    SectionBreak,
    StructuralElement,
    TableOfContents,
    TextRun,
)
from google_docs_markdown.models.styles import (
    ParagraphStyle,
    SectionStyle,
    TextStyle,
)

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

RESOURCES_DIR = Path(__file__).parent / "resources" / "document_jsons"
MULTI_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Multi-Tab.json"


@pytest.fixture
def serializer() -> MarkdownSerializer:
    return MarkdownSerializer()


def _make_doc_tab(
    elements: list[StructuralElement],
    named_styles: NamedStyles | None = None,
    headers: dict[str, Any] | None = None,
    footers: dict[str, Any] | None = None,
) -> DocumentTab:
    return DocumentTab(
        body=Body(content=elements),
        namedStyles=named_styles,
        headers=headers,
        footers=footers,
    )


def _para(
    text: str,
    style_type: _NamedStyleType = "NORMAL_TEXT",
    text_style: TextStyle | None = None,
    start_index: int | None = None,
) -> StructuralElement:
    return StructuralElement(
        startIndex=start_index,
        paragraph=Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content=text + "\n", textStyle=text_style))],
            paragraphStyle=ParagraphStyle(namedStyleType=style_type),
        ),
    )


# --- Person ---


class TestPerson:
    def test_basic_person(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        person=Person(personProperties=PersonProperties(name="Alice", email="alice@example.com"))
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert '<!-- person: {"email": "alice@example.com"} -->Alice<!-- /person -->' in result

    def test_person_no_name(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[ParagraphElement(person=Person(personProperties=PersonProperties(email="bob@test.com")))],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "bob@test.com" in result
        assert "<!-- person:" in result

    def test_person_inline_with_text(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(textRun=TextRun(content="Contact: ")),
                    ParagraphElement(person=Person(personProperties=PersonProperties(name="Charlie", email="c@x.com"))),
                    ParagraphElement(textRun=TextRun(content=" for details\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "Contact:" in result
        assert "Charlie<!-- /person -->" in result
        assert "for details" in result


# --- DateElement ---


class TestDateElement:
    def test_basic_date(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        dateElement=DateElement(
                            dateElementProperties=DateElementProperties(
                                displayText="2026-01-08",
                                dateFormat="DATE_FORMAT_ISO8601",
                                locale="en",
                                timestamp="2026-01-08T12:00:00Z",
                            )
                        )
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- date -->2026-01-08<!-- /date -->" in result
        assert "DATE_FORMAT_ISO8601" in result

    def test_date_with_timezone(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        dateElement=DateElement(
                            dateElementProperties=DateElementProperties(
                                displayText="Jan 8",
                                dateFormat="DATE_FORMAT_MONTH_DAY_ABBREVIATED",
                                locale="en",
                                timeZoneId="America/New_York",
                            )
                        )
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "America/New_York" in result


# --- Style Comments ---


class TestStyleComments:
    def _make_styled_doc(
        self,
        text: str,
        text_style: TextStyle,
        default_font: str = "Proxima Nova",
        default_size: float = 11.0,
    ) -> DocumentTab:
        from google_docs_markdown.models.common import Dimension

        named_styles = NamedStyles(
            styles=[
                NamedStyle(
                    namedStyleType="NORMAL_TEXT",
                    textStyle=TextStyle(
                        weightedFontFamily=WeightedFontFamily(fontFamily=default_font, weight=400),
                        fontSize=Dimension(magnitude=default_size, unit="PT"),
                    ),
                )
            ]
        )
        return _make_doc_tab(
            [_para(text, text_style=text_style)],
            named_styles=named_styles,
        )

    def test_colored_text(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(foregroundColor=OptionalColor(color=Color(rgbColor=RgbColor(red=1.0, green=0.0, blue=0.0))))
        doc = self._make_styled_doc("red text", style)
        result = serializer.serialize(doc)
        assert '<!-- style: {"color": "#FF0000"} -->' in result
        assert "red text" in result
        assert "<!-- /style -->" in result

    def test_background_color(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(backgroundColor=OptionalColor(color=Color(rgbColor=RgbColor(red=0.0, green=0.0, blue=1.0))))
        doc = self._make_styled_doc("highlighted", style)
        result = serializer.serialize(doc)
        assert "background-color" in result
        assert "#0000FF" in result

    def test_default_font_no_style_comment(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(weightedFontFamily=WeightedFontFamily(fontFamily="Proxima Nova", weight=400))
        doc = self._make_styled_doc("normal text", style)
        result = serializer.serialize(doc)
        assert "<!-- style:" not in result

    def test_common_gdocs_font_no_style_comment(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(weightedFontFamily=WeightedFontFamily(fontFamily="Arial", weight=400))
        doc = self._make_styled_doc("arial text", style)
        result = serializer.serialize(doc)
        assert "font-family" not in result

    def test_custom_font_gets_style_comment(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(weightedFontFamily=WeightedFontFamily(fontFamily="Comic Sans MS", weight=400))
        doc = self._make_styled_doc("custom font", style)
        result = serializer.serialize(doc)
        assert "Comic Sans MS" in result
        assert "<!-- style:" in result

    def test_non_default_size(self, serializer: MarkdownSerializer) -> None:
        from google_docs_markdown.models.common import Dimension

        style = TextStyle(fontSize=Dimension(magnitude=18.0, unit="PT"))
        doc = self._make_styled_doc("big text", style)
        result = serializer.serialize(doc)
        assert "font-size" in result
        assert "18.0" in result

    def test_style_wraps_markdown_formatting(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(
            bold=True,
            foregroundColor=OptionalColor(color=Color(rgbColor=RgbColor(red=1.0, green=0.0, blue=0.0))),
        )
        doc = self._make_styled_doc("bold red", style)
        result = serializer.serialize(doc)
        assert "<!-- style:" in result
        assert "**bold red**" in result
        assert "<!-- /style -->" in result

    def test_small_caps(self, serializer: MarkdownSerializer) -> None:
        style = TextStyle(smallCaps=True)
        doc = self._make_styled_doc("caps", style)
        result = serializer.serialize(doc)
        assert "small-caps" in result


# --- Structural Elements ---


class TestStructuralAnnotations:
    def test_section_break_skipped_at_start(self, serializer: MarkdownSerializer) -> None:
        elems = [
            StructuralElement(
                startIndex=0,
                endIndex=1,
                sectionBreak=SectionBreak(sectionStyle=SectionStyle(sectionType="CONTINUOUS")),
            ),
            _para("Hello", start_index=1),
        ]
        doc = _make_doc_tab(elems)
        result = serializer.serialize(doc)
        assert "section-break" not in result
        assert "Hello" in result

    def test_section_break_skipped_no_indices(self, serializer: MarkdownSerializer) -> None:
        elems = [
            StructuralElement(
                sectionBreak=SectionBreak(sectionStyle=SectionStyle(sectionType="CONTINUOUS")),
            ),
            _para("Content"),
        ]
        doc = _make_doc_tab(elems)
        result = serializer.serialize(doc)
        assert "section-break" not in result

    def test_mid_doc_section_break(self, serializer: MarkdownSerializer) -> None:
        elems = [
            _para("Before", start_index=1),
            StructuralElement(
                startIndex=10,
                endIndex=11,
                sectionBreak=SectionBreak(sectionStyle=SectionStyle(sectionType="NEXT_PAGE")),
            ),
            _para("After", start_index=11),
        ]
        doc = _make_doc_tab(elems)
        result = serializer.serialize(doc)
        assert '<!-- section-break: {"type": "NEXT_PAGE"} -->' in result

    def test_page_break(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(pageBreak=PageBreak()),
                    ParagraphElement(textRun=TextRun(content="\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- page-break -->" in result

    def test_column_break(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(columnBreak=ColumnBreak()),
                    ParagraphElement(textRun=TextRun(content="\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- column-break -->" in result

    def test_table_of_contents(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            tableOfContents=TableOfContents(
                content=[
                    StructuralElement(
                        paragraph=Paragraph(
                            elements=[ParagraphElement(textRun=TextRun(content="Heading 1\n"))],
                            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                        )
                    )
                ]
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- table-of-contents -->" in result
        assert "Heading 1" not in result

    def test_title_marker(self, serializer: MarkdownSerializer) -> None:
        doc = _make_doc_tab([_para("My Title", "TITLE")])
        result = serializer.serialize(doc)
        assert "<!-- title -->" in result
        assert "# My Title" in result

    def test_subtitle_marker(self, serializer: MarkdownSerializer) -> None:
        doc = _make_doc_tab([_para("My Sub", "SUBTITLE")])
        result = serializer.serialize(doc)
        assert "<!-- subtitle -->" in result
        assert "*My Sub*" in result


# --- Suggestions ---


class TestSuggestions:
    def test_suggested_insertion(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        textRun=TextRun(
                            content="inserted text\n",
                            suggestedInsertionIds=["suggest.abc123"],
                        )
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- suggestion:" in result
        assert '"type": "insertion"' in result
        assert "inserted text" in result
        assert "<!-- /suggestion -->" in result

    def test_suggested_deletion(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        textRun=TextRun(
                            content="deleted text\n",
                            suggestedDeletionIds=["suggest.del456"],
                        )
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- suggestion:" in result
        assert '"type": "deletion"' in result
        assert "deleted text" in result


# --- Rich Link Metadata ---


class TestRichLinkMetadata:
    def test_rich_link_with_mime_type(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        richLink=RichLink(
                            richLinkProperties=RichLinkProperties(
                                title="My Sheet",
                                uri="https://docs.google.com/spreadsheets/d/abc",
                                mimeType="application/vnd.google-apps.spreadsheet",
                            )
                        )
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- rich-link:" in result
        assert "spreadsheet" in result
        assert "[My Sheet](https://docs.google.com/spreadsheets/d/abc)" in result
        assert "<!-- /rich-link -->" in result

    def test_rich_link_no_mime_type(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(
                        richLink=RichLink(
                            richLinkProperties=RichLinkProperties(
                                title="Link",
                                uri="https://example.com",
                            )
                        )
                    )
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- rich-link:" not in result
        assert "[Link](https://example.com)" in result


# --- Opaque Elements ---


class TestOpaqueElements:
    def test_auto_text(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(autoText=AutoText(type="PAGE_NUMBER")),
                    ParagraphElement(textRun=TextRun(content="\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert '<!-- auto-text: {"type": "PAGE_NUMBER"} -->' in result

    def test_equation(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(equation=Equation()),
                    ParagraphElement(textRun=TextRun(content="\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- equation -->" in result

    def test_chip_placeholder(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(textRun=TextRun(content="Status: \ue907\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert "<!-- chip-placeholder -->" in result
        assert "Status:" in result
        assert "\ue907" not in result

    def test_multiple_chip_placeholders(self, serializer: MarkdownSerializer) -> None:
        elem = StructuralElement(
            paragraph=Paragraph(
                elements=[
                    ParagraphElement(textRun=TextRun(content="A\ue907B\ue907C\n")),
                ],
                paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            )
        )
        doc = _make_doc_tab([elem])
        result = serializer.serialize(doc)
        assert result.count("<!-- chip-placeholder -->") == 2


# --- Headers/Footers ---


class TestHeadersFooters:
    def test_header(self, serializer: MarkdownSerializer) -> None:
        header = Header(
            headerId="h1",
            content=[
                StructuralElement(
                    paragraph=Paragraph(
                        elements=[ParagraphElement(textRun=TextRun(content="Company Name\n"))],
                        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                    )
                )
            ],
        )
        doc = _make_doc_tab(
            [_para("Body text")],
            headers={"h1": header.model_dump()},
        )
        result = serializer.serialize(doc)
        assert '<!-- header: {"id": "h1"} -->' in result
        assert "Company Name" in result
        assert "<!-- /header -->" in result

    def test_footer(self, serializer: MarkdownSerializer) -> None:
        footer = Footer(
            footerId="f1",
            content=[
                StructuralElement(
                    paragraph=Paragraph(
                        elements=[ParagraphElement(textRun=TextRun(content="Page 1\n"))],
                        paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                    )
                )
            ],
        )
        doc = _make_doc_tab(
            [_para("Body text")],
            footers={"f1": footer.model_dump()},
        )
        result = serializer.serialize(doc)
        assert '<!-- footer: {"id": "f1"} -->' in result
        assert "Page 1" in result
        assert "<!-- /footer -->" in result


# --- Fixture-Based Tests ---


class TestFixtureAnnotations:
    """Tests using the real Multi-Tab fixture to verify annotation elements."""

    @pytest.fixture
    def first_tab_result(self, serializer: MarkdownSerializer) -> str:
        with open(MULTI_TAB_JSON) as f:
            data = json.load(f)
        from google_docs_markdown.models import Document

        doc = Document.model_validate(data)
        return serializer.serialize(doc.tabs[0].documentTab)  # type: ignore

    def test_person_chips(self, first_tab_result: str) -> None:
        assert "<!-- person:" in first_tab_result
        assert "markkoh@spotify.com" in first_tab_result
        assert "Mark Koh<!-- /person -->" in first_tab_result

    def test_date_elements(self, first_tab_result: str) -> None:
        assert "<!-- date -->2026-01-08<!-- /date -->" in first_tab_result
        assert "dateDefaults" in first_tab_result

    def test_chip_placeholders(self, first_tab_result: str) -> None:
        assert "<!-- chip-placeholder -->" in first_tab_result

    def test_title_marker(self, first_tab_result: str) -> None:
        assert "<!-- title -->" in first_tab_result

    def test_subtitle_marker(self, first_tab_result: str) -> None:
        assert "<!-- subtitle -->" in first_tab_result

    def test_table_of_contents(self, first_tab_result: str) -> None:
        assert "<!-- table-of-contents -->" in first_tab_result

    def test_rich_link(self, first_tab_result: str) -> None:
        assert "<!-- rich-link:" in first_tab_result
        assert "Markdown Conversion Example - Single-Tab" in first_tab_result

    def test_suggestions(self, first_tab_result: str) -> None:
        assert "<!-- suggestion:" in first_tab_result
        assert "This is an inline suggestion" in first_tab_result

    def test_no_leading_section_break(self, first_tab_result: str) -> None:
        assert not first_tab_result.startswith("<!-- section-break")

    def test_no_ue907_in_output(self, first_tab_result: str) -> None:
        assert "\ue907" not in first_tab_result
