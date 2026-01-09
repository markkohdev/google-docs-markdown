"""
Google Docs API Client

Handles authentication, API requests, and multi-tab document support.
"""

import re
import time
from dataclasses import dataclass
from typing import Any

from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest

# Google Docs API scope
SCOPES = ["https://www.googleapis.com/auth/documents"]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1
RETRYABLE_ERROR_CODES = [429, 500, 502, 503, 504]


@dataclass
class TabInfo:
    """Information about a document tab."""

    tab_id: str
    name: str


class GoogleDocsAPIClient:
    """
    Client for interacting with the Google Docs API.

    Handles authentication, API requests, retry logic, and multi-tab document support.
    """

    def __init__(self, credentials: Credentials | None = None):
        """
        Initialize the API client.

        Args:
            credentials: Optional pre-configured credentials. If None, uses
                        Application Default Credentials.
        """
        self.credentials = credentials
        self._service = None

    @property
    def service(self) -> Any:
        """Lazy-load the Google Docs API service."""
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def _build_service(self) -> Any:
        """Build and return the Google Docs API service."""
        if self.credentials is None:
            self.credentials = self._get_credentials()

        return build("docs", "v1", credentials=self.credentials)

    def _get_credentials(self) -> Credentials:
        """
        Get credentials using Application Default Credentials (ADC).

        Raises:
            DefaultCredentialsError: If credentials cannot be obtained.
        """
        try:
            from google.auth import default

            credentials, _ = default(scopes=SCOPES)
            return credentials
        except DefaultCredentialsError as e:
            raise DefaultCredentialsError(
                "Failed to obtain Application Default Credentials. "
                "Please run: gcloud auth application-default login "
                "--scopes=https://www.googleapis.com/auth/documents"
            ) from e

    @staticmethod
    def extract_document_id(url_or_id: str) -> str:
        """
        Extract document ID from a Google Docs URL or return the ID if already extracted.

        Supports various Google Docs URL formats:
        - https://docs.google.com/document/d/DOC_ID/edit
        - https://docs.google.com/document/d/DOC_ID/view
        - https://docs.google.com/document/d/DOC_ID
        - DOC_ID (already extracted)

        Args:
            url_or_id: Google Docs URL or document ID

        Returns:
            Document ID string

        Raises:
            ValueError: If document ID cannot be extracted from the URL
        """
        # Try to extract from URL patterns first
        patterns = [
            r"/document/d/([a-zA-Z0-9-_]+)",
            r"id=([a-zA-Z0-9-_]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        # If it's already just an ID (no slashes, no dots, looks like a doc ID)
        # Google Docs IDs are typically 44 characters, but can vary
        # They contain only alphanumeric, dashes, and underscores
        # For testing, we accept shorter IDs (10+ chars) that match the format
        if "/" not in url_or_id and "." not in url_or_id:
            # Validate it looks like a document ID (alphanumeric/dash/underscore)
            # Minimum 10 chars to avoid accepting generic strings, but allow test IDs
            if re.match(r"^[a-zA-Z0-9-_]{10,}$", url_or_id):
                return url_or_id

        raise ValueError(f"Could not extract document ID from: {url_or_id}. Expected a Google Docs URL or document ID.")

    def get_document(self, document_id: str, include_tabs_content: bool = True) -> dict[str, Any]:
        """
        Retrieve a document from Google Docs API.

        Args:
            document_id: The document ID
            include_tabs_content: If True, includes content from all tabs
                                 (required for multi-tab documents)

        Returns:
            Document dictionary from the API

        Raises:
            HttpError: If the API request fails
            ValueError: If document_id is invalid
        """
        document_id = self.extract_document_id(document_id)

        result = self._execute_with_retry(
            lambda: self.service.documents()
            .get(documentId=document_id, includeTabsContent=include_tabs_content)
            .execute()
        )
        assert isinstance(result, dict)
        return result

    def is_multi_tab(self, document_id: str) -> bool:
        """
        Check if a document has multiple tabs.

        Args:
            document_id: The document ID

        Returns:
            True if the document has multiple tabs, False otherwise
        """
        try:
            doc = self.get_document(document_id, include_tabs_content=True)
            tabs = doc.get("tabs", [])
            return len(tabs) > 0
        except Exception:
            # If we can't determine, assume single-tab
            return False

    def get_tabs(self, document_id: str) -> list[TabInfo]:
        """
        Get information about all tabs in a document.

        Args:
            document_id: The document ID

        Returns:
            List of TabInfo objects. Empty list for single-tab documents.
        """
        doc = self.get_document(document_id, include_tabs_content=True)
        tabs = doc.get("tabs", [])

        tab_info_list = []
        for tab in tabs:
            tab_info = TabInfo(tab_id=tab.get("tabId", ""), name=tab.get("name", "Untitled Tab"))
            tab_info_list.append(tab_info)

        return tab_info_list

    def get_document_title(self, document_id: str) -> str:
        """
        Get the title of a document.

        Args:
            document_id: The document ID

        Returns:
            Document title, or 'Untitled Document' if not found
        """
        doc = self.get_document(document_id, include_tabs_content=False)
        title = doc.get("title", "Untitled Document")
        assert isinstance(title, str)
        return title

    def create_document(self, title: str) -> dict[str, Any]:
        """
        Create a new blank document.

        Args:
            title: The title for the new document

        Returns:
            Created document dictionary with document ID
        """
        result = self._execute_with_retry(lambda: self.service.documents().create(body={"title": title}).execute())
        assert isinstance(result, dict)
        return result

    def batch_update(self, document_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Execute a batch update on a document.

        Args:
            document_id: The document ID
            requests: List of request dictionaries for batchUpdate

        Returns:
            Response dictionary from the API
        """
        document_id = self.extract_document_id(document_id)

        result = self._execute_with_retry(
            lambda: self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        )
        assert isinstance(result, dict)
        return result

    def _execute_with_retry(self, api_call: Any) -> Any:
        """
        Execute an API call with retry logic for transient failures.

        Args:
            api_call: Callable that returns an HttpRequest or executes an API call

        Returns:
            Result of the API call

        Raises:
            HttpError: If the API request fails after all retries
        """
        last_exception = None

        for attempt in range(MAX_RETRIES):
            try:
                result = api_call()
                # If it's an HttpRequest, execute it
                if isinstance(result, HttpRequest):
                    return result.execute()
                return result
            except HttpError as e:
                last_exception = e
                error_code = e.resp.status if e.resp else None

                # Check if error is retryable
                if error_code not in RETRYABLE_ERROR_CODES:
                    # Non-retryable error, raise immediately
                    raise

                # If this is the last attempt, raise the exception
                if attempt == MAX_RETRIES - 1:
                    raise

                # Wait before retrying (exponential backoff)
                delay = RETRY_DELAY_SECONDS * (2**attempt)
                time.sleep(delay)
            except Exception:
                # Non-HTTP errors are not retryable
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
