"""Tests for the source map module."""

from __future__ import annotations

from google_docs_markdown.source_map import (
    SourceMap,
    SourceMapBuilder,
    SourceSpan,
    SpanKind,
)


class TestSourceSpan:
    def test_basic_creation(self) -> None:
        span = SourceSpan(md_start=0, md_end=5, api_start=1, api_end=6)
        assert span.md_start == 0
        assert span.md_end == 5
        assert span.api_start == 1
        assert span.api_end == 6
        assert span.kind == SpanKind.TEXT

    def test_syntax_span_no_api_indices(self) -> None:
        span = SourceSpan(md_start=0, md_end=2, kind=SpanKind.SYNTAX)
        assert span.api_start is None
        assert span.api_end is None
        assert span.kind == SpanKind.SYNTAX

    def test_span_with_metadata(self) -> None:
        span = SourceSpan(
            md_start=0,
            md_end=10,
            api_start=1,
            api_end=11,
            tab_id="t.0",
            segment_id="body",
            kind=SpanKind.HEADING,
            handler_type="HeadingHandler",
            style={"level": 1},
            tag_data={"foo": "bar"},
        )
        assert span.tab_id == "t.0"
        assert span.segment_id == "body"
        assert span.handler_type == "HeadingHandler"
        assert span.style == {"level": 1}
        assert span.tag_data == {"foo": "bar"}


class TestSourceMap:
    def _make_map(self, spans: list[SourceSpan]) -> SourceMap:
        return SourceMap(spans)

    def test_empty_source_map(self) -> None:
        sm = self._make_map([])
        assert len(sm) == 0
        assert sm.lookup(0) is None
        assert sm.span_at(0) is None

    def test_lookup_within_span(self) -> None:
        spans = [SourceSpan(md_start=0, md_end=5, api_start=1, api_end=6)]
        sm = self._make_map(spans)
        assert sm.lookup(0) == 1
        assert sm.lookup(2) == 3
        assert sm.lookup(4) == 5
        assert sm.lookup(5) is None

    def test_lookup_syntax_span_returns_none(self) -> None:
        spans = [
            SourceSpan(md_start=0, md_end=2, kind=SpanKind.SYNTAX),
            SourceSpan(md_start=2, md_end=7, api_start=1, api_end=6),
            SourceSpan(md_start=7, md_end=9, kind=SpanKind.SYNTAX),
        ]
        sm = self._make_map(spans)
        assert sm.lookup(0) is None
        assert sm.lookup(1) is None
        assert sm.lookup(2) == 1
        assert sm.lookup(6) == 5
        assert sm.lookup(7) is None

    def test_span_at(self) -> None:
        span1 = SourceSpan(md_start=0, md_end=5, api_start=1, api_end=6)
        span2 = SourceSpan(md_start=5, md_end=10, api_start=6, api_end=11)
        sm = self._make_map([span1, span2])
        assert sm.span_at(2) is span1
        assert sm.span_at(7) is span2
        assert sm.span_at(10) is None

    def test_spans_in_range(self) -> None:
        span1 = SourceSpan(md_start=0, md_end=5, api_start=1, api_end=6)
        span2 = SourceSpan(md_start=5, md_end=10, api_start=6, api_end=11)
        span3 = SourceSpan(md_start=10, md_end=15, api_start=11, api_end=16)
        sm = self._make_map([span1, span2, span3])
        assert sm.spans_in_range(3, 12) == [span1, span2, span3]
        assert sm.spans_in_range(5, 10) == [span2]
        assert sm.spans_in_range(0, 5) == [span1]
        assert sm.spans_in_range(15, 20) == []

    def test_visible_and_syntax_spans(self) -> None:
        span1 = SourceSpan(md_start=0, md_end=2, kind=SpanKind.SYNTAX)
        span2 = SourceSpan(md_start=2, md_end=7, api_start=1, api_end=6)
        span3 = SourceSpan(md_start=7, md_end=9, kind=SpanKind.SYNTAX)
        sm = self._make_map([span1, span2, span3])
        assert len(sm.visible_spans()) == 1
        assert sm.visible_spans()[0] is span2
        assert len(sm.syntax_spans()) == 2

    def test_sorted_by_md_start(self) -> None:
        span_b = SourceSpan(md_start=5, md_end=10, api_start=6, api_end=11)
        span_a = SourceSpan(md_start=0, md_end=5, api_start=1, api_end=6)
        sm = self._make_map([span_b, span_a])
        assert sm.spans[0].md_start == 0
        assert sm.spans[1].md_start == 5

    def test_repr(self) -> None:
        sm = self._make_map([SourceSpan(md_start=0, md_end=5)])
        assert "1 spans" in repr(sm)

    def test_tab_and_segment_id(self) -> None:
        sm = SourceMap([], tab_id="t.1", segment_id="header")
        assert sm.tab_id == "t.1"
        assert sm.segment_id == "header"


class TestSourceMapBuilder:
    def test_basic_recording(self) -> None:
        builder = SourceMapBuilder()
        builder.record("hello", api_start=1, api_end=6, kind=SpanKind.TEXT)
        builder.record(" ", api_start=6, api_end=7, kind=SpanKind.TEXT)
        builder.record("world", api_start=7, api_end=12, kind=SpanKind.TEXT)
        sm = builder.build()
        assert len(sm) == 3
        assert sm.lookup(0) == 1
        assert sm.lookup(5) == 6
        assert sm.lookup(6) == 7

    def test_record_syntax(self) -> None:
        builder = SourceMapBuilder()
        builder.record_syntax("**", handler_type="BoldHandler")
        builder.record("bold text", api_start=1, api_end=10)
        builder.record_syntax("**", handler_type="BoldHandler")
        sm = builder.build()
        assert sm.lookup(0) is None
        assert sm.lookup(2) == 1
        assert sm.lookup(11) is None

    def test_advance(self) -> None:
        builder = SourceMapBuilder()
        builder.record("hello", api_start=1, api_end=6)
        builder.advance(2)
        builder.record("world", api_start=6, api_end=11)
        sm = builder.build()
        assert sm.spans[0].md_end == 5
        assert sm.spans[1].md_start == 7

    def test_set_segment(self) -> None:
        builder = SourceMapBuilder(tab_id="t.0")
        builder.set_segment(tab_id="t.1", segment_id="header")
        builder.record("text", api_start=1, api_end=5)
        sm = builder.build()
        assert sm.spans[0].tab_id == "t.1"
        assert sm.spans[0].segment_id == "header"

    def test_empty_text_not_recorded(self) -> None:
        builder = SourceMapBuilder()
        builder.record("", api_start=1, api_end=1)
        sm = builder.build()
        assert len(sm) == 0

    def test_offset_tracking(self) -> None:
        builder = SourceMapBuilder()
        assert builder.offset == 0
        builder.record("abc", api_start=1, api_end=4)
        assert builder.offset == 3
        builder.advance(2)
        assert builder.offset == 5

    def test_build_produces_immutable_source_map(self) -> None:
        builder = SourceMapBuilder()
        builder.record("text", api_start=1, api_end=5)
        sm = builder.build()
        builder.record("more", api_start=5, api_end=9)
        assert len(sm) == 1


class TestSpanKind:
    def test_all_kinds_exist(self) -> None:
        expected = {
            "text",
            "heading",
            "list_item",
            "table_cell",
            "code_line",
            "widget",
            "syntax",
            "image",
            "footnote_ref",
            "link",
            "metadata",
        }
        actual = {k.value for k in SpanKind}
        assert actual == expected
