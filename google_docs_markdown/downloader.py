"""Downloader: orchestrates fetching a Google Doc and writing Markdown files.

Uses GoogleDocsClient to retrieve the Document, MarkdownSerializer to convert
each tab to Markdown, and writes the result as a directory of .md files.
"""

from __future__ import annotations

import re
from pathlib import Path

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.models.document import Document, Tab


class Downloader:
    """Download a Google Doc as Markdown files.

    Every document is treated as multi-tab: the output is a directory
    (named after the document title) containing one ``.md`` file per tab.
    Nested tabs produce nested directories.
    """

    def __init__(
        self,
        client: GoogleDocsClient | None = None,
        serializer: MarkdownSerializer | None = None,
    ) -> None:
        self._client = client or GoogleDocsClient()
        self._serializer = serializer or MarkdownSerializer()

    def download(
        self,
        document_id: str,
        *,
        tab_names: list[str] | None = None,
    ) -> dict[str, str]:
        """Download a document and return tab-name-to-markdown mapping.

        Args:
            document_id: Google Doc document ID or URL.
            tab_names: Optional list of tab titles to include. If None, all
                tabs are downloaded.

        Returns:
            Dict mapping tab path (e.g. ``"Tab 1"`` or
            ``"Parent Tab/Child Tab"``) to Markdown content.
        """
        doc = self._client.get_document(document_id)
        result: dict[str, str] = {}
        self._collect_tabs(doc.tabs or [], result, prefix="", tab_filter=tab_names)
        return result

    def download_to_files(
        self,
        document_id: str,
        output_dir: str | Path | None = None,
        *,
        tab_names: list[str] | None = None,
    ) -> dict[str, Path]:
        """Download a document and write Markdown files to disk.

        Args:
            document_id: Google Doc document ID or URL.
            output_dir: Root directory for output. If None, a directory named
                after the document title is created in the current directory.
            tab_names: Optional list of tab titles to include.

        Returns:
            Dict mapping tab path to the written file Path.
        """
        doc = self._client.get_document(document_id)

        if output_dir is None:
            title = doc.title or "Untitled Document"
            output_dir = Path(sanitize_filename(title))
        else:
            output_dir = Path(output_dir)

        tab_markdowns: dict[str, str] = {}
        self._collect_tabs(doc.tabs or [], tab_markdowns, prefix="", tab_filter=tab_names)

        written: dict[str, Path] = {}
        for tab_path, markdown in tab_markdowns.items():
            file_path = output_dir / f"{tab_path}.md"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(markdown, encoding="utf-8")
            written[tab_path] = file_path

        return written

    def _collect_tabs(
        self,
        tabs: list[Tab],
        result: dict[str, str],
        *,
        prefix: str,
        tab_filter: list[str] | None,
    ) -> None:
        """Recursively serialize tabs and populate *result*."""
        for tab in tabs:
            title = "Untitled"
            if tab.tabProperties and tab.tabProperties.title:
                title = tab.tabProperties.title

            tab_path = f"{prefix}/{title}" if prefix else title

            if tab.documentTab is not None:
                if tab_filter is None or title in tab_filter:
                    result[tab_path] = self._serializer.serialize(tab.documentTab)

            if tab.childTabs:
                self._collect_tabs(
                    tab.childTabs,
                    result,
                    prefix=tab_path,
                    tab_filter=tab_filter,
                )


_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str) -> str:
    """Replace characters that are unsafe for file/directory names.

    Strips leading/trailing whitespace and dots, replaces unsafe characters
    with underscores, and collapses runs of underscores.
    """
    name = name.strip().strip(".")
    name = _UNSAFE_CHARS.sub("_", name)
    name = re.sub(r"_+", "_", name)
    return name or "Untitled"
