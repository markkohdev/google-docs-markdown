"""Tests for embedded metadata block serialization and parsing."""

from __future__ import annotations

from google_docs_markdown.metadata import parse_metadata, serialize_metadata, strip_metadata


class TestSerializeMetadata:
    def test_basic(self) -> None:
        result = serialize_metadata(document_id="abc123", tab_id="t.0")
        assert "<!-- google-docs-metadata" in result
        assert "-->" in result
        assert '"documentId"' in result
        assert '"abc123"' in result

    def test_with_default_styles(self) -> None:
        result = serialize_metadata(
            document_id="doc1",
            default_styles={"fontFamily": "Arial", "fontSize": 11},
        )
        assert '"fontFamily"' in result
        assert "Arial" in result

    def test_escapes_angle_brackets(self) -> None:
        result = serialize_metadata(
            document_id="doc1",
            revision_id="rev-->danger",
        )
        assert "-->" not in result.split("\n")[1:-1].__repr__() or "\\u003e" in result

    def test_empty_metadata(self) -> None:
        result = serialize_metadata()
        assert "<!-- google-docs-metadata" in result
        assert "-->" in result


class TestParseMetadata:
    def test_roundtrip(self) -> None:
        block = serialize_metadata(
            document_id="doc123",
            tab_id="t.0",
            revision_id="rev1",
            default_styles={"fontFamily": "Proxima Nova", "fontSize": 11},
        )
        markdown = f"# Hello\n\nSome content\n\n{block}\n"
        parsed = parse_metadata(markdown)
        assert parsed is not None
        assert parsed["documentId"] == "doc123"
        assert parsed["tabId"] == "t.0"
        assert parsed["revisionId"] == "rev1"
        assert parsed["defaultStyles"]["fontFamily"] == "Proxima Nova"

    def test_no_metadata(self) -> None:
        assert parse_metadata("# Just markdown\n\nNo metadata here.\n") is None

    def test_with_escaped_angle_brackets(self) -> None:
        block = serialize_metadata(
            document_id="test",
            revision_id="has>bracket",
        )
        markdown = f"Content\n\n{block}\n"
        parsed = parse_metadata(markdown)
        assert parsed is not None
        assert parsed["revisionId"] == "has>bracket"


class TestStripMetadata:
    def test_strips_metadata_block(self) -> None:
        block = serialize_metadata(document_id="doc1")
        markdown = f"# Title\n\nContent\n\n{block}\n"
        stripped = strip_metadata(markdown)
        assert "google-docs-metadata" not in stripped
        assert "# Title" in stripped
        assert "Content" in stripped
        assert stripped.endswith("\n")

    def test_no_metadata_returns_original(self) -> None:
        original = "# Title\n\nContent\n"
        assert strip_metadata(original) == original

    def test_preserves_content(self) -> None:
        block = serialize_metadata(document_id="x")
        markdown = f"Line 1\n\nLine 2\n\n{block}\n"
        stripped = strip_metadata(markdown)
        assert "Line 1" in stripped
        assert "Line 2" in stripped
