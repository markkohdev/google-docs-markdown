"""Tests for the diff engine (Phase 3.8)."""

from __future__ import annotations

from google_docs_markdown.diff_engine import DiffEngine, DiffOp, DiffOpKind, _line_offsets
from google_docs_markdown.models.requests import Request
from google_docs_markdown.source_map import SourceMap, SourceMapBuilder, SourceSpan, SpanKind


def _simple_source_map(text: str, *, api_offset: int = 1) -> SourceMap:
    """Build a trivial 1:1 source map where md_pos maps to api_offset + md_pos."""
    builder = SourceMapBuilder()
    builder.record(
        text,
        api_start=api_offset,
        api_end=api_offset + len(text),
        kind=SpanKind.TEXT,
    )
    return builder.build()


class TestComputeDiff:
    def test_identical_texts_no_ops(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("Hello\n", "Hello\n")
        assert ops == []

    def test_empty_texts_no_ops(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("", "")
        assert ops == []

    def test_simple_insertion(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("Line 1\n", "Line 1\nLine 2\n")
        assert len(ops) == 1
        assert ops[0].kind == DiffOpKind.INSERT
        assert ops[0].local_text == "Line 2\n"

    def test_simple_deletion(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("Line 1\nLine 2\n", "Line 1\n")
        assert len(ops) == 1
        assert ops[0].kind == DiffOpKind.DELETE
        assert ops[0].canonical_text == "Line 2\n"

    def test_simple_replacement(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("Old text\n", "New text\n")
        assert len(ops) == 1
        assert ops[0].kind == DiffOpKind.REPLACE
        assert ops[0].canonical_text == "Old text\n"
        assert ops[0].local_text == "New text\n"

    def test_multiple_ops(self) -> None:
        canonical = "Line 1\nLine 2\nLine 3\n"
        local = "Line 1\nModified\nLine 3\nLine 4\n"
        engine = DiffEngine()
        ops = engine.compute_diff(canonical, local)
        assert len(ops) >= 1

    def test_metadata_stripped_before_diff(self) -> None:
        metadata = '<!-- google-docs-metadata\n{"documentId": "abc"}\n-->'
        canonical = "Hello\n\n" + metadata
        local = "Hello\n"
        engine = DiffEngine()
        ops = engine.compute_diff(canonical, local)
        assert ops == []

    def test_insert_at_beginning(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("Existing\n", "New line\nExisting\n")
        assert len(ops) == 1
        assert ops[0].kind == DiffOpKind.INSERT
        assert ops[0].local_text == "New line\n"

    def test_delete_at_beginning(self) -> None:
        engine = DiffEngine()
        ops = engine.compute_diff("First\nSecond\n", "Second\n")
        assert len(ops) == 1
        assert ops[0].kind == DiffOpKind.DELETE
        assert ops[0].canonical_text == "First\n"

    def test_multiline_replacement(self) -> None:
        canonical = "A\nB\nC\n"
        local = "A\nX\nY\nC\n"
        engine = DiffEngine()
        ops = engine.compute_diff(canonical, local)
        assert len(ops) == 1
        assert ops[0].kind == DiffOpKind.REPLACE


class TestComputeRequests:
    def test_no_changes_returns_empty(self) -> None:
        engine = DiffEngine()
        sm = _simple_source_map("Hello\n")
        requests = engine.compute_requests("Hello\n", "Hello\n", sm)
        assert requests == []

    def test_insertion_produces_insert_request(self) -> None:
        text = "Line 1\n"
        sm = _simple_source_map(text)

        engine = DiffEngine()
        requests = engine.compute_requests(text, "Line 1\nLine 2\n", sm)

        insert_reqs = [r for r in requests if r.insertText is not None]
        assert len(insert_reqs) >= 1
        assert insert_reqs[0].insertText is not None
        assert "Line 2" in (insert_reqs[0].insertText.text or "")

    def test_deletion_produces_delete_request(self) -> None:
        text = "Line 1\nLine 2\n"
        sm = _simple_source_map(text)

        engine = DiffEngine()
        requests = engine.compute_requests(text, "Line 1\n", sm)

        delete_reqs = [r for r in requests if r.deleteContentRange is not None]
        assert len(delete_reqs) >= 1

    def test_replacement_produces_delete_and_insert(self) -> None:
        text = "Old text\n"
        sm = _simple_source_map(text)

        engine = DiffEngine()
        requests = engine.compute_requests(text, "New text\n", sm)

        delete_reqs = [r for r in requests if r.deleteContentRange is not None]
        insert_reqs = [r for r in requests if r.insertText is not None]
        assert len(delete_reqs) >= 1
        assert len(insert_reqs) >= 1

    def test_deletions_ordered_end_to_start(self) -> None:
        text = "Line 1\nLine 2\nLine 3\n"
        sm = _simple_source_map(text)

        engine = DiffEngine()
        requests = engine.compute_requests(text, "", sm)

        delete_reqs = [r for r in requests if r.deleteContentRange is not None]
        if len(delete_reqs) >= 2:
            indices = [
                r.deleteContentRange.range.startIndex
                for r in delete_reqs
                if r.deleteContentRange and r.deleteContentRange.range and r.deleteContentRange.range.startIndex is not None
            ]
            assert indices == sorted(indices, reverse=True)

    def test_tab_id_propagated(self) -> None:
        text = "Hello\n"
        sm = _simple_source_map(text)

        engine = DiffEngine()
        requests = engine.compute_requests(
            text, "Hello\nWorld\n", sm, tab_id="t.42"
        )

        for r in requests:
            if r.insertText and r.insertText.location:
                assert r.insertText.location.tabId == "t.42"

    def test_segment_id_propagated(self) -> None:
        text = "Hello\n"
        sm = _simple_source_map(text)

        engine = DiffEngine()
        requests = engine.compute_requests(
            text, "Hello\nWorld\n", sm, segment_id="header.1"
        )

        for r in requests:
            if r.insertText and r.insertText.location:
                assert r.insertText.location.segmentId == "header.1"


class TestLineOffsets:
    def test_empty_string(self) -> None:
        assert _line_offsets("") == [0]

    def test_single_line(self) -> None:
        assert _line_offsets("Hello\n") == [0, 6]

    def test_multiple_lines(self) -> None:
        assert _line_offsets("A\nBB\nCCC\n") == [0, 2, 5, 9]

    def test_no_trailing_newline(self) -> None:
        assert _line_offsets("Hello") == [0]

    def test_empty_lines(self) -> None:
        assert _line_offsets("\n\n") == [0, 1, 2]


class TestDiffOp:
    def test_dataclass_fields(self) -> None:
        op = DiffOp(
            kind=DiffOpKind.REPLACE,
            canonical_start=0,
            canonical_end=1,
            local_start=0,
            local_end=2,
            canonical_text="old\n",
            local_text="new1\nnew2\n",
        )
        assert op.kind == DiffOpKind.REPLACE
        assert op.canonical_text == "old\n"
        assert op.local_text == "new1\nnew2\n"

    def test_default_texts_empty(self) -> None:
        op = DiffOp(
            kind=DiffOpKind.EQUAL,
            canonical_start=0,
            canonical_end=0,
            local_start=0,
            local_end=0,
        )
        assert op.canonical_text == ""
        assert op.local_text == ""


class TestDiffOpKind:
    def test_enum_values(self) -> None:
        assert DiffOpKind.INSERT == "insert"
        assert DiffOpKind.DELETE == "delete"
        assert DiffOpKind.REPLACE == "replace"
        assert DiffOpKind.EQUAL == "equal"
