"""
Google Docs Markdown - Tools for downloading and editing Google Docs as Markdown.

This package provides:
- GoogleDocsAPIClient: Low-level API client for Google Docs
- GoogleDocMarkdown: Download and upload Google Docs as Markdown (coming soon)
- Image extraction and inlining utilities for Markdown files
"""

from google_docs_markdown.api_client import GoogleDocsAPIClient, TabInfo

__all__ = [
    "GoogleDocsAPIClient",
    "TabInfo",
]

__version__ = "0.2.0"
