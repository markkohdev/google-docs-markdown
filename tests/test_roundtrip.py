"""Round-trip tests: JSON fixture → serialize → deserialize → verify requests."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from google_docs_markdown.markdown_deserializer import deserialize
from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.models.document import Document
from google_docs_markdown.models.requests import Request

FIXTURE_DIR = Path(__file__).parent / "resources" / "document_jsons"
SINGLE_TAB_FIXTURE = FIXTURE_DIR / "Markdown_Conversion_Example_-_Single-Tab.json"


def _load_fixture_doc_tab(fixture_path: Path):
    """Load a fixture JSON and return the first tab's DocumentTab."""
    doc = Document.model_validate(json.loads(fixture_path.read_text()))
    assert doc.tabs, f"No tabs in {fixture_path}"
    tab = doc.tabs[0]
    assert tab.documentTab, f"No documentTab in first tab of {fixture_path}"
    return tab.documentTab


def _roundtrip(fixture_path: Path) -> tuple[str, list[Request]]:
    """Serialize fixture to markdown, then deserialize back to requests."""
    doc_tab = _load_fixture_doc_tab(fixture_path)
    markdown = MarkdownSerializer().serialize(doc_tab)
    requests = deserialize(markdown)
    return markdown, requests


def _request_type_counts(requests: list[Request]) -> Counter[str]:
    """Count requests by type (the non-None field name on each Request)."""
    counts: Counter[str] = Counter()
    for r in requests:
        for field_name in Request.model_fields:
            if getattr(r, field_name, None) is not None:
                counts[field_name] += 1
    return counts


def _find_all(requests: list[Request], field: str) -> list[Request]:
    return [r for r in requests if getattr(r, field, None) is not None]


def _all_insert_text(requests: list[Request]) -> str:
    parts = []
    for r in requests:
        if r.insertText and r.insertText.text:
            parts.append(r.insertText.text)
    return "".join(parts)


class TestFixtureRoundtrip:
    """Tests that load the single-tab fixture and verify the serialize→deserialize roundtrip."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        if not SINGLE_TAB_FIXTURE.exists():
            pytest.skip(f"Fixture not found: {SINGLE_TAB_FIXTURE}")
        self.markdown, self.requests = _roundtrip(SINGLE_TAB_FIXTURE)

    def test_serialize_deserialize_request_count(self) -> None:
        """Roundtrip should produce a substantial number of requests (document has many elements)."""
        assert len(self.requests) > 20, f"Expected >20 requests from roundtrip, got {len(self.requests)}"
        counts = _request_type_counts(self.requests)
        assert counts["insertText"] > 0, "Should have insertText requests"

    def test_roundtrip_preserves_headings(self) -> None:
        """Headings in the markdown should produce updateParagraphStyle requests with heading styles."""
        assert "# " in self.markdown, "Serialized markdown should contain headings"

        style_reqs = _find_all(self.requests, "updateParagraphStyle")
        heading_styles = set()
        for r in style_reqs:
            ps = r.updateParagraphStyle
            if ps and ps.paragraphStyle and ps.paragraphStyle.namedStyleType:
                style_name = ps.paragraphStyle.namedStyleType
                if style_name.startswith("HEADING_"):
                    heading_styles.add(style_name)

        assert len(heading_styles) >= 2, f"Expected at least 2 heading levels, got {heading_styles}"

    def test_roundtrip_preserves_tables(self) -> None:
        """Tables in the document should produce insertTable requests after roundtrip."""
        table_reqs = _find_all(self.requests, "insertTable")
        assert len(table_reqs) >= 1, "Expected at least 1 insertTable request"

    def test_roundtrip_preserves_persons(self) -> None:
        """Person chips should produce insertPerson requests after roundtrip."""
        person_reqs = _find_all(self.requests, "insertPerson")
        assert len(person_reqs) >= 1, "Expected at least 1 insertPerson request"

    def test_roundtrip_preserves_dates(self) -> None:
        """Date chips should produce insertDate requests after roundtrip."""
        date_reqs = _find_all(self.requests, "insertDate")
        assert len(date_reqs) >= 1, "Expected at least 1 insertDate request"


class TestSimpleMarkdownRoundtrip:
    """Tests that take simple markdown strings and verify content preservation through deserialization."""

    def test_simple_markdown_idempotent(self) -> None:
        """All text content from a simple markdown should appear in the deserialized insert requests."""
        md = (
            "# Main Title\n\n"
            "A paragraph with **bold** and *italic* text.\n\n"
            "## Sub Heading\n\n"
            "Another paragraph with `inline code` and a [link](https://example.com).\n\n"
            "- bullet one\n"
            "- bullet two\n\n"
            "1. ordered one\n"
            "2. ordered two\n"
        )
        requests = deserialize(md)
        all_text = _all_insert_text(requests)

        for expected in [
            "Main Title",
            "bold",
            "italic",
            "Sub Heading",
            "inline code",
            "link",
            "bullet one",
            "bullet two",
            "ordered one",
            "ordered two",
        ]:
            assert expected in all_text, f"Expected '{expected}' in insert text, got: {all_text!r}"

    def test_table_roundtrip(self) -> None:
        """A markdown table should roundtrip into an insertTable + cell inserts."""
        md = "| Name | Value |\n| --- | --- |\n| foo | 42 |\n"
        requests = deserialize(md)
        table_reqs = _find_all(requests, "insertTable")
        assert len(table_reqs) == 1

        all_text = _all_insert_text(requests)
        assert "Name" in all_text
        assert "foo" in all_text
        assert "42" in all_text

    def test_code_block_roundtrip(self) -> None:
        """Fenced code blocks should preserve their content."""
        md = "```python\ndef hello():\n    return 42\n```\n"
        requests = deserialize(md)
        all_text = _all_insert_text(requests)
        assert "def hello():" in all_text
        assert "return 42" in all_text

    def test_heading_levels_roundtrip(self) -> None:
        """All 6 heading levels should produce the correct paragraph style."""
        md = "\n\n".join(f"{'#' * i} Heading {i}" for i in range(1, 7)) + "\n"
        requests = deserialize(md)

        style_reqs = _find_all(requests, "updateParagraphStyle")
        heading_styles = set()
        for r in style_reqs:
            ps = r.updateParagraphStyle
            if ps and ps.paragraphStyle and ps.paragraphStyle.namedStyleType:
                heading_styles.add(ps.paragraphStyle.namedStyleType)

        for level in range(1, 7):
            assert f"HEADING_{level}" in heading_styles, f"HEADING_{level} missing from {heading_styles}"

    def test_formatting_types_roundtrip(self) -> None:
        """Bold, italic, strikethrough, and inline code should all generate style requests."""
        md = "**bold** *italic* ~~struck~~ `code`\n"
        requests = deserialize(md)
        counts = _request_type_counts(requests)
        assert counts["updateTextStyle"] >= 3, f"Expected >=3 text style requests, got {counts['updateTextStyle']}"

    def test_person_tag_roundtrip(self) -> None:
        """Person comment tags should produce insertPerson requests."""
        md = '<!-- person: {"email": "test@example.com"} -->Test User<!-- /person -->\n'
        requests = deserialize(md)
        person_reqs = _find_all(requests, "insertPerson")
        assert len(person_reqs) == 1
        assert person_reqs[0].insertPerson is not None
        assert person_reqs[0].insertPerson.personProperties is not None
        assert person_reqs[0].insertPerson.personProperties.email == "test@example.com"

    def test_date_tag_roundtrip(self) -> None:
        """Date comment tags should produce insertDate requests."""
        md = "<!-- date -->2026-03-15<!-- /date -->\n"
        requests = deserialize(md)
        date_reqs = _find_all(requests, "insertDate")
        assert len(date_reqs) == 1

    def test_content_coverage(self) -> None:
        """Most meaningful words from the markdown should appear in insert requests."""
        md = (
            "# Document Title\n\n"
            "Introduction paragraph with important details.\n\n"
            "## Chapter One\n\n"
            "Content of chapter one with **emphasis** on key points.\n\n"
            "- first item\n"
            "- second item\n"
        )
        requests = deserialize(md)
        all_text = _all_insert_text(requests)

        keywords = [
            "Document Title",
            "Introduction",
            "important",
            "details",
            "Chapter One",
            "Content",
            "emphasis",
            "key points",
            "first item",
            "second item",
        ]
        found = sum(1 for kw in keywords if kw in all_text)
        coverage = found / len(keywords) * 100
        assert coverage >= 80, f"Content coverage {coverage:.1f}% is below 80% threshold"
