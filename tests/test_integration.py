"""Integration tests for end-to-end download.

These tests hit the live Google Docs API and require Application Default
Credentials to be configured.  Run with::

    pytest -m integration tests/test_integration.py

They are **skipped by default** in normal ``pytest`` runs (CI should use
``-m "not integration"``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from google_docs_markdown.downloader import Downloader

SINGLE_TAB_DOC_ID = "1JSbV5QEuG9kkG2YCBajqhWWgzBkXGJwu4moRSEUSg3M"
MULTI_TAB_DOC_ID = "1fLfF7Mx-Vt-ZZSYJ3ksfEIcH9gEV5Fnat4tPewazyug"

pytestmark = pytest.mark.integration


def _credentials_available() -> bool:
    """Return True when ADC are available."""
    try:
        import google.auth

        google.auth.default(scopes=["https://www.googleapis.com/auth/documents.readonly"])
        return True
    except Exception:
        return False


skip_no_creds = pytest.mark.skipif(
    not _credentials_available(),
    reason="Google Application Default Credentials not available",
)


@skip_no_creds
class TestSingleTabDownload:
    """End-to-end download of the single-tab example doc."""

    def test_download_returns_markdown(self) -> None:
        dl = Downloader()
        result = dl.download(SINGLE_TAB_DOC_ID)

        assert len(result) >= 1
        first_tab = next(iter(result.values()))
        assert "# " in first_tab
        assert len(first_tab) > 100

    def test_download_to_files(self, tmp_path: Path) -> None:
        dl = Downloader()
        written = dl.download_to_files(SINGLE_TAB_DOC_ID, output_dir=tmp_path)

        assert len(written) >= 1
        for _tab_path, file_path in written.items():
            assert file_path.exists()
            assert file_path.suffix == ".md"
            content = file_path.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_get_document_title(self) -> None:
        dl = Downloader()
        title = dl.get_document_title(SINGLE_TAB_DOC_ID)
        assert isinstance(title, str)
        assert len(title) > 0
        assert title != "Untitled Document"

    def test_get_tabs(self) -> None:
        dl = Downloader()
        tabs = dl.get_tabs(SINGLE_TAB_DOC_ID)
        assert len(tabs) >= 1
        for tab in tabs:
            assert tab.tab_id
            assert tab.title

    def test_deterministic_output(self) -> None:
        dl = Downloader()
        result1 = dl.download(SINGLE_TAB_DOC_ID)
        result2 = dl.download(SINGLE_TAB_DOC_ID)
        assert result1 == result2


@skip_no_creds
class TestMultiTabDownload:
    """End-to-end download of the multi-tab example doc.

    These tests adapt to the actual state of the live document.  If the
    document no longer has multiple tabs, some assertions are relaxed.
    """

    def test_download_returns_tabs(self) -> None:
        dl = Downloader()
        result = dl.download(MULTI_TAB_DOC_ID)

        assert len(result) >= 1
        for _tab_path, markdown in result.items():
            assert len(markdown) > 0

    def test_download_to_files(self, tmp_path: Path) -> None:
        dl = Downloader()
        written = dl.download_to_files(MULTI_TAB_DOC_ID, output_dir=tmp_path)

        assert len(written) >= 1
        for _tab_path, file_path in written.items():
            assert file_path.exists()
            assert file_path.suffix == ".md"

    def test_selective_tab_download(self) -> None:
        dl = Downloader()
        all_tabs = dl.get_tabs(MULTI_TAB_DOC_ID)
        assert len(all_tabs) >= 1

        first_title = all_tabs[0].title
        result = dl.download(MULTI_TAB_DOC_ID, tab_names=[first_title])
        assert len(result) == 1
        assert first_title in next(iter(result.keys()))

    def test_get_tabs_returns_structure(self) -> None:
        dl = Downloader()
        tabs = dl.get_tabs(MULTI_TAB_DOC_ID)

        assert len(tabs) >= 1
        for tab in tabs:
            assert tab.tab_id
            assert tab.title

    def test_get_nested_tabs_on_parent_with_children(self) -> None:
        """If any tab has children, verify get_nested_tabs returns them."""
        dl = Downloader()
        tabs = dl.get_tabs(MULTI_TAB_DOC_ID)

        parent = next((t for t in tabs if t.child_tabs), None)
        if parent is None:
            pytest.skip("Live document has no nested tabs — cannot test get_nested_tabs")

        children = dl.get_nested_tabs(MULTI_TAB_DOC_ID, parent.tab_id)
        assert len(children) >= 1
        assert children[0].title == parent.child_tabs[0].title

    def test_get_nested_tabs_on_leaf(self) -> None:
        """Calling get_nested_tabs on a leaf tab returns an empty list."""
        dl = Downloader()
        tabs = dl.get_tabs(MULTI_TAB_DOC_ID)
        assert len(tabs) >= 1

        leaf = tabs[0]
        while leaf.child_tabs:
            leaf = leaf.child_tabs[0]

        children = dl.get_nested_tabs(MULTI_TAB_DOC_ID, leaf.tab_id)
        assert children == []

    def test_deterministic_output(self) -> None:
        dl = Downloader()
        result1 = dl.download(MULTI_TAB_DOC_ID)
        result2 = dl.download(MULTI_TAB_DOC_ID)
        assert result1 == result2
