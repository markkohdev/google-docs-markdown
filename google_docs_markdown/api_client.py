"""
Google Docs API Client

Handles authentication, API requests, and basic calls to the Google Docs API.
"""

from __future__ import annotations

import re
import typing
from dataclasses import dataclass

from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.discovery import build

# Google API python clients are very weirdly typed so we need to use stubs to get the correct types
# since these aren't "real" types, we need to use TYPE_CHECKING to get the correct types
# see https://pypi.org/project/google-api-python-client-stubs/ for more info
# and make sure you always have `from __future__ import annotations` at the top of the file!
if typing.TYPE_CHECKING:
    from googleapiclient._apis.docs.v1 import DocsResource, Document, Request, Response


# Google Docs API scope
SCOPES = ["https://www.googleapis.com/auth/documents"]

# Retry configuration
MAX_RETRIES = 3


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
    def service(self) -> DocsResource:
        """Lazy-load the Google Docs API service."""
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def _build_service(self) -> DocsResource:
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
        - https://docs.google.com/document/d/DOC_ID/edit?pli=1&tab=TAB_ID (will still only extract the DOC_ID)
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

    def get_document(self, document_id: str) -> Document:
        """
        Retrieve a document from Google Docs API.

        Always includes content from all tabs, treating every document as a multi-tab document
        (even if it only has a single tab).

        Args:
            document_id: The document ID

        Returns:
            Document object from the API

        Raises:
            HttpError: If the API request fails
            ValueError: If document_id is invalid
        """
        document_id = self.extract_document_id(document_id)

        result = (
            self.service.documents()
            .get(documentId=document_id, includeTabsContent=True)
            .execute(num_retries=MAX_RETRIES)
        )
        return result

    def create_document(self, document: Document) -> Document:
        """
        Create a new blank document.

        Args:
            document: The document to create

        Returns:
            The newly created document
        """
        result = self.service.documents().create(body=document).execute(num_retries=MAX_RETRIES)
        return result

    def batch_update(self, document_id: str, requests: list[Request]) -> list[Response]:
        """
        Execute a batch update on a document.

        Args:
            document_id: The document ID
            requests: List of Request objects for batchUpdate

        Returns:
            List of responses from the API
        """
        document_id = self.extract_document_id(document_id)

        result = (
            self.service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute(num_retries=MAX_RETRIES)
        )

        # result is a BatchUpdateDocumentResponse TypedDict
        response_list = result.get("replies", [])
        return response_list
