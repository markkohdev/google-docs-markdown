"""
Tests for Google Docs API Client.

Tests authentication, document retrieval, and error handling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import Mock, patch

import pytest
from google.auth.exceptions import DefaultCredentialsError

from google_docs_markdown.api_client import (
    SCOPES,
    GoogleDocsAPIClient,
)

if TYPE_CHECKING:
    from googleapiclient._apis.docs.v1 import Document, Request


def load_example_document_json() -> dict[str, Any]:
    """Load the example document JSON from test resources."""
    json_path = Path(__file__).parent / "resources" / "document_jsons" / "Markdown_Conversion_Example.json"
    with json_path.open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


class TestExtractDocumentID:
    """Test document ID extraction from URLs."""

    def test_extract_from_edit_url(self) -> None:
        """Test extraction from edit URL."""
        url = "https://docs.google.com/document/d/abc123def456/edit"
        assert GoogleDocsAPIClient.extract_document_id(url) == "abc123def456"

    def test_extract_from_view_url(self) -> None:
        """Test extraction from view URL."""
        url = "https://docs.google.com/document/d/abc123def456/view"
        assert GoogleDocsAPIClient.extract_document_id(url) == "abc123def456"

    def test_extract_from_bare_url(self) -> None:
        """Test extraction from URL without /edit or /view."""
        url = "https://docs.google.com/document/d/abc123def456"
        assert GoogleDocsAPIClient.extract_document_id(url) == "abc123def456"

    def test_extract_already_extracted_id(self) -> None:
        """Test that already extracted ID is returned as-is."""
        doc_id = "abc123def456"
        assert GoogleDocsAPIClient.extract_document_id(doc_id) == doc_id

    def test_extract_with_query_params(self) -> None:
        """Test extraction from URL with query parameters."""
        url = "https://docs.google.com/document/d/abc123def456/edit?usp=sharing"
        assert GoogleDocsAPIClient.extract_document_id(url) == "abc123def456"

    def test_extract_invalid_url(self) -> None:
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Could not extract document ID"):
            GoogleDocsAPIClient.extract_document_id("invalid")


class TestAuthentication:
    """Test authentication handling."""

    @patch("google.auth.default")
    def test_get_credentials_success(self, mock_default: Any) -> None:
        """Test successful credential retrieval."""
        mock_creds = Mock()
        mock_default.return_value = (mock_creds, None)

        client = GoogleDocsAPIClient()
        creds = client._get_credentials()

        assert creds == mock_creds
        mock_default.assert_called_once_with(scopes=SCOPES)

    @patch("google.auth.default")
    def test_get_credentials_failure(self, mock_default: Any) -> None:
        """Test credential retrieval failure."""
        mock_default.side_effect = DefaultCredentialsError("No credentials")

        client = GoogleDocsAPIClient()
        with pytest.raises(DefaultCredentialsError, match="Failed to obtain"):
            client._get_credentials()

    def test_custom_credentials(self) -> None:
        """Test using custom credentials."""
        mock_creds = Mock()
        client = GoogleDocsAPIClient(credentials=mock_creds)
        assert client.credentials == mock_creds


class TestGetDocument:
    """Test document retrieval."""

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_success(self, mock_build: Any) -> None:
        """Test successful document retrieval."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "body": {}}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        result = client.get_document("test-doc-id")

        assert result["title"] == "Test Doc"
        mock_service.documents.return_value.get.assert_called_once_with(
            documentId="test-doc-id", includeTabsContent=True
        )

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_with_url(self, mock_build: Any) -> None:
        """Test document retrieval with URL."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "body": {}}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        url = "https://docs.google.com/document/d/test-doc-id/edit"
        result = client.get_document(url)

        assert result["title"] == "Test Doc"
        # Should extract ID from URL
        mock_service.documents.return_value.get.assert_called_once_with(
            documentId="test-doc-id", includeTabsContent=True
        )

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_with_real_api_response(self, mock_build: Any) -> None:
        """Test document retrieval with real Google Docs API response structure."""
        example_doc = load_example_document_json()
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = example_doc
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        result = client.get_document(example_doc["documentId"])

        # Validate the response structure matches real API response
        assert result["title"] == "Markdown Conversion Example"
        assert result["documentId"] == "1JSbV5QEuG9kkG2YCBajqhWWgzBkXGJwu4moRSEUSg3M"
        assert "tabs" in result
        assert len(result["tabs"]) > 0

        # Validate tab structure
        first_tab = result["tabs"][0]
        assert "tabProperties" in first_tab
        assert "documentTab" in first_tab
        assert first_tab["tabProperties"]["tabId"] == "t.0"
        assert first_tab["tabProperties"]["title"] == "First tab"

        # Validate document tab has body content
        assert "body" in first_tab["documentTab"]
        assert "content" in first_tab["documentTab"]["body"]

        # Validate includes multi-tab structure (nested tabs)
        assert len(result["tabs"]) > 1
        second_tab = result["tabs"][1]
        assert "childTabs" in second_tab
        assert len(second_tab["childTabs"]) > 0

        mock_service.documents.return_value.get.assert_called_once_with(
            documentId=example_doc["documentId"], includeTabsContent=True
        )

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_real_response_structure_validation(self, mock_build: Any) -> None:
        """Validate that the API client correctly handles complex real document structures."""
        example_doc = load_example_document_json()
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = example_doc
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        result = client.get_document(example_doc["documentId"])

        # Validate document metadata
        assert "title" in result
        assert "documentId" in result
        assert "suggestionsViewMode" in result

        # Validate tabs array exists and has expected structure
        assert isinstance(result["tabs"], list)
        assert len(result["tabs"]) >= 1

        # Validate first tab has all expected fields
        first_tab = result["tabs"][0]
        assert "tabProperties" in first_tab
        assert "documentTab" in first_tab

        tab_props = first_tab["tabProperties"]
        assert "tabId" in tab_props
        assert "title" in tab_props
        assert "index" in tab_props

        doc_tab = first_tab["documentTab"]
        assert "body" in doc_tab
        assert "documentStyle" in doc_tab

        # Validate body content structure
        body = doc_tab["body"]
        assert "content" in body
        assert isinstance(body["content"], list)

        # Validate document style structure
        doc_style = doc_tab["documentStyle"]
        assert "pageSize" in doc_style
        assert "marginTop" in doc_style

        # Validate named styles exist
        assert "namedStyles" in doc_tab
        assert "styles" in doc_tab["namedStyles"]

        # Validate inline objects exist (for images)
        assert "inlineObjects" in doc_tab

        # Validate lists exist
        assert "lists" in doc_tab


class TestCreateDocument:
    """Test document creation."""

    @patch("google_docs_markdown.api_client.build")
    def test_create_document(self, mock_build: Any) -> None:
        """Test creating a new document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"documentId": "new-doc-id", "title": "New Document"}
        mock_service.documents.return_value.create.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        document_body: Document = cast("Document", {"title": "New Document"})
        result = client.create_document(document_body)

        assert result["documentId"] == "new-doc-id"
        assert result["title"] == "New Document"
        mock_service.documents.return_value.create.assert_called_once_with(body=document_body)


class TestBatchUpdate:
    """Test batch update operations."""

    @patch("google_docs_markdown.api_client.build")
    def test_batch_update(self, mock_build: Any) -> None:
        """Test batch update execution."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"replies": []}
        mock_service.documents.return_value.batchUpdate.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        requests: list[Request] = cast("list[Request]", [{"insertText": {"location": {"index": 1}, "text": "Hello"}}])
        result = client.batch_update("test-doc-id", requests)

        assert isinstance(result, list)
        assert len(result) == 0
        mock_service.documents.return_value.batchUpdate.assert_called_once_with(
            documentId="test-doc-id", body={"requests": requests}
        )
