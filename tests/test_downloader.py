"""Tests for the Downloader.

Uses mocked GoogleDocsClient and real JSON fixtures to verify tab traversal,
directory/file creation, filename sanitization, and selective tab download.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from google_docs_markdown.downloader import Downloader, TabSummary, sanitize_filename
from google_docs_markdown.models import Document

RESOURCES_DIR = Path(__file__).parent / "resources" / "document_jsons"
SINGLE_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Single-Tab.json"
MULTI_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Multi-Tab.json"


def _load_raw(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def _mock_client(raw: dict[str, Any]) -> MagicMock:
    """Create a mocked GoogleDocsClient that returns a parsed Document."""
    client = MagicMock()
    client.get_document.return_value = Document.model_validate(raw)
    return client


# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    def test_clean_name(self) -> None:
        assert sanitize_filename("My Document") == "My Document"

    def test_strips_whitespace(self) -> None:
        assert sanitize_filename("  hello  ") == "hello"

    def test_replaces_slashes(self) -> None:
        assert sanitize_filename("a/b\\c") == "a_b_c"

    def test_replaces_colons(self) -> None:
        assert sanitize_filename("a:b") == "a_b"

    def test_replaces_special_chars(self) -> None:
        assert sanitize_filename('a<b>c"d|e?f*g') == "a_b_c_d_e_f_g"

    def test_collapses_underscores(self) -> None:
        assert sanitize_filename("a:::b") == "a_b"

    def test_strips_leading_dots(self) -> None:
        assert sanitize_filename("..hidden") == "hidden"

    def test_empty_fallback(self) -> None:
        assert sanitize_filename("") == "Untitled"
        assert sanitize_filename("...") == "Untitled"

    def test_null_bytes(self) -> None:
        assert sanitize_filename("a\x00b") == "a_b"


# ---------------------------------------------------------------------------
# Downloader.download (in-memory)
# ---------------------------------------------------------------------------


class TestDownloaderDownload:
    def test_single_tab(self) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)
        result = dl.download("fake-id")

        assert len(result) == 1
        assert "First tab" in result
        assert result["First tab"].startswith("# Markdown Conversion Example")

    def test_multi_tab_flat_and_nested(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        result = dl.download("fake-id")

        assert "First tab" in result
        assert "Tab with child tab" in result
        assert "Tab with child tab/Child tab" in result
        assert "Tab with child tab/Child tab/Grandchild tab" in result
        assert len(result) == 4

    def test_tab_filter(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        result = dl.download("fake-id", tab_names=["First tab"])

        assert "First tab" in result
        assert len(result) == 1

    def test_tab_filter_with_nested(self) -> None:
        """Filter applies to tab title, not path — nested tabs are still traversed."""
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        result = dl.download("fake-id", tab_names=["Grandchild tab"])

        assert "Tab with child tab/Child tab/Grandchild tab" in result
        assert len(result) == 1

    def test_content_of_nested_tab(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        result = dl.download("fake-id")

        assert "I am the content of the grandchild tab" in result["Tab with child tab/Child tab/Grandchild tab"]

    def test_client_called_with_id(self) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)
        dl.download("my-doc-id")
        client.get_document.assert_called_once_with("my-doc-id")


# ---------------------------------------------------------------------------
# Downloader.download_to_files (disk I/O)
# ---------------------------------------------------------------------------


class TestDownloaderDownloadToFiles:
    def test_creates_directory_from_title(self, tmp_path: Path) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id", output_dir=tmp_path)

        assert len(written) == 1
        assert "First tab" in written
        file_path = written["First tab"]
        assert file_path.exists()
        assert file_path.name == "First tab.md"
        assert file_path.parent == tmp_path / "Markdown Conversion Example - Single-Tab"

    def test_auto_names_from_title(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id")

        assert len(written) == 1
        file_path = written["First tab"]
        assert file_path.exists()
        assert file_path.parent.name == "Markdown Conversion Example - Single-Tab"

    def test_multi_tab_nested_dirs(self, tmp_path: Path) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id", output_dir=tmp_path / "out")
        root = tmp_path / "out" / "Markdown Conversion Example - Multi-Tab"

        assert (root / "First tab.md").exists()
        assert (root / "Tab with child tab.md").exists()
        assert (root / "Tab with child tab" / "Child tab.md").exists()
        assert (root / "Tab with child tab" / "Child tab" / "Grandchild tab.md").exists()
        assert len(written) == 4

    def test_file_content(self, tmp_path: Path) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id", output_dir=tmp_path)
        doc_root = tmp_path / "Markdown Conversion Example - Single-Tab"
        assert written["First tab"] == doc_root / "First tab.md"
        content = written["First tab"].read_text(encoding="utf-8")
        assert content.startswith("# Markdown Conversion Example - Single Tab")
        assert content.endswith("\n")

    def test_tab_filter_on_disk(self, tmp_path: Path) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id", output_dir=tmp_path, tab_names=["First tab"])
        doc_root = tmp_path / "Markdown Conversion Example - Multi-Tab"
        assert len(written) == 1
        assert (doc_root / "First tab.md").exists()

    def test_sanitizes_unsafe_title(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        raw = _load_raw(SINGLE_TAB_JSON)
        raw["title"] = 'My: "Special" Doc?'
        client = _mock_client(raw)
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id")
        file_path = list(written.values())[0]
        assert file_path.exists()
        assert file_path.parent.name == "My_ _Special_ Doc_"

    def test_untitled_document(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        raw = _load_raw(SINGLE_TAB_JSON)
        raw["title"] = None
        client = _mock_client(raw)
        dl = Downloader(client=client)

        written = dl.download_to_files("fake-id")
        file_path = list(written.values())[0]
        assert file_path.exists()
        assert file_path.parent.name == "Untitled Document"


# ---------------------------------------------------------------------------
# Downloader.get_document_title
# ---------------------------------------------------------------------------


class TestGetDocumentTitle:
    def test_returns_title(self) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)
        assert dl.get_document_title("fake-id") == "Markdown Conversion Example - Single-Tab"

    def test_returns_fallback_for_none(self) -> None:
        raw = _load_raw(SINGLE_TAB_JSON)
        raw["title"] = None
        client = _mock_client(raw)
        dl = Downloader(client=client)
        assert dl.get_document_title("fake-id") == "Untitled Document"


# ---------------------------------------------------------------------------
# Downloader.get_tabs
# ---------------------------------------------------------------------------


class TestGetTabs:
    def test_single_tab(self) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)
        tabs = dl.get_tabs("fake-id")

        assert len(tabs) == 1
        assert tabs[0].title == "First tab"
        assert tabs[0].tab_id == "t.0"
        assert tabs[0].child_tabs == []

    def test_multi_tab_structure(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        tabs = dl.get_tabs("fake-id")

        assert len(tabs) == 2
        assert tabs[0].title == "First tab"
        assert tabs[0].tab_id == "t.0"
        assert tabs[0].child_tabs == []

        assert tabs[1].title == "Tab with child tab"
        assert tabs[1].tab_id == "t.ytrmrxold3qv"
        assert len(tabs[1].child_tabs) == 1

        child = tabs[1].child_tabs[0]
        assert child.title == "Child tab"
        assert child.tab_id == "t.lkp7hl41vf2d"
        assert child.nesting_level == 1
        assert child.parent_tab_id == "t.ytrmrxold3qv"
        assert len(child.child_tabs) == 1

        grandchild = child.child_tabs[0]
        assert grandchild.title == "Grandchild tab"
        assert grandchild.nesting_level == 2
        assert grandchild.parent_tab_id == "t.lkp7hl41vf2d"
        assert grandchild.child_tabs == []

    def test_empty_tabs(self) -> None:
        raw = _load_raw(SINGLE_TAB_JSON)
        raw["tabs"] = []
        client = _mock_client(raw)
        dl = Downloader(client=client)
        assert dl.get_tabs("fake-id") == []

    def test_returns_tab_summary_type(self) -> None:
        client = _mock_client(_load_raw(SINGLE_TAB_JSON))
        dl = Downloader(client=client)
        tabs = dl.get_tabs("fake-id")
        assert isinstance(tabs[0], TabSummary)


# ---------------------------------------------------------------------------
# Downloader.get_nested_tabs
# ---------------------------------------------------------------------------


class TestGetNestedTabs:
    def test_returns_children(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        children = dl.get_nested_tabs("fake-id", "t.ytrmrxold3qv")

        assert len(children) == 1
        assert children[0].title == "Child tab"
        assert children[0].tab_id == "t.lkp7hl41vf2d"

    def test_returns_grandchildren(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        grandchildren = dl.get_nested_tabs("fake-id", "t.lkp7hl41vf2d")

        assert len(grandchildren) == 1
        assert grandchildren[0].title == "Grandchild tab"

    def test_leaf_tab_returns_empty(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        children = dl.get_nested_tabs("fake-id", "t.a2r49ovghki6")
        assert children == []

    def test_unknown_tab_id_raises(self) -> None:
        client = _mock_client(_load_raw(MULTI_TAB_JSON))
        dl = Downloader(client=client)
        with pytest.raises(ValueError, match="No tab with tabId"):
            dl.get_nested_tabs("fake-id", "nonexistent")
