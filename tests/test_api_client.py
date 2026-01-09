"""
Tests for Google Docs API Client.

Tests authentication, document retrieval, multi-tab detection, and error handling.
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.errors import HttpError

from google_docs_markdown.api_client import (
    MAX_RETRIES,
    SCOPES,
    GoogleDocsAPIClient,
    TabInfo,
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

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_include_tabs_false(self, mock_build: Any) -> None:
        """Test document retrieval without tabs content."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "body": {}}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        client.get_document("test-doc-id", include_tabs_content=False)

        mock_service.documents.return_value.get.assert_called_once_with(
            documentId="test-doc-id", includeTabsContent=False
        )


class TestMultiTabDetection:
    """Test multi-tab document detection."""

    @patch("google_docs_markdown.api_client.build")
    def test_is_multi_tab_true(self, mock_build: Any) -> None:
        """Test detection of multi-tab document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {
            "title": "Test Doc",
            "tabs": [{"tabId": "tab1", "name": "Tab 1"}, {"tabId": "tab2", "name": "Tab 2"}],
        }
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        assert client.is_multi_tab("test-doc-id") is True

    @patch("google_docs_markdown.api_client.build")
    def test_is_multi_tab_false(self, mock_build: Any) -> None:
        """Test detection of single-tab document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "tabs": []}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        assert client.is_multi_tab("test-doc-id") is False

    @patch("google_docs_markdown.api_client.build")
    def test_is_multi_tab_no_tabs_key(self, mock_build: Any) -> None:
        """Test detection when tabs key is missing."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc"}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        assert client.is_multi_tab("test-doc-id") is False

    @patch("google_docs_markdown.api_client.build")
    def test_get_tabs_multi_tab(self, mock_build: Any) -> None:
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
        tabs = client.get_tabs("test-doc-id")

        assert len(tabs) == 2
        assert tabs[0] == TabInfo(tab_id="tab1", name="Tab 1")
        assert tabs[1] == TabInfo(tab_id="tab2", name="Tab 2")

    @patch("google_docs_markdown.api_client.build")
    def test_get_tabs_single_tab(self, mock_build: Any) -> None:
        """Test getting tabs from single-tab document."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "Test Doc", "tabs": []}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        tabs = client.get_tabs("test-doc-id")

        assert len(tabs) == 0


class TestRetryLogic:
    """Test retry logic for transient failures."""

    @patch("google_docs_markdown.api_client.build")
    @patch("time.sleep")
    def test_retry_on_retryable_error(self, mock_sleep: Any, mock_build: Any) -> None:
        """Test retry on retryable HTTP error."""
        mock_service = Mock()
        mock_request = Mock()
        # First call fails with 500, second succeeds
        mock_request.execute.side_effect = [
            HttpError(Mock(status=500), b"Server Error"),
            {"title": "Test Doc"},
        ]
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        result = client.get_document("test-doc-id")

        assert result["title"] == "Test Doc"
        assert mock_request.execute.call_count == 2
        mock_sleep.assert_called_once()

    @patch("google_docs_markdown.api_client.build")
    @patch("time.sleep")
    def test_no_retry_on_non_retryable_error(self, mock_sleep: Any, mock_build: Any) -> None:
        """Test no retry on non-retryable HTTP error."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.side_effect = HttpError(Mock(status=404), b"Not Found")
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        with pytest.raises(HttpError):
            client.get_document("test-doc-id")

        assert mock_request.execute.call_count == 1
        mock_sleep.assert_not_called()

    @patch("google_docs_markdown.api_client.build")
    @patch("time.sleep")
    def test_max_retries_exceeded(self, mock_sleep: Any, mock_build: Any) -> None:
        """Test that max retries are respected."""
        mock_service = Mock()
        mock_request = Mock()
        # Always fail with retryable error
        mock_request.execute.side_effect = HttpError(Mock(status=500), b"Server Error")
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        with pytest.raises(HttpError):
            client.get_document("test-doc-id")

        assert mock_request.execute.call_count == MAX_RETRIES
        assert mock_sleep.call_count == MAX_RETRIES - 1


class TestDocumentTitle:
    """Test document title retrieval."""

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_title(self, mock_build: Any) -> None:
        """Test getting document title."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"title": "My Document"}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        title = client.get_document_title("test-doc-id")

        assert title == "My Document"

    @patch("google_docs_markdown.api_client.build")
    def test_get_document_title_missing(self, mock_build: Any) -> None:
        """Test getting title when title is missing."""
        mock_service = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {}
        mock_service.documents.return_value.get.return_value = mock_request
        mock_build.return_value = mock_service

        client = GoogleDocsAPIClient(credentials=Mock())
        title = client.get_document_title("test-doc-id")

        assert title == "Untitled Document"


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
        result = client.create_document("New Document")

        assert result["documentId"] == "new-doc-id"
        assert result["title"] == "New Document"
        mock_service.documents.return_value.create.assert_called_once_with(body={"title": "New Document"})


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

        assert "replies" in result
        mock_service.documents.return_value.batchUpdate.assert_called_once_with(
            documentId="test-doc-id", body={"requests": requests}
        )
