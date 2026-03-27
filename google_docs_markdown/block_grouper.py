"""Pre-processing pass that groups StructuralElements into typed blocks.

The Google Docs API represents lists as consecutive Paragraph elements with
``bullet`` fields. This module groups those into ``ListBlock`` objects so
the serializer can render them as a single Markdown list.

Code blocks are detected via U+E907 boundary markers and monospace font
(``Roboto Mono``).  Consecutive monospace paragraphs between U+E907
bookends are grouped into ``CodeBlock`` objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google_docs_markdown.element_registry import CODE_BLOCK_MARKER, ORDERED_GLYPH_TYPES
from google_docs_markdown.models.common import List as DocList
from google_docs_markdown.models.elements import Paragraph, StructuralElement


@dataclass
class ListItem:
    """A single item within a Markdown list."""

    paragraph: Paragraph
    nesting_level: int
    is_ordered: bool


@dataclass
class ListBlock:
    """A run of consecutive list-item paragraphs sharing the same ``listId``."""

    items: list[ListItem] = field(default_factory=list)


@dataclass
class CodeBlock:
    """A run of consecutive monospace paragraphs between U+E907 bookends."""

    paragraphs: list[Paragraph] = field(default_factory=list)


Block = StructuralElement | ListBlock | CodeBlock


def group_elements(
    elements: list[StructuralElement],
    lists_context: dict[str, Any] | None = None,
) -> list[Block]:
    """Group structural elements into typed blocks.

    * Consecutive paragraphs with the same ``bullet.listId`` are collapsed
      into a single :class:`ListBlock`.
    * Paragraphs between U+E907 bookends that use a monospace font are
      collapsed into a single :class:`CodeBlock`.
    * All other structural elements pass through unchanged.
    """
    blocks: list[Block] = []
    current_list: ListBlock | None = None
    current_list_id: str | None = None
    current_code: CodeBlock | None = None

    for element in elements:
        para = element.paragraph

        if para and _is_code_block_start(para) and current_code is None:
            current_list = None
            current_list_id = None
            current_code = CodeBlock()
            current_code.paragraphs.append(para)
            blocks.append(current_code)
            continue

        if current_code is not None and para:
            current_code.paragraphs.append(para)
            if _is_code_block_end(para):
                current_code = None
            continue

        if current_code is not None and not para:
            current_code = None

        if para and para.bullet and para.bullet.listId:
            list_id = para.bullet.listId
            nesting = para.bullet.nestingLevel or 0
            is_ordered = _is_ordered_list(list_id, nesting, lists_context)

            if current_list is None or list_id != current_list_id:
                current_list = ListBlock()
                current_list_id = list_id
                blocks.append(current_list)

            current_list.items.append(
                ListItem(
                    paragraph=para,
                    nesting_level=nesting,
                    is_ordered=is_ordered,
                )
            )
        else:
            current_list = None
            current_list_id = None
            blocks.append(element)

    return blocks


def _is_code_block_start(para: Paragraph) -> bool:
    """Return True if the paragraph starts a code block (U+E907 bookend)."""
    if not para.elements:
        return False
    first = para.elements[0]
    if not first.textRun or not first.textRun.content:
        return False
    return first.textRun.content.startswith(CODE_BLOCK_MARKER)


def _is_code_block_end(para: Paragraph) -> bool:
    """Return True if the paragraph ends a code block (trailing U+E907)."""
    if not para.elements:
        return False
    for elem in reversed(para.elements):
        if not elem.textRun or not elem.textRun.content:
            continue
        content = elem.textRun.content.rstrip("\n")
        if content.endswith(CODE_BLOCK_MARKER):
            return True
        if content:
            return False
    return False


def _is_ordered_list(
    list_id: str,
    nesting_level: int,
    lists_context: dict[str, Any] | None,
) -> bool:
    """Check whether the given list at the given nesting level uses ordered glyphs."""
    if not lists_context:
        return False

    raw = lists_context.get(list_id)
    if raw is None:
        return False

    list_obj = raw if isinstance(raw, DocList) else DocList.model_validate(raw)

    if not list_obj.listProperties or not list_obj.listProperties.nestingLevels:
        return False

    levels = list_obj.listProperties.nestingLevels
    if nesting_level >= len(levels):
        return False

    glyph_type = levels[nesting_level].glyphType
    return glyph_type in ORDERED_GLYPH_TYPES
