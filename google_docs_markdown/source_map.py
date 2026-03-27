"""Source map for bidirectional Markdown ↔ Google Docs API index translation.

During serialization, handlers record :class:`SourceSpan` entries that pair
Markdown character positions with API ``startIndex``/``endIndex`` values.
After serialization, the read-only :class:`SourceMap` provides ``lookup()``
to translate a Markdown character offset back to an API index — used by the
diff engine to generate surgical ``batchUpdate`` requests.

Syntax spans (formatting markers like ``**``, ``*``, ``~~``, comment tags)
have no API index counterpart; they are tracked separately so the diff
engine can skip them when mapping positions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SpanKind(StrEnum):
    """Classifies a source-map span for downstream consumers (diff engine)."""

    TEXT = "text"
    HEADING = "heading"
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"
    CODE_LINE = "code_line"
    WIDGET = "widget"
    SYNTAX = "syntax"
    IMAGE = "image"
    FOOTNOTE_REF = "footnote_ref"
    LINK = "link"
    METADATA = "metadata"


@dataclass(slots=True)
class SourceSpan:
    """A single mapping between Markdown text and Google Docs API indices.

    Attributes:
        md_start: Start offset in the Markdown output (0-based, inclusive).
        md_end: End offset in the Markdown output (0-based, exclusive).
        api_start: Corresponding ``startIndex`` in the API, or ``None`` for
            syntax-only spans (formatting markers, comment tags).
        api_end: Corresponding ``endIndex`` in the API, or ``None`` for
            syntax-only spans.
        tab_id: Tab identifier for multi-tab documents.
        segment_id: Segment identifier (body, header, footer, footnote).
        kind: Classification of this span.
        handler_type: The handler class name that produced this span.
        style: Optional style metadata for the span.
        tag_data: Optional comment-tag data dict for widget spans.
    """

    md_start: int
    md_end: int
    api_start: int | None = None
    api_end: int | None = None
    tab_id: str = ""
    segment_id: str = ""
    kind: SpanKind = SpanKind.TEXT
    handler_type: str = ""
    style: dict[str, Any] | None = None
    tag_data: dict[str, Any] | None = None


class SourceMap:
    """Read-only view over recorded source spans.

    Provides ``lookup()`` to translate a Markdown character position to
    the corresponding API index.
    """

    __slots__ = ("_spans", "_tab_id", "_segment_id")

    def __init__(self, spans: list[SourceSpan], *, tab_id: str = "", segment_id: str = "") -> None:
        self._spans = sorted(spans, key=lambda s: s.md_start)
        self._tab_id = tab_id
        self._segment_id = segment_id

    @property
    def spans(self) -> list[SourceSpan]:
        return list(self._spans)

    @property
    def tab_id(self) -> str:
        return self._tab_id

    @property
    def segment_id(self) -> str:
        return self._segment_id

    def lookup(self, md_pos: int) -> int | None:
        """Translate a Markdown character position to an API index.

        Returns ``None`` if *md_pos* falls within a syntax-only span or
        outside any recorded span.
        """
        for span in self._spans:
            if span.md_start <= md_pos < span.md_end:
                if span.api_start is None:
                    return None
                offset = md_pos - span.md_start
                return span.api_start + offset
        return None

    def span_at(self, md_pos: int) -> SourceSpan | None:
        """Return the span containing *md_pos*, or ``None``."""
        for span in self._spans:
            if span.md_start <= md_pos < span.md_end:
                return span
        return None

    def spans_in_range(self, md_start: int, md_end: int) -> list[SourceSpan]:
        """Return all spans overlapping the given Markdown range."""
        return [s for s in self._spans if s.md_start < md_end and s.md_end > md_start]

    def visible_spans(self) -> list[SourceSpan]:
        """Return only spans with API index counterparts (non-syntax)."""
        return [s for s in self._spans if s.api_start is not None]

    def syntax_spans(self) -> list[SourceSpan]:
        """Return only syntax spans (no API index counterpart)."""
        return [s for s in self._spans if s.api_start is None]

    def __len__(self) -> int:
        return len(self._spans)

    def __repr__(self) -> str:
        return f"SourceMap({len(self._spans)} spans)"


class SourceMapBuilder:
    """Mutable builder for recording source spans during serialization.

    Passed as ``ctx.source_map`` during serialization.  Handlers call
    :meth:`record` as they emit text.  After serialization, call
    :meth:`build` to get the frozen :class:`SourceMap`.
    """

    def __init__(self, *, tab_id: str = "", segment_id: str = "") -> None:
        self._spans: list[SourceSpan] = []
        self._md_offset: int = 0
        self._tab_id = tab_id
        self._segment_id = segment_id

    def record(
        self,
        text: str,
        *,
        api_start: int | None = None,
        api_end: int | None = None,
        kind: SpanKind = SpanKind.TEXT,
        handler_type: str = "",
        style: dict[str, Any] | None = None,
        tag_data: dict[str, Any] | None = None,
    ) -> None:
        """Record a span of emitted Markdown text.

        Args:
            text: The Markdown text being emitted.
            api_start: API startIndex, or None for syntax spans.
            api_end: API endIndex, or None for syntax spans.
            kind: Classification of the span.
            handler_type: Name of the handler class.
            style: Optional style metadata.
            tag_data: Optional comment-tag data.
        """
        if not text:
            return
        md_start = self._md_offset
        md_end = md_start + len(text)
        self._spans.append(
            SourceSpan(
                md_start=md_start,
                md_end=md_end,
                api_start=api_start,
                api_end=api_end,
                tab_id=self._tab_id,
                segment_id=self._segment_id,
                kind=kind,
                handler_type=handler_type,
                style=style,
                tag_data=tag_data,
            )
        )
        self._md_offset = md_end

    def record_syntax(self, text: str, *, handler_type: str = "") -> None:
        """Shorthand for recording a syntax span (no API counterpart)."""
        self.record(text, kind=SpanKind.SYNTAX, handler_type=handler_type)

    def advance(self, length: int) -> None:
        """Advance the Markdown offset without recording a span.

        Useful for paragraph separators (``\\n\\n``) that don't correspond
        to any API element.
        """
        self._md_offset += length

    def set_segment(self, *, tab_id: str = "", segment_id: str = "") -> None:
        """Update the tab/segment context for subsequent recordings."""
        self._tab_id = tab_id
        self._segment_id = segment_id

    @property
    def offset(self) -> int:
        """Current Markdown character offset."""
        return self._md_offset

    def build(self) -> SourceMap:
        """Create a frozen :class:`SourceMap` from recorded spans."""
        return SourceMap(list(self._spans), tab_id=self._tab_id, segment_id=self._segment_id)
