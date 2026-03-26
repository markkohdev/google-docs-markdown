"""Google Docs API Pydantic models."""

from google_docs_markdown.models import common as _common
from google_docs_markdown.models import document as _document
from google_docs_markdown.models import elements as _elements
from google_docs_markdown.models import requests as _requests
from google_docs_markdown.models import responses as _responses
from google_docs_markdown.models import styles as _styles
from google_docs_markdown.models.base import GoogleDocsBaseModel

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
from google_docs_markdown.models.requests import BatchUpdateDocumentRequest, InsertTextRequest, Request
from google_docs_markdown.models.responses import BatchUpdateDocumentResponse, Response

# Collect all model classes into a shared namespace for forward reference resolution
_namespace: dict[str, type] = {}
for _module in [_common, _styles, _elements, _document, _requests, _responses]:
    for _name in dir(_module):
        _obj = getattr(_module, _name)
        if isinstance(_obj, type) and issubclass(_obj, GoogleDocsBaseModel):
            _namespace[_name] = _obj

# Rebuild all models so Pydantic can resolve cross-module forward references
for _model_cls in _namespace.values():
    if hasattr(_model_cls, "model_rebuild"):
        _model_cls.model_rebuild(_types_namespace=_namespace)  # type: ignore[union-attr]

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
    "InsertTextRequest",
    # Common
    "Location",
    "Range",
    "Color",
    "Dimension",
]
