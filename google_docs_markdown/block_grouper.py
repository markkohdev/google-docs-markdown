"""Pre-processing pass that groups StructuralElements into typed blocks.

The Google Docs API represents lists as consecutive Paragraph elements with
``bullet`` fields. This module groups those into ``ListBlock`` objects so
the serializer can render them as a single Markdown list.

Future phases can add more block types (e.g., CodeBlock for U+E907 detection).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google_docs_markdown.models.common import List as DocList
from google_docs_markdown.models.elements import Paragraph, StructuralElement

_ORDERED_GLYPH_TYPES = frozenset({"DECIMAL", "ZERO_DECIMAL", "UPPER_ALPHA", "ALPHA", "UPPER_ROMAN", "ROMAN"})


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


Block = StructuralElement | ListBlock


def group_elements(
    elements: list[StructuralElement],
    lists_context: dict[str, Any] | None = None,
) -> list[Block]:
    """Group consecutive list-item paragraphs into :class:`ListBlock` objects.

    Non-list structural elements pass through unchanged. Consecutive paragraphs
    with the same ``bullet.listId`` are collapsed into a single ``ListBlock``.
    A change of ``listId`` or any non-list element starts a new block.
    """
    blocks: list[Block] = []
    current_list: ListBlock | None = None
    current_list_id: str | None = None

    for element in elements:
        para = element.paragraph
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
    return glyph_type in _ORDERED_GLYPH_TYPES
