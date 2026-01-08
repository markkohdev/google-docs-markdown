"""
Google Docs Markdown - Tools for downloading and editing Google Docs as Markdown.

This package provides:
- GoogleDocMarkdown: Download and upload Google Docs as Markdown
- Image extraction and inlining utilities for Markdown files
"""

from google_docs_markdown.downloader import GoogleDocMarkdown
from google_docs_markdown.image_extractor import extract_images, inline_images

__all__ = [
    "GoogleDocMarkdown",
    "extract_images",
    "inline_images",
]

__version__ = "0.2.0"
