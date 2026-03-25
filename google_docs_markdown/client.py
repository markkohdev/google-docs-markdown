"""
Google Docs Client

High-level client that composes the transport layer with Pydantic model
serialization/deserialization. This is the primary interface most consumers should use.
"""

from __future__ import annotations

from google.auth.credentials import Credentials

from google_docs_markdown.models import Document, Request, Response
from google_docs_markdown.transport import GoogleDocsTransport


class GoogleDocsClient:
    """
    High-level Google Docs client that returns typed Pydantic models.

    Wraps GoogleDocsTransport and handles conversion between raw API dicts and
    Pydantic models. For raw dict access (e.g. downloading test fixtures), use
    GoogleDocsTransport directly.
    """

    def __init__(
        self,
        transport: GoogleDocsTransport | None = None,
        *,
        credentials: Credentials | None = None,
    ):
        """
        Initialize the client.

        Args:
            transport: Optional pre-configured transport. If None, a new one is created.
            credentials: Optional credentials forwarded to the transport (ignored if
                        transport is provided).
        """
        self.transport = transport or GoogleDocsTransport(credentials=credentials)

    @staticmethod
    def extract_document_id(url_or_id: str) -> str:
        """Delegate to GoogleDocsTransport.extract_document_id."""
        return GoogleDocsTransport.extract_document_id(url_or_id)

    def get_document(self, document_id: str) -> Document:
        """
        Retrieve a document from Google Docs API as a Pydantic model.

        Args:
            document_id: The document ID or URL

        Returns:
            Document Pydantic model

        Raises:
            HttpError: If the API request fails
            ValueError: If document_id is invalid
        """
        raw = self.transport.get_document(document_id)
        return Document.model_validate(raw)

    def create_document(self, document: Document) -> Document:
        """
        Create a new blank document.

        Args:
            document: The document Pydantic model to create

        Returns:
            The newly created document as a Pydantic model
        """
        raw_input = document.model_dump(exclude_none=True)
        raw_result = self.transport.create_document(raw_input)  # type: ignore[arg-type]
        return Document.model_validate(raw_result)

    def batch_update(self, document_id: str, requests: list[Request]) -> list[Response]:
        """
        Execute a batch update on a document.

        Args:
            document_id: The document ID
            requests: List of Request Pydantic models for batchUpdate

        Returns:
            List of Response Pydantic models from the API
        """
        raw_requests = [r.model_dump(exclude_none=True) for r in requests]
        raw_responses = self.transport.batch_update(document_id, raw_requests)  # type: ignore[arg-type]
        return [Response.model_validate(r) for r in raw_responses]
