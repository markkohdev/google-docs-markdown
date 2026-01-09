"""
Tests for Google Docs API Client.

Tests authentication, document retrieval, and error handling.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.errors import HttpError

from google_docs_markdown.api_client import (
    MAX_RETRIES,
    SCOPES,
    GoogleDocsAPIClient,
)


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


class TestGetTabs:
    """Test tab retrieval from document."""

    @patch("google_docs_markdown.api_client.build")
    def test_get_tabs_from_document(self, mock_build: Any) -> None:
        """Test getting tabs from multi-tab document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {
            "title": "Test Doc",
            "tabs": [{"tabId": "tab1", "name": "Tab 1"}, {"tabId": "tab2", "name": "Tab 2"}],
        }
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        doc = client.get_document("test-doc-id")

        assert "tabs" in doc
        assert len(doc["tabs"]) == 2
        assert doc["tabs"][0]["tabId"] == "tab1"
        assert doc["tabs"][0]["name"] == "Tab 1"

    @patch("google_docs_markdown.api_client.build")
    def test_get_tabs_single_tab(self, mock_build: Any) -> None:
        """Test getting tabs from single-tab document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "tabs": []}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        doc = client.get_document("test-doc-id")

        assert "tabs" in doc
        assert len(doc.get("tabs", [])) == 0


class TestRetryLogic:
    """Test retry logic for transient failures.

    Note: Retries are now handled by the Google API client library via num_retries parameter.
    These tests verify that num_retries is passed correctly.
    """

    @patch("google_docs_markdown.api_client.build")
    def test_retry_parameter_passed(self, mock_build: Any) -> None:
        """Test that num_retries parameter is passed to execute()."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc"}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        result = client.get_document("test-doc-id")

        assert result["title"] == "Test Doc"
        # Verify that execute was called with num_retries
        mock_request.execute.assert_called_once_with(num_retries=MAX_RETRIES)

    @patch("google_docs_markdown.api_client.build")
    def test_no_retry_on_non_retryable_error(self, mock_build: Any) -> None:
        """Test that non-retryable errors are not retried by the library."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.side_effect = HttpError(Mock(status=404), b"Not Found")
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        with pytest.raises(HttpError):
            client.get_document("test-doc-id")

        # The library will still attempt retries, but 404 is not retryable
        # So it should fail immediately after the retry logic determines it's not retryable
        mock_request.execute.assert_called_with(num_retries=MAX_RETRIES)


class TestDocumentTitle:
    """Test document title retrieval from document."""

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_title(self, mock_build: Any) -> None:
        """Test getting document title from document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "My Document"}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        doc = client.get_document("test-doc-id")

        assert doc["title"] == "My Document"

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_title_missing(self, mock_build: Any) -> None:
        """Test getting title when title is missing."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        doc = client.get_document("test-doc-id")

        # Title may be missing or empty
        assert "title" not in doc or doc.get("title") == ""


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
        document_body = {"title": "New Document"}
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
        requests = [{"insertText": {"location": {"index": 1}, "text": "Hello"}}]
        result = client.batch_update("test-doc-id", requests)

        assert isinstance(result, list)
        assert len(result) == 0
        mock_service.documents.return_value.batchUpdate.assert_called_once_with(
            documentId="test-doc-id", body={"requests": requests}
        )
