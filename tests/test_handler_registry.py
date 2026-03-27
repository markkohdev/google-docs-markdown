"""Tests for HandlerRegistry dispatch in both serialization directions."""

from __future__ import annotations

from typing import Any

import pytest

from google_docs_markdown.block_grouper import CodeBlock, ListBlock
from google_docs_markdown.handlers.base import (
    ElementHandler,
)
from google_docs_markdown.handlers.breaks import (
    AutoTextHandler,
    ColumnBreakHandler,
    EquationHandler,
    HorizontalRuleHandler,
    PageBreakHandler,
    SectionBreakHandler,
)
from google_docs_markdown.handlers.code_block import CodeBlockHandler
from google_docs_markdown.handlers.date import DateHandler
from google_docs_markdown.handlers.footnote import FootnoteRefHandler
from google_docs_markdown.handlers.image import ImageHandler
from google_docs_markdown.handlers.list_handler import ListHandler
from google_docs_markdown.handlers.person import PersonHandler
from google_docs_markdown.handlers.registry import HandlerRegistry
from google_docs_markdown.handlers.rich_link import RichLinkHandler
from google_docs_markdown.handlers.table import TableHandler
from google_docs_markdown.handlers.text_run import TextRunHandler
from google_docs_markdown.handlers.toc import TableOfContentsHandler
from google_docs_markdown.models.common import PersonProperties, RichLinkProperties
from google_docs_markdown.models.elements import (
    AutoText,
    ColumnBreak,
    DateElement,
    DateElementProperties,
    Equation,
    FootnoteReference,
    HorizontalRule,
    InlineObjectElement,
    PageBreak,
    Paragraph,
    ParagraphElement,
    Person,
    RichLink,
    SectionBreak,
    StructuralElement,
    Table,
    TableOfContents,
    TextRun,
)


@pytest.fixture
def registry() -> HandlerRegistry:
    return HandlerRegistry.default()


# ---------------------------------------------------------------------------
# Paragraph element dispatch
# ---------------------------------------------------------------------------


class TestParagraphElementDispatch:
    def test_person_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(person=Person(personProperties=PersonProperties(email="a@b.com")))
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, PersonHandler)

    def test_date_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(
            dateElement=DateElement(dateElementProperties=DateElementProperties(displayText="today"))
        )
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, DateHandler)

    def test_rich_link_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(richLink=RichLink(richLinkProperties=RichLinkProperties(uri="https://example.com")))
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, RichLinkHandler)

    def test_footnote_ref_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(footnoteReference=FootnoteReference(footnoteId="fn1", footnoteNumber="1"))
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, FootnoteRefHandler)

    def test_image_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(inlineObjectElement=InlineObjectElement(inlineObjectId="img1"))
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, ImageHandler)

    def test_horizontal_rule_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(horizontalRule=HorizontalRule())
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, HorizontalRuleHandler)

    def test_page_break_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(pageBreak=PageBreak())
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, PageBreakHandler)

    def test_column_break_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(columnBreak=ColumnBreak())
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, ColumnBreakHandler)

    def test_auto_text_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(autoText=AutoText(type="PAGE_NUMBER"))
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, AutoTextHandler)

    def test_equation_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(equation=Equation())
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, EquationHandler)

    def test_text_run_handler(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement(textRun=TextRun(content="hello"))
        handler = registry.match_paragraph_element(elem)
        assert isinstance(handler, TextRunHandler)

    def test_empty_element_no_match(self, registry: HandlerRegistry) -> None:
        elem = ParagraphElement()
        handler = registry.match_paragraph_element(elem)
        assert handler is None


# ---------------------------------------------------------------------------
# Structural element dispatch
# ---------------------------------------------------------------------------


class TestStructuralElementDispatch:
    def test_table_handler(self, registry: HandlerRegistry) -> None:
        elem = StructuralElement(table=Table(rows=1, columns=1))
        handler = registry.match_structural(elem)
        assert isinstance(handler, TableHandler)

    def test_section_break_handler(self, registry: HandlerRegistry) -> None:
        elem = StructuralElement(sectionBreak=SectionBreak())
        handler = registry.match_structural(elem)
        assert isinstance(handler, SectionBreakHandler)

    def test_toc_handler(self, registry: HandlerRegistry) -> None:
        elem = StructuralElement(tableOfContents=TableOfContents())
        handler = registry.match_structural(elem)
        assert isinstance(handler, TableOfContentsHandler)

    def test_paragraph_no_structural_match(self, registry: HandlerRegistry) -> None:
        elem = StructuralElement(paragraph=Paragraph(elements=[ParagraphElement(textRun=TextRun(content="hi"))]))
        handler = registry.match_structural(elem)
        assert handler is None


# ---------------------------------------------------------------------------
# Block dispatch
# ---------------------------------------------------------------------------


class TestBlockDispatch:
    def test_list_block_handler(self, registry: HandlerRegistry) -> None:
        block = ListBlock()
        handler = registry.match_block(block)
        assert isinstance(handler, ListHandler)

    def test_code_block_handler(self, registry: HandlerRegistry) -> None:
        block = CodeBlock()
        handler = registry.match_block(block)
        assert isinstance(handler, CodeBlockHandler)

    def test_structural_element_not_a_block(self, registry: HandlerRegistry) -> None:
        elem = StructuralElement(paragraph=Paragraph())
        handler = registry.match_block(elem)
        assert handler is None


# ---------------------------------------------------------------------------
# get_handler
# ---------------------------------------------------------------------------


class TestGetHandler:
    def test_get_person_handler(self, registry: HandlerRegistry) -> None:
        handler = registry.get_handler(PersonHandler)
        assert isinstance(handler, PersonHandler)

    def test_get_missing_handler(self, registry: HandlerRegistry) -> None:
        class FakeHandler(ElementHandler):
            def serialize_match(self, element: Any) -> bool:
                return False

            def serialize(self, element: Any, ctx: Any) -> str | None:
                return None

            def deserialize_match(self, token: Any) -> bool:
                return False

            def deserialize(self, token: Any, ctx: Any) -> list[Any]:
                return []

        assert registry.get_handler(FakeHandler) is None


# ---------------------------------------------------------------------------
# Custom registry
# ---------------------------------------------------------------------------


class TestCustomRegistry:
    def test_empty_registry(self) -> None:
        registry = HandlerRegistry()
        elem = ParagraphElement(textRun=TextRun(content="hello"))
        assert registry.match_paragraph_element(elem) is None

    def test_custom_handlers(self) -> None:
        registry = HandlerRegistry(
            paragraph_element_handlers=[PersonHandler()],
        )
        person_elem = ParagraphElement(person=Person(personProperties=PersonProperties(email="a@b.com")))
        assert isinstance(registry.match_paragraph_element(person_elem), PersonHandler)

        text_elem = ParagraphElement(textRun=TextRun(content="hi"))
        assert registry.match_paragraph_element(text_elem) is None
