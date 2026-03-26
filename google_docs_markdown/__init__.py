"""
Google Docs Markdown - Tools for downloading and editing Google Docs as Markdown.

This package provides:
- Downloader: Orchestrates fetching a Google Doc and writing Markdown files
- MarkdownSerializer: Converts DocumentTab Pydantic models to Markdown text
- GoogleDocsClient: High-level client returning typed Pydantic models
- GoogleDocsTransport: Low-level transport returning raw API dicts
"""

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.downloader import Downloader
from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.transport import GoogleDocsTransport, TabInfo

__all__ = [
    "Downloader",
    "GoogleDocsClient",
    "GoogleDocsTransport",
    "MarkdownSerializer",
    "TabInfo",
]

__version__ = "0.2.0"
