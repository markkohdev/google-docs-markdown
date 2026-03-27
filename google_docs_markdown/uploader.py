"""Uploader: orchestrates creating or updating Google Docs from Markdown.

Uses ``MarkdownDeserializer`` to convert Markdown text into ``batchUpdate``
requests, and ``GoogleDocsClient`` to apply them.

Create flow (Phase 3.7):
    ``create_from_markdown`` — create a blank doc, populate via batchUpdate.
    ``create_from_directory`` — create a multi-tab doc from a directory of
    ``.md`` files.

Update flow (Phase 3.9):
    ``update_document`` — fetch current doc, serialize with source map, diff
    against local markdown, generate surgical batchUpdate requests.
    ``update_from_directory`` — per-tab updates for multi-tab documents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.markdown_deserializer import MarkdownDeserializer
from google_docs_markdown.models.document import Document, TabProperties
from google_docs_markdown.models.requests import (
    AddDocumentTabRequest,
    Request,
    UpdateDocumentTabPropertiesRequest,
)


class Uploader:
    """Upload Markdown as Google Docs (create or update).

    Every document is treated as multi-tab: even a single markdown file
    produces a single-tab document.
    """

    def __init__(
        self,
        client: GoogleDocsClient | None = None,
        deserializer: MarkdownDeserializer | None = None,
    ) -> None:
        self._client = client or GoogleDocsClient()
        self._deserializer = deserializer or MarkdownDeserializer()

    # ------------------------------------------------------------------
    # Create flow (Phase 3.7)
    # ------------------------------------------------------------------

    def create_from_markdown(
        self,
        title: str,
        markdown_text: str,
    ) -> str:
        """Create a new Google Doc from a single Markdown string.

        Creates a blank document via the API, then applies the deserialized
        ``batchUpdate`` requests to populate it.

        Args:
            title: The document title.
            markdown_text: Markdown source text for the document body.

        Returns:
            The ``documentId`` of the newly created document.
        """
        doc = self._client.create_document(Document(title=title))
        document_id = doc.documentId or ""

        requests = self._deserializer.deserialize(markdown_text)
        if requests:
            self._client.batch_update(document_id, requests)

        return document_id

    def create_from_directory(
        self,
        directory_path: str | Path,
        *,
        document_title: str | None = None,
    ) -> str:
        """Create a new multi-tab Google Doc from a directory of Markdown files.

        The directory name is used as the document title (unless
        *document_title* overrides it).  Each ``.md`` file becomes a tab
        (tab title = file stem).  Subdirectories produce nested tabs via
        ``addDocumentTab`` with ``parentTabId``.

        Files and subdirectories are sorted alphabetically to ensure
        deterministic tab ordering.

        Args:
            directory_path: Path to the directory containing ``.md`` files.
            document_title: Optional override for the document title.

        Returns:
            The ``documentId`` of the newly created document.

        Raises:
            FileNotFoundError: If *directory_path* does not exist.
            ValueError: If the directory contains no ``.md`` files and no
                subdirectories with ``.md`` files.
        """
        directory = Path(directory_path)
        if not directory.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")

        md_files = sorted(directory.glob("*.md"))
        subdirs = sorted(d for d in directory.iterdir() if d.is_dir())

        if not md_files and not subdirs:
            raise ValueError(f"No .md files or subdirectories found in: {directory}")

        title = document_title or directory.name
        doc = self._client.create_document(Document(title=title))
        document_id = doc.documentId or ""

        first_tab_id = _get_first_tab_id(doc)

        if md_files:
            self._populate_default_tab(document_id, first_tab_id, md_files[0])
            for md_file in md_files[1:]:
                self._add_tab_from_file(document_id, md_file)
        elif subdirs:
            self._rename_tab(document_id, first_tab_id, subdirs[0].name)

        for subdir in subdirs:
            self._add_tabs_from_subdir(document_id, subdir, parent_tab_id=None)

        return document_id

    # ------------------------------------------------------------------
    # Update flow (Phase 3.9)
    # ------------------------------------------------------------------

    def update_document(
        self,
        document_id: str,
        local_markdown: str,
        *,
        tab_id: str | None = None,
    ) -> bool:
        """Update an existing Google Doc with local Markdown changes.

        Pipeline: fetch doc → serialize with source map → diff against
        *local_markdown* → generate surgical ``batchUpdate`` requests.

        Args:
            document_id: The document ID or URL.
            local_markdown: The local Markdown content to push.
            tab_id: Optional tab ID to update (defaults to first tab).

        Returns:
            ``True`` if changes were applied, ``False`` if no changes detected.
        """
        from google_docs_markdown.diff_engine import DiffEngine
        from google_docs_markdown.markdown_serializer import MarkdownSerializer

        serializer = MarkdownSerializer()

        doc = self._client.get_document(document_id)
        target_tab = _find_target_tab(doc, tab_id)
        if target_tab is None:
            raise ValueError(f"No tab found with tab_id={tab_id!r}")

        resolved_tab_id = ""
        if target_tab.tabProperties and target_tab.tabProperties.tabId:
            resolved_tab_id = target_tab.tabProperties.tabId

        document_tab = target_tab.documentTab
        if document_tab is None:
            raise ValueError(f"Tab {resolved_tab_id!r} has no content")

        canonical_md, source_map = serializer.serialize_with_source_map(
            document_tab,
            document_id=doc.documentId,
            tab_id=resolved_tab_id,
        )

        engine = DiffEngine()
        requests = engine.compute_requests(
            canonical_md,
            local_markdown,
            source_map,
            tab_id=resolved_tab_id,
        )

        if not requests:
            return False

        self._client.batch_update(doc.documentId or document_id, requests)
        return True

    def update_from_directory(
        self,
        document_id: str,
        directory_path: str | Path,
    ) -> dict[str, bool]:
        """Update a multi-tab document from a directory of Markdown files.

        Each ``.md`` file is matched to a tab by name and updated
        independently.  Unchanged tabs are skipped.

        Args:
            document_id: The document ID or URL.
            directory_path: Path to the directory of Markdown files.

        Returns:
            Dict mapping tab path to whether changes were applied.
        """
        from google_docs_markdown.diff_engine import DiffEngine
        from google_docs_markdown.markdown_serializer import MarkdownSerializer

        directory = Path(directory_path)
        if not directory.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")

        serializer = MarkdownSerializer()
        doc = self._client.get_document(document_id)
        engine = DiffEngine()
        results: dict[str, bool] = {}

        tab_map = _build_tab_map(doc)

        for md_file in sorted(directory.rglob("*.md")):
            rel = md_file.relative_to(directory)
            tab_path = str(rel.with_suffix(""))

            tab = tab_map.get(tab_path)
            if tab is None:
                results[tab_path] = False
                continue

            resolved_tab_id = ""
            if tab.tabProperties and tab.tabProperties.tabId:
                resolved_tab_id = tab.tabProperties.tabId

            document_tab = tab.documentTab
            if document_tab is None:
                results[tab_path] = False
                continue

            canonical_md, source_map = serializer.serialize_with_source_map(
                document_tab,
                document_id=doc.documentId,
                tab_id=resolved_tab_id,
            )

            local_md = md_file.read_text(encoding="utf-8")
            requests = engine.compute_requests(
                canonical_md,
                local_md,
                source_map,
                tab_id=resolved_tab_id,
            )

            if requests:
                self._client.batch_update(doc.documentId or document_id, requests)
                results[tab_path] = True
            else:
                results[tab_path] = False

        return results

    # ------------------------------------------------------------------
    # Internal helpers — create flow
    # ------------------------------------------------------------------

    def _populate_default_tab(
        self,
        document_id: str,
        tab_id: str,
        md_file: Path,
    ) -> None:
        """Populate the default (first) tab and rename it to match the file."""
        markdown_text = md_file.read_text(encoding="utf-8")
        requests = self._deserializer.deserialize(markdown_text, tab_id=tab_id)

        rename_req = _rename_tab_request(tab_id, md_file.stem)
        all_requests = [rename_req] + requests
        if all_requests:
            self._client.batch_update(document_id, all_requests)

    def _rename_tab(self, document_id: str, tab_id: str, title: str) -> None:
        """Rename a tab."""
        self._client.batch_update(document_id, [_rename_tab_request(tab_id, title)])

    def _add_tab_from_file(
        self,
        document_id: str,
        md_file: Path,
        *,
        parent_tab_id: str | None = None,
    ) -> str:
        """Add a new tab from a Markdown file and return the new tab ID."""
        tab_title = md_file.stem

        add_req = Request(
            addDocumentTab=AddDocumentTabRequest(
                tabProperties=TabProperties(
                    title=tab_title,
                    parentTabId=parent_tab_id,
                ),
            )
        )
        responses = self._client.batch_update(document_id, [add_req])

        new_tab_id = ""
        if responses:
            resp = responses[0]
            if resp.addDocumentTab and resp.addDocumentTab.tabProperties:
                new_tab_id = resp.addDocumentTab.tabProperties.tabId or ""

        markdown_text = md_file.read_text(encoding="utf-8")
        requests = self._deserializer.deserialize(markdown_text, tab_id=new_tab_id)
        if requests:
            self._client.batch_update(document_id, requests)

        return new_tab_id

    def _add_tabs_from_subdir(
        self,
        document_id: str,
        subdir: Path,
        parent_tab_id: str | None,
    ) -> None:
        """Recursively add tabs from a subdirectory."""
        md_files = sorted(subdir.glob("*.md"))
        child_subdirs = sorted(d for d in subdir.iterdir() if d.is_dir())

        for md_file in md_files:
            self._add_tab_from_file(document_id, md_file, parent_tab_id=parent_tab_id)

        for child in child_subdirs:
            add_req = Request(
                addDocumentTab=AddDocumentTabRequest(
                    tabProperties=TabProperties(
                        title=child.name,
                        parentTabId=parent_tab_id,
                    ),
                )
            )
            responses = self._client.batch_update(document_id, [add_req])
            new_parent_id = ""
            if responses:
                resp = responses[0]
                if resp.addDocumentTab and resp.addDocumentTab.tabProperties:
                    new_parent_id = resp.addDocumentTab.tabProperties.tabId or ""

            self._add_tabs_from_subdir(document_id, child, parent_tab_id=new_parent_id)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _get_first_tab_id(doc: Document) -> str:
    """Extract the tab ID of the first tab in a document."""
    if doc.tabs:
        first = doc.tabs[0]
        if first.tabProperties and first.tabProperties.tabId:
            return first.tabProperties.tabId
    return ""


def _rename_tab_request(tab_id: str, title: str) -> Request:
    """Build an ``UpdateDocumentTabPropertiesRequest`` to rename a tab."""
    return Request(
        updateDocumentTabProperties=UpdateDocumentTabPropertiesRequest(
            tabProperties=TabProperties(tabId=tab_id, title=title),
            fields="title",
        )
    )


def _find_target_tab(doc: Document, tab_id: str | None) -> Any:
    """Find a tab by ID, defaulting to the first tab.

    Returns a ``Tab`` model or ``None``.
    """
    if not doc.tabs:
        return None

    if tab_id is None:
        return doc.tabs[0]

    from google_docs_markdown.models.document import Tab

    def _search(tabs: list[Tab]) -> Tab | None:
        for tab in tabs:
            if tab.tabProperties and tab.tabProperties.tabId == tab_id:
                return tab
            if tab.childTabs:
                found = _search(tab.childTabs)
                if found is not None:
                    return found
        return None

    return _search(doc.tabs)


def _build_tab_map(doc: Document) -> dict[str, Any]:
    """Build a mapping from tab path (e.g. ``Parent/Child``) to ``Tab`` model."""
    from google_docs_markdown.models.document import Tab

    result: dict[str, Tab] = {}

    def _walk(tabs: list[Tab], prefix: str) -> None:
        for tab in tabs:
            title = "Untitled"
            if tab.tabProperties:
                title = tab.tabProperties.title or "Untitled"
            path = f"{prefix}/{title}" if prefix else title
            result[path] = tab
            if tab.childTabs:
                _walk(tab.childTabs, path)

    _walk(doc.tabs or [], "")
    return result
