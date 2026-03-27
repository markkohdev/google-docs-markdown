"""Diff engine for computing surgical Google Docs ``batchUpdate`` requests.

Compares *canonical* Markdown (serialized from the live document via
:class:`~google_docs_markdown.markdown_serializer.MarkdownSerializer`) against
*local* Markdown (edited by the user) and produces a minimal list of
:class:`~google_docs_markdown.models.requests.Request` objects that, when
applied via ``batchUpdate``, transform the live document to match the local
version.

Pipeline
--------
1. Strip embedded metadata blocks from both texts (metadata is document-level,
   not content).
2. Compute a line-level diff using :func:`difflib.unified_diff`-style
   operations via :class:`difflib.SequenceMatcher`.
3. Convert diff operations into :class:`DiffOp` objects with Markdown
   character ranges.
4. Map Markdown character ranges to API index ranges via :class:`SourceMap`.
5. Generate ``deleteContentRange`` and ``insertText`` (plus styling) requests,
   ordered so that indices remain valid:
   - Deletions are emitted **end-to-start** (highest index first).
   - Insertions are emitted **start-to-end** (lowest index first).
   - Style updates follow insertions.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from enum import StrEnum

from google_docs_markdown.markdown_deserializer import MarkdownDeserializer
from google_docs_markdown.metadata import strip_metadata
from google_docs_markdown.models.common import Location, Range
from google_docs_markdown.models.requests import (
    DeleteContentRangeRequest,
    InsertTextRequest,
    Request,
)
from google_docs_markdown.source_map import SourceMap


class DiffOpKind(StrEnum):
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    EQUAL = "equal"


@dataclass(slots=True)
class DiffOp:
    """A single diff operation between canonical and local Markdown.

    Attributes:
        kind: The type of operation.
        canonical_start: Start line in the canonical text (0-based).
        canonical_end: End line in the canonical text (exclusive).
        local_start: Start line in the local text (0-based).
        local_end: End line in the local text (exclusive).
        canonical_text: The text from the canonical version (for delete/replace).
        local_text: The text from the local version (for insert/replace).
    """

    kind: DiffOpKind
    canonical_start: int
    canonical_end: int
    local_start: int
    local_end: int
    canonical_text: str = ""
    local_text: str = ""


class DiffEngine:
    """Compute surgical ``batchUpdate`` requests from Markdown diffs.

    Compares canonical (serialized from live doc) Markdown against local
    (user-edited) Markdown and produces the minimal set of API requests
    to reconcile them.
    """

    def __init__(self) -> None:
        self._deserializer = MarkdownDeserializer()

    def compute_diff(
        self,
        canonical: str,
        local: str,
    ) -> list[DiffOp]:
        """Compute line-level diff operations between two Markdown texts.

        Both inputs are stripped of embedded metadata blocks before diffing.

        Args:
            canonical: Markdown serialized from the live document.
            local: Markdown edited locally by the user.

        Returns:
            List of :class:`DiffOp` objects. Empty list means no changes.
        """
        canonical_clean = strip_metadata(canonical)
        local_clean = strip_metadata(local)

        canonical_lines = canonical_clean.splitlines(keepends=True)
        local_lines = local_clean.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, canonical_lines, local_lines)
        ops: list[DiffOp] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            elif tag == "replace":
                ops.append(
                    DiffOp(
                        kind=DiffOpKind.REPLACE,
                        canonical_start=i1,
                        canonical_end=i2,
                        local_start=j1,
                        local_end=j2,
                        canonical_text="".join(canonical_lines[i1:i2]),
                        local_text="".join(local_lines[j1:j2]),
                    )
                )
            elif tag == "delete":
                ops.append(
                    DiffOp(
                        kind=DiffOpKind.DELETE,
                        canonical_start=i1,
                        canonical_end=i2,
                        local_start=j1,
                        local_end=j2,
                        canonical_text="".join(canonical_lines[i1:i2]),
                    )
                )
            elif tag == "insert":
                ops.append(
                    DiffOp(
                        kind=DiffOpKind.INSERT,
                        canonical_start=i1,
                        canonical_end=i2,
                        local_start=j1,
                        local_end=j2,
                        local_text="".join(local_lines[j1:j2]),
                    )
                )

        return ops

    def compute_requests(
        self,
        canonical: str,
        local: str,
        source_map: SourceMap,
        *,
        tab_id: str = "",
        segment_id: str = "",
    ) -> list[Request]:
        """Compute ``batchUpdate`` requests to transform the live doc.

        This is the main entry point. Returns an empty list when no changes
        are detected (enabling no-op short-circuit).

        When the source map has sufficient coverage, surgical (line-level)
        edits are generated.  When the source map cannot map the changed
        positions (e.g. because only structural spans were recorded), falls
        back to a full-content replacement strategy: delete everything from
        index 1, then re-insert using the deserializer.

        Args:
            canonical: Markdown serialized from the live document.
            local: The local (edited) Markdown to push.
            source_map: Source map from the serialization pass.
            tab_id: Tab ID for multi-tab documents.
            segment_id: Segment ID (body, header, footer).

        Returns:
            Ordered list of :class:`Request` objects ready for ``batchUpdate``.
        """
        ops = self.compute_diff(canonical, local)
        if not ops:
            return []

        surgical = self._try_surgical(ops, canonical, source_map, tab_id=tab_id, segment_id=segment_id)
        if surgical is not None:
            return surgical

        return self._full_replacement(canonical, local, tab_id=tab_id, segment_id=segment_id)

    def _try_surgical(
        self,
        ops: list[DiffOp],
        canonical: str,
        source_map: SourceMap,
        *,
        tab_id: str,
        segment_id: str,
    ) -> list[Request] | None:
        """Attempt surgical edits via source map.  Returns ``None`` on mapping failure."""
        canonical_clean = strip_metadata(canonical)
        line_offsets_canonical = _line_offsets(canonical_clean)

        deletions: list[Request] = []
        insertions: list[Request] = []
        style_requests: list[Request] = []
        mapping_failed = False

        for op in ops:
            if op.kind == DiffOpKind.DELETE:
                md_start = line_offsets_canonical[op.canonical_start]
                md_end = (
                    line_offsets_canonical[op.canonical_end]
                    if op.canonical_end < len(line_offsets_canonical)
                    else len(canonical_clean)
                )
                api_start = source_map.lookup(md_start)
                api_end = source_map.lookup(md_end - 1)
                if api_start is None or api_end is None:
                    mapping_failed = True
                    break
                deletions.append(
                    Request(
                        deleteContentRange=DeleteContentRangeRequest(
                            range=Range(
                                startIndex=api_start,
                                endIndex=api_end + 1,
                                segmentId=segment_id or None,
                                tabId=tab_id or None,
                            )
                        )
                    )
                )

            elif op.kind == DiffOpKind.INSERT:
                md_pos = (
                    line_offsets_canonical[op.canonical_start]
                    if op.canonical_start < len(line_offsets_canonical)
                    else len(canonical_clean)
                )
                api_pos = source_map.lookup(md_pos)
                if api_pos is None and md_pos > 0:
                    api_pos = source_map.lookup(md_pos - 1)
                    if api_pos is not None:
                        api_pos += 1
                if api_pos is None:
                    mapping_failed = True
                    break
                insert_req, style_reqs = self._make_insert_requests(
                    op.local_text,
                    api_pos,
                    tab_id=tab_id,
                    segment_id=segment_id,
                )
                insertions.append(insert_req)
                style_requests.extend(style_reqs)

            elif op.kind == DiffOpKind.REPLACE:
                md_start = line_offsets_canonical[op.canonical_start]
                md_end = (
                    line_offsets_canonical[op.canonical_end]
                    if op.canonical_end < len(line_offsets_canonical)
                    else len(canonical_clean)
                )
                api_start = source_map.lookup(md_start)
                api_end = source_map.lookup(md_end - 1)
                if api_start is None or api_end is None:
                    mapping_failed = True
                    break
                deletions.append(
                    Request(
                        deleteContentRange=DeleteContentRangeRequest(
                            range=Range(
                                startIndex=api_start,
                                endIndex=api_end + 1,
                                segmentId=segment_id or None,
                                tabId=tab_id or None,
                            )
                        )
                    )
                )
                insert_req, style_reqs = self._make_insert_requests(
                    op.local_text,
                    api_start,
                    tab_id=tab_id,
                    segment_id=segment_id,
                )
                insertions.append(insert_req)
                style_requests.extend(style_reqs)

        if mapping_failed:
            return None

        deletions.sort(
            key=lambda r: (
                -(
                    r.deleteContentRange.range.startIndex
                    if r.deleteContentRange and r.deleteContentRange.range and r.deleteContentRange.range.startIndex
                    else 0
                )
            )
        )

        return deletions + insertions + style_requests

    def _full_replacement(
        self,
        canonical: str,
        local: str,
        *,
        tab_id: str,
        segment_id: str,
    ) -> list[Request]:
        """Fallback: delete all body content and re-insert from local markdown.

        Used when the source map cannot map diff positions to API indices.
        """
        canonical_clean = strip_metadata(canonical)

        requests: list[Request] = []

        content_len = len(canonical_clean.rstrip("\n"))
        if content_len > 0:
            requests.append(
                Request(
                    deleteContentRange=DeleteContentRangeRequest(
                        range=Range(
                            startIndex=1,
                            endIndex=1 + content_len,
                            segmentId=segment_id or None,
                            tabId=tab_id or None,
                        )
                    )
                )
            )

        local_clean = strip_metadata(local)
        insert_requests = self._deserializer.deserialize(
            local_clean,
            tab_id=tab_id,
            segment_id=segment_id,
        )
        requests.extend(insert_requests)

        return requests

    def _make_insert_requests(
        self,
        text: str,
        api_index: int,
        *,
        tab_id: str = "",
        segment_id: str = "",
    ) -> tuple[Request, list[Request]]:
        """Create an insert-text request and any associated style requests.

        For plain text inserts, only the ``InsertTextRequest`` is returned.
        The style requests list will be empty for simple text changes.
        """
        insert_req = Request(
            insertText=InsertTextRequest(
                text=text,
                location=Location(
                    index=api_index,
                    segmentId=segment_id or None,
                    tabId=tab_id or None,
                ),
            )
        )
        return insert_req, []


def _line_offsets(text: str) -> list[int]:
    """Compute the character offset of each line start in *text*.

    ``offsets[0]`` is always 0. ``offsets[n]`` is the character offset of
    the start of line *n*.
    """
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets
