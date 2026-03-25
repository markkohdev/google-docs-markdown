"""
Tests for GoogleDocsClient.

Verifies that the typed client layer correctly wraps the transport and
produces Pydantic models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.models import Document, InsertTextRequest, Location, Request


def load_example_document_json() -> dict[str, Any]:
    """Load the example document JSON from test resources."""
    json_path = Path(__file__).parent / "resources" / "document_jsons" / "Markdown_Conversion_Example_-_Multi-Tab.json"
    with json_path.open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


class TestGetDocument:
    """Test typed document retrieval via GoogleDocsClient."""

    @patch("google_docs_markdown.transport.build")
    def test_get_document_returns_pydantic_model(self, mock_build: Any) -> None:
        """Test that get_document returns a Pydantic Document model."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "body": {}}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsClient(credentials=Mock())
        result = client.get_document("test-doc-id")

        assert isinstance(result, Document)
        assert result.title == "Test Doc"

    @patch("google_docs_markdown.transport.build")
    def test_get_document_with_real_api_response(self, mock_build: Any) -> None:
        """Test that real API response is correctly parsed into Pydantic models."""
        example_doc = load_example_document_json()
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = example_doc
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsClient(credentials=Mock())
        result = client.get_document(example_doc["documentId"])

        assert isinstance(result, Document)
        assert result.title == "Markdown Conversion Example - Multi-Tab"
        assert result.documentId == "1JSbV5QEuG9kkG2YCBajqhWWgzBkXGJwu4moRSEUSg3M"
        assert result.tabs is not None
        assert len(result.tabs) > 0

        # Validate tab structure
        first_tab = result.tabs[0]
        assert first_tab.tabProperties is not None
        assert first_tab.documentTab is not None
        assert first_tab.tabProperties.tabId == "t.0"
        assert first_tab.tabProperties.title == "First tab"

        # Validate document tab has body content
        assert first_tab.documentTab.body is not None
        assert first_tab.documentTab.body.content is not None

        # Validate includes multi-tab structure (nested tabs)
        assert len(result.tabs) > 1
        second_tab = result.tabs[1]
        assert second_tab.childTabs is not None
        assert len(second_tab.childTabs) > 0

    @patch("google_docs_markdown.transport.build")
    def test_get_document_real_response_structure_validation(self, mock_build: Any) -> None:
        """Validate that the client correctly parses complex real document structures."""
        example_doc = load_example_document_json()
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = example_doc
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsClient(credentials=Mock())
        result = client.get_document(example_doc["documentId"])

        # Validate document metadata
        assert result.title is not None
        assert result.documentId is not None
        assert result.suggestionsViewMode is not None

        # Validate tabs array exists and has expected structure
        assert result.tabs is not None
        assert isinstance(result.tabs, list)
        assert len(result.tabs) >= 1

        # Validate first tab has all expected fields
        first_tab = result.tabs[0]
        assert first_tab.tabProperties is not None
        assert first_tab.documentTab is not None

        tab_props = first_tab.tabProperties
        assert tab_props.tabId is not None
        assert tab_props.title is not None
        assert tab_props.index is not None

        doc_tab = first_tab.documentTab
        assert doc_tab.body is not None
        assert doc_tab.documentStyle is not None

        # Validate body content structure
        body = doc_tab.body
        assert body.content is not None
        assert isinstance(body.content, list)

        # Validate document style structure
        doc_style = doc_tab.documentStyle
        assert doc_style.pageSize is not None
        assert doc_style.marginTop is not None

        # Validate named styles exist
        assert doc_tab.namedStyles is not None
        assert doc_tab.namedStyles.styles is not None

        # Validate inline objects exist (for images)
        assert doc_tab.inlineObjects is not None

        # Validate lists exist
        assert doc_tab.lists is not None


class TestCreateDocument:
    """Test typed document creation via GoogleDocsClient."""

    @patch("google_docs_markdown.transport.build")
    def test_create_document(self, mock_build: Any) -> None:
        """Test creating a new document returns a Pydantic model."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"documentId": "new-doc-id", "title": "New Document"}
        mock_service.documents.return_value.create.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsClient(credentials=Mock())
        document_body = Document(title="New Document")
        result = client.create_document(document_body)

        assert isinstance(result, Document)
        assert result.documentId == "new-doc-id"
        assert result.title == "New Document"

        # Verify the transport was called with a dict (Pydantic model converted)
        call_args = mock_service.documents.return_value.create.call_args
        assert call_args is not None
        assert call_args.kwargs["body"]["title"] == "New Document"


class TestBatchUpdate:
    """Test typed batch update operations via GoogleDocsClient."""

    @patch("google_docs_markdown.transport.build")
    def test_batch_update(self, mock_build: Any) -> None:
        """Test batch update execution with Pydantic models."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"replies": []}
        mock_service.documents.return_value.batchUpdate.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsClient(credentials=Mock())
        location = Location(index=1)
        insert_request = InsertTextRequest(location=location, text="Hello")
        request = Request(insertText=insert_request)
        requests = [request]
        result = client.batch_update("test-doc-id", requests)

        assert isinstance(result, list)
        assert len(result) == 0

        # Verify the transport was called with dicts (Pydantic models converted)
        call_args = mock_service.documents.return_value.batchUpdate.call_args
        assert call_args is not None
        assert call_args.kwargs["documentId"] == "test-doc-id"
        assert "requests" in call_args.kwargs["body"]


class TestExtractDocumentId:
    """Test that extract_document_id is properly delegated."""

    def test_delegates_to_transport(self) -> None:
        """Test that extract_document_id delegates to the transport."""
        url = "https://docs.google.com/document/d/abc123def456/edit"
        assert GoogleDocsClient.extract_document_id(url) == "abc123def456"
