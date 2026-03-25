"""
Google Docs Markdown - Tools for downloading and editing Google Docs as Markdown.

This package provides:
- GoogleDocsClient: High-level client returning typed Pydantic models
- GoogleDocsTransport: Low-level transport returning raw API dicts
- Image extraction and inlining utilities for Markdown files
"""

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.transport import GoogleDocsTransport, TabInfo

__all__ = [
    "GoogleDocsClient",
    "GoogleDocsTransport",
    "TabInfo",
]

__version__ = "0.2.0"
