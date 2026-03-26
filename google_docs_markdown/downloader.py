"""Downloader: orchestrates fetching a Google Doc and writing Markdown files.

Uses GoogleDocsClient to retrieve the Document, MarkdownSerializer to convert
each tab to Markdown, and writes the result as a directory of .md files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.markdown_serializer import MarkdownSerializer
from google_docs_markdown.models.document import Tab


class FileConflictError(Exception):
    """Raised when output files already exist and *overwrite* is ``False``."""

    def __init__(self, existing_paths: list[Path]) -> None:
        self.existing_paths = existing_paths
        paths_str = ", ".join(str(p) for p in existing_paths)
        super().__init__(f"{len(existing_paths)} file(s) already exist: {paths_str}")


@dataclass(frozen=True)
class TabSummary:
    """Lightweight summary of a document tab (no content)."""

    tab_id: str
    title: str
    nesting_level: int
    parent_tab_id: str | None
    child_tabs: list[TabSummary]


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
        overwrite: bool = True,
    ) -> dict[str, Path]:
        """Download a document and write Markdown files to disk.

        Args:
            document_id: Google Doc document ID or URL.
            output_dir: Parent directory for output. A subdirectory named after
                the document title is always created inside it. If None, the
                current directory is used as the parent.
            tab_names: Optional list of tab titles to include.
            overwrite: If ``False``, raise :class:`FileConflictError` when any
                target file already exists on disk.

        Returns:
            Dict mapping tab path to the written file Path.

        Raises:
            FileConflictError: If *overwrite* is ``False`` and one or more
                target files already exist.
        """
        doc = self._client.get_document(document_id)
        title = doc.title or "Untitled Document"
        doc_dir = sanitize_filename(title)

        if output_dir is None:
            output_dir = Path(doc_dir)
        else:
            output_dir = Path(output_dir) / doc_dir

        tab_markdowns: dict[str, str] = {}
        self._collect_tabs(doc.tabs or [], tab_markdowns, prefix="", tab_filter=tab_names)

        planned: dict[str, Path] = {}
        for tab_path in tab_markdowns:
            planned[tab_path] = output_dir / f"{tab_path}.md"

        if not overwrite:
            existing = [p for p in planned.values() if p.exists()]
            if existing:
                raise FileConflictError(existing)

        written: dict[str, Path] = {}
        for tab_path, markdown in tab_markdowns.items():
            file_path = planned[tab_path]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(markdown, encoding="utf-8")
            written[tab_path] = file_path

        return written

    def get_document_title(self, document_id: str) -> str:
        """Return the title of a Google Doc.

        Args:
            document_id: Google Doc document ID or URL.

        Returns:
            The document title, or ``"Untitled Document"`` if unset.
        """
        doc = self._client.get_document(document_id)
        return doc.title or "Untitled Document"

    def get_tabs(self, document_id: str) -> list[TabSummary]:
        """Return a flat-friendly tree of tab summaries for a document.

        Args:
            document_id: Google Doc document ID or URL.

        Returns:
            List of top-level :class:`TabSummary` objects. Each summary
            contains nested ``child_tabs`` for recursive traversal.
        """
        doc = self._client.get_document(document_id)
        return [_tab_to_summary(t) for t in (doc.tabs or [])]

    def get_nested_tabs(self, document_id: str, tab_id: str) -> list[TabSummary]:
        """Return the child tabs nested under a specific tab.

        Args:
            document_id: Google Doc document ID or URL.
            tab_id: The ``tabId`` of the parent tab whose children to return.

        Returns:
            List of :class:`TabSummary` for the immediate children.

        Raises:
            ValueError: If no tab with the given *tab_id* exists.
        """
        doc = self._client.get_document(document_id)
        target = _find_tab(doc.tabs or [], tab_id)
        if target is None:
            raise ValueError(f"No tab with tabId={tab_id!r} in document")
        return [_tab_to_summary(t) for t in (target.childTabs or [])]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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


def find_stale_files(
    output_dir: Path,
    current_files: set[Path],
) -> list[Path]:
    """Find ``.md`` files under *output_dir* that are not in *current_files*.

    Useful for detecting tab markdown files left over from a previous download
    after tabs have been removed from the upstream document.

    Args:
        output_dir: Root directory to scan recursively.
        current_files: Set of file paths that are still valid (just written).

    Returns:
        Sorted list of stale ``.md`` file paths.
    """
    if not output_dir.is_dir():
        return []
    resolved_current = {p.resolve() for p in current_files}
    return sorted(p for p in output_dir.rglob("*.md") if p.resolve() not in resolved_current)


def remove_empty_dirs(root: Path) -> None:
    """Remove empty directories under *root* (bottom-up), excluding *root*."""
    if not root.is_dir():
        return
    for dirpath in sorted(root.rglob("*"), reverse=True):
        if dirpath.is_dir() and not any(dirpath.iterdir()):
            dirpath.rmdir()


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


def _tab_to_summary(tab: Tab) -> TabSummary:
    """Convert a Pydantic ``Tab`` model to a lightweight ``TabSummary``."""
    props = tab.tabProperties
    return TabSummary(
        tab_id=(props.tabId or "") if props else "",
        title=(props.title or "Untitled") if props else "Untitled",
        nesting_level=(props.nestingLevel or 0) if props else 0,
        parent_tab_id=(props.parentTabId) if props else None,
        child_tabs=[_tab_to_summary(c) for c in (tab.childTabs or [])],
    )


def _find_tab(tabs: list[Tab], tab_id: str) -> Tab | None:
    """Recursively search for a tab by ``tabId``."""
    for tab in tabs:
        if tab.tabProperties and tab.tabProperties.tabId == tab_id:
            return tab
        if tab.childTabs:
            found = _find_tab(tab.childTabs, tab_id)
            if found is not None:
                return found
    return None
