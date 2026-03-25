"""Google Docs API Pydantic models."""

# Core document models
# Common models
from google_docs_markdown.models.common import (
    Color,
    Dimension,
    Location,
    Range,
)
from google_docs_markdown.models.document import Body, Document, DocumentTab, Tab, TabProperties

# Element models
from google_docs_markdown.models.elements import (
    Paragraph,
    ParagraphElement,
    StructuralElement,
    Table,
    TextRun,
)

# Request/Response models
from google_docs_markdown.models.requests import BatchUpdateDocumentRequest, Request
from google_docs_markdown.models.responses import BatchUpdateDocumentResponse, Response

__all__ = [
    # Document
    "Document",
    "DocumentTab",
    "Body",
    "Tab",
    "TabProperties",
    # Elements
    "StructuralElement",
    "Paragraph",
    "Table",
    "ParagraphElement",
    "TextRun",
    # Requests/Responses
    "Request",
    "Response",
    "BatchUpdateDocumentRequest",
    "BatchUpdateDocumentResponse",
    # Common
    "Location",
    "Range",
    "Color",
    "Dimension",
]
