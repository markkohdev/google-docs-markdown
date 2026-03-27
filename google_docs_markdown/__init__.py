"""
Google Docs Markdown - Tools for downloading and editing Google Docs as Markdown.

This package provides:
- Downloader: Orchestrates fetching a Google Doc and writing Markdown files
- Uploader: Orchestrates creating or updating Google Docs from Markdown
- MarkdownSerializer: Converts DocumentTab Pydantic models to Markdown text
- MarkdownDeserializer: Converts Markdown text to Google Docs API requests
- GoogleDocsClient: High-level client returning typed Pydantic models
- GoogleDocsTransport: Low-level transport returning raw API dicts
"""

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.downloader import (
    Downloader,
    FileConflictError,
    TabSummary,
    find_stale_files,
    remove_empty_dirs,
)
from google_docs_markdown.markdown_deserializer import MarkdownDeserializer
from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.transport import GoogleDocsTransport, TabInfo
from google_docs_markdown.uploader import Uploader

__all__ = [
    "Downloader",
    "FileConflictError",
    "GoogleDocsClient",
    "GoogleDocsTransport",
    "MarkdownDeserializer",
    "MarkdownSerializer",
    "TabInfo",
    "TabSummary",
    "Uploader",
    "find_stale_files",
    "remove_empty_dirs",
]

__version__ = "0.3.0"
