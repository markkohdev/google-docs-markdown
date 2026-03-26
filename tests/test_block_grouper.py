"""Tests for the block grouper pre-processing pass."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.block_grouper import (
    CodeBlock,
    ListBlock,
    group_elements,
)
from google_docs_markdown.models.elements import (
    Paragraph,
    ParagraphElement,
    SectionBreak,
    StructuralElement,
    Table,
    TextRun,
)
from google_docs_markdown.models.styles import Bullet, ParagraphStyle, TextStyle
from google_docs_markdown.models.common import WeightedFontFamily


def _para(text: str, list_id: str | None = None, nesting: int = 0) -> StructuralElement:
    """Build a minimal StructuralElement wrapping a Paragraph."""
    bullet = Bullet(listId=list_id, nestingLevel=nesting) if list_id else None
    return StructuralElement(
        paragraph=Paragraph(
            elements=[ParagraphElement(textRun=TextRun(content=text + "\n"))],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
            bullet=bullet,
        )
    )


def _lists_context(
    entries: dict[str, str],
) -> dict[str, Any]:
    """Build a lists context dict.

    ``entries`` maps listId -> glyphType (applied at all nesting levels).
    """
    ctx: dict[str, Any] = {}
    for list_id, glyph_type in entries.items():
        ctx[list_id] = {
            "listProperties": {"nestingLevels": [{"glyphType": glyph_type, "startNumber": 1} for _ in range(9)]}
        }
    return ctx


class TestGroupElements:
    def test_no_lists_passthrough(self) -> None:
        elements = [_para("Hello"), _para("World")]
        blocks = group_elements(elements)
        assert len(blocks) == 2
        assert all(isinstance(b, StructuralElement) for b in blocks)

    def test_single_list(self) -> None:
        elements = [
            _para("Item 1", list_id="kix.abc"),
            _para("Item 2", list_id="kix.abc"),
        ]
        ctx = _lists_context({"kix.abc": "GLYPH_TYPE_UNSPECIFIED"})
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 1
        lb = blocks[0]
        assert isinstance(lb, ListBlock)
        assert len(lb.items) == 2
        assert not lb.items[0].is_ordered
        assert not lb.items[1].is_ordered

    def test_ordered_list(self) -> None:
        elements = [
            _para("First", list_id="kix.num"),
            _para("Second", list_id="kix.num"),
        ]
        ctx = _lists_context({"kix.num": "DECIMAL"})
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 1
        lb = blocks[0]
        assert isinstance(lb, ListBlock)
        assert lb.items[0].is_ordered
        assert lb.items[1].is_ordered

    def test_different_list_ids_separate_blocks(self) -> None:
        elements = [
            _para("Bullet", list_id="kix.a"),
            _para("Number", list_id="kix.b"),
        ]
        ctx = _lists_context({"kix.a": "GLYPH_TYPE_UNSPECIFIED", "kix.b": "DECIMAL"})
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 2
        assert isinstance(blocks[0], ListBlock)
        assert isinstance(blocks[1], ListBlock)
        assert not blocks[0].items[0].is_ordered
        assert blocks[1].items[0].is_ordered

    def test_list_interrupted_by_paragraph(self) -> None:
        elements = [
            _para("Item 1", list_id="kix.a"),
            _para("Normal text"),
            _para("Item 2", list_id="kix.a"),
        ]
        ctx = _lists_context({"kix.a": "GLYPH_TYPE_UNSPECIFIED"})
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 3
        assert isinstance(blocks[0], ListBlock)
        assert isinstance(blocks[1], StructuralElement)
        assert isinstance(blocks[2], ListBlock)

    def test_nested_list(self) -> None:
        elements = [
            _para("Top", list_id="kix.a", nesting=0),
            _para("Sub", list_id="kix.a", nesting=1),
            _para("SubSub", list_id="kix.a", nesting=2),
        ]
        ctx = _lists_context({"kix.a": "GLYPH_TYPE_UNSPECIFIED"})
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 1
        lb = blocks[0]
        assert isinstance(lb, ListBlock)
        assert lb.items[0].nesting_level == 0
        assert lb.items[1].nesting_level == 1
        assert lb.items[2].nesting_level == 2

    def test_non_paragraph_elements_passthrough(self) -> None:
        elements = [
            StructuralElement(sectionBreak=SectionBreak()),
            _para("Item", list_id="kix.a"),
            StructuralElement(table=Table(rows=1, columns=1)),
        ]
        ctx = _lists_context({"kix.a": "GLYPH_TYPE_UNSPECIFIED"})
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 3
        assert isinstance(blocks[0], StructuralElement)
        assert isinstance(blocks[1], ListBlock)
        assert isinstance(blocks[2], StructuralElement)

    def test_no_lists_context_defaults_unordered(self) -> None:
        elements = [_para("Item", list_id="kix.a")]
        blocks = group_elements(elements, None)
        assert len(blocks) == 1
        lb = blocks[0]
        assert isinstance(lb, ListBlock)
        assert not lb.items[0].is_ordered

    def test_empty_elements(self) -> None:
        blocks = group_elements([])
        assert blocks == []

    def test_mixed_ordered_nesting(self) -> None:
        """A list that is unordered at level 0 but ordered at level 1."""
        elements = [
            _para("Top", list_id="kix.mixed", nesting=0),
            _para("Nested", list_id="kix.mixed", nesting=1),
        ]
        ctx: dict[str, Any] = {
            "kix.mixed": {
                "listProperties": {
                    "nestingLevels": [
                        {"glyphType": "GLYPH_TYPE_UNSPECIFIED", "startNumber": 1},
                        {"glyphType": "DECIMAL", "startNumber": 1},
                    ]
                }
            }
        }
        blocks = group_elements(elements, ctx)
        assert len(blocks) == 1
        lb = blocks[0]
        assert isinstance(lb, ListBlock)
        assert not lb.items[0].is_ordered
        assert lb.items[1].is_ordered


def _mono_text_run(content: str) -> TextRun:
    """Build a TextRun with Roboto Mono font."""
    return TextRun(
        content=content,
        textStyle=TextStyle(
            weightedFontFamily=WeightedFontFamily(fontFamily="Roboto Mono", weight=400),
        ),
    )


def _code_para(*runs: TextRun) -> StructuralElement:
    """Build a StructuralElement wrapping a code-like paragraph."""
    return StructuralElement(
        paragraph=Paragraph(
            elements=[ParagraphElement(textRun=r) for r in runs],
            paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
        )
    )


class TestCodeBlockGrouping:
    def test_code_block_detected(self) -> None:
        """Paragraphs between U+E907 bookends form a CodeBlock."""
        elements = [
            _code_para(TextRun(content="\ue907"), _mono_text_run("def foo():\n")),
            _code_para(_mono_text_run("    pass\n")),
            _code_para(_mono_text_run("\ue907\n")),
        ]
        blocks = group_elements(elements)
        assert len(blocks) == 1
        assert isinstance(blocks[0], CodeBlock)
        assert len(blocks[0].paragraphs) == 3

    def test_code_block_between_regular_paragraphs(self) -> None:
        elements = [
            _para("Before"),
            _code_para(TextRun(content="\ue907"), _mono_text_run("code\n")),
            _code_para(_mono_text_run("\ue907\n")),
            _para("After"),
        ]
        blocks = group_elements(elements)
        assert len(blocks) == 3
        assert isinstance(blocks[0], StructuralElement)
        assert isinstance(blocks[1], CodeBlock)
        assert isinstance(blocks[2], StructuralElement)

    def test_non_code_block_not_grouped(self) -> None:
        """Regular paragraphs without U+E907 are not grouped as code."""
        elements = [
            _para("Hello"),
            _para("World"),
        ]
        blocks = group_elements(elements)
        assert len(blocks) == 2
        assert all(isinstance(b, StructuralElement) for b in blocks)

    def test_start_and_end_on_same_paragraph(self) -> None:
        """A single-line code block with U+E907 on both ends."""
        elements = [
            _code_para(
                TextRun(content="\ue907"),
                _mono_text_run("single line"),
                TextRun(content="\ue907\n"),
            ),
        ]
        blocks = group_elements(elements)
        assert len(blocks) == 1
        assert isinstance(blocks[0], CodeBlock)
        assert len(blocks[0].paragraphs) == 1

    def test_multiple_code_blocks(self) -> None:
        """Two separate code blocks produce two CodeBlock objects."""
        elements = [
            _code_para(TextRun(content="\ue907"), _mono_text_run("block1\n")),
            _code_para(_mono_text_run("\ue907\n")),
            _para("Between"),
            _code_para(TextRun(content="\ue907"), _mono_text_run("block2\n")),
            _code_para(_mono_text_run("\ue907\n")),
        ]
        blocks = group_elements(elements)
        assert len(blocks) == 3
        assert isinstance(blocks[0], CodeBlock)
        assert isinstance(blocks[1], StructuralElement)
        assert isinstance(blocks[2], CodeBlock)
