"""Tests for the Uploader (create flow — Phase 3.7)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from google_docs_markdown.client import GoogleDocsClient
from google_docs_markdown.markdown_deserializer import MarkdownDeserializer
from google_docs_markdown.models.document import Document, Tab, TabProperties
from google_docs_markdown.models.requests import Request
from google_docs_markdown.models.responses import AddDocumentTabResponse, Response
from google_docs_markdown.uploader import Uploader, _build_tab_map, _find_target_tab, _get_first_tab_id


def _mock_client(document_id: str = "new-doc-id", first_tab_id: str = "t.0") -> Mock:
    """Create a mock GoogleDocsClient for testing."""
    client = Mock(spec=GoogleDocsClient)
    client.create_document.return_value = Document(
        documentId=document_id,
        title="Test Doc",
        tabs=[
            Tab(
                tabProperties=TabProperties(tabId=first_tab_id, title="Tab 1"),
            )
        ],
    )
    client.batch_update.return_value = []
    return client


class TestCreateFromMarkdown:
    def test_creates_document_with_title(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        doc_id = uploader.create_from_markdown("My Title", "# Hello\n")

        assert doc_id == "new-doc-id"
        client.create_document.assert_called_once()
        created_doc = client.create_document.call_args[0][0]
        assert isinstance(created_doc, Document)
        assert created_doc.title == "My Title"

    def test_applies_deserialized_requests(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        uploader.create_from_markdown("Test", "# Heading\n\nParagraph text.\n")

        assert client.batch_update.called
        call_args = client.batch_update.call_args
        assert call_args[0][0] == "new-doc-id"
        requests = call_args[0][1]
        assert len(requests) > 0
        assert all(isinstance(r, Request) for r in requests)

    def test_empty_markdown_no_batch_update(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        doc_id = uploader.create_from_markdown("Empty", "")

        assert doc_id == "new-doc-id"
        client.create_document.assert_called_once()
        client.batch_update.assert_not_called()

    def test_whitespace_only_no_batch_update(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        doc_id = uploader.create_from_markdown("Blank", "   \n\n   \n")

        assert doc_id == "new-doc-id"
        client.batch_update.assert_not_called()

    def test_heading_and_paragraph(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        uploader.create_from_markdown("Test", "# Heading 1\n\nSome text here.\n")

        requests = client.batch_update.call_args[0][1]
        insert_texts = [r for r in requests if r.insertText is not None]
        assert len(insert_texts) >= 2

    def test_bold_formatting(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        uploader.create_from_markdown("Test", "This is **bold** text.\n")

        requests = client.batch_update.call_args[0][1]
        style_updates = [r for r in requests if r.updateTextStyle is not None]
        assert len(style_updates) >= 1
        bold_req = style_updates[0]
        assert bold_req.updateTextStyle is not None
        assert bold_req.updateTextStyle.textStyle is not None
        assert bold_req.updateTextStyle.textStyle.bold is True

    def test_uses_custom_deserializer(self) -> None:
        from google_docs_markdown.models.common import Location
        from google_docs_markdown.models.requests import InsertTextRequest

        client = _mock_client()
        deser = Mock(spec=MarkdownDeserializer)
        deser.deserialize.return_value = [
            Request(insertText=InsertTextRequest(text="custom", location=Location(index=1)))
        ]
        uploader = Uploader(client=client, deserializer=deser)

        uploader.create_from_markdown("Test", "custom content")

        deser.deserialize.assert_called_once_with("custom content")
        assert client.batch_update.called


class TestCreateFromDirectory:
    def test_single_file_directory(self, tmp_path: Path) -> None:
        md_dir = tmp_path / "My Document"
        md_dir.mkdir()
        (md_dir / "First tab.md").write_text("# Hello\n", encoding="utf-8")

        client = _mock_client()
        uploader = Uploader(client=client)

        doc_id = uploader.create_from_directory(md_dir)

        assert doc_id == "new-doc-id"
        client.create_document.assert_called_once()
        created_doc = client.create_document.call_args[0][0]
        assert created_doc.title == "My Document"
        assert client.batch_update.called

    def test_multiple_files_creates_additional_tabs(self, tmp_path: Path) -> None:
        md_dir = tmp_path / "Multi Tab Doc"
        md_dir.mkdir()
        (md_dir / "Alpha.md").write_text("# Alpha\n", encoding="utf-8")
        (md_dir / "Beta.md").write_text("# Beta\n", encoding="utf-8")

        client = _mock_client()
        client.batch_update.return_value = [
            Response(addDocumentTab=AddDocumentTabResponse(tabProperties=TabProperties(tabId="t.new", title="Beta")))
        ]
        uploader = Uploader(client=client)

        doc_id = uploader.create_from_directory(md_dir)

        assert doc_id == "new-doc-id"
        batch_calls = client.batch_update.call_args_list
        assert len(batch_calls) >= 2

    def test_custom_title_overrides_directory_name(self, tmp_path: Path) -> None:
        md_dir = tmp_path / "dirname"
        md_dir.mkdir()
        (md_dir / "Tab.md").write_text("text\n", encoding="utf-8")

        client = _mock_client()
        uploader = Uploader(client=client)

        uploader.create_from_directory(md_dir, document_title="Custom Title")

        created_doc = client.create_document.call_args[0][0]
        assert created_doc.title == "Custom Title"

    def test_nonexistent_directory_raises(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)

        with pytest.raises(FileNotFoundError, match="Directory not found"):
            uploader.create_from_directory("/nonexistent/path")

    def test_empty_directory_raises(self, tmp_path: Path) -> None:
        md_dir = tmp_path / "empty"
        md_dir.mkdir()

        client = _mock_client()
        uploader = Uploader(client=client)

        with pytest.raises(ValueError, match="No .md files"):
            uploader.create_from_directory(md_dir)

    def test_subdirectory_creates_nested_tabs(self, tmp_path: Path) -> None:
        md_dir = tmp_path / "Doc"
        md_dir.mkdir()
        (md_dir / "Main.md").write_text("# Main\n", encoding="utf-8")

        sub = md_dir / "nested"
        sub.mkdir()
        (sub / "Child.md").write_text("# Child\n", encoding="utf-8")

        client = _mock_client()
        call_count = 0

        def mock_batch_update(doc_id: str, requests: list[Request]) -> list[Response]:
            nonlocal call_count
            call_count += 1
            for r in requests:
                if r.addDocumentTab is not None:
                    return [
                        Response(
                            addDocumentTab=AddDocumentTabResponse(
                                tabProperties=TabProperties(
                                    tabId=f"t.new.{call_count}",
                                    title="nested",
                                )
                            )
                        )
                    ]
            return []

        client.batch_update.side_effect = mock_batch_update
        uploader = Uploader(client=client)

        doc_id = uploader.create_from_directory(md_dir)

        assert doc_id == "new-doc-id"
        assert client.batch_update.call_count >= 2

    def test_paired_file_and_directory_same_tab(self, tmp_path: Path) -> None:
        """When X.md and X/ both exist, they should produce one tab with children, not two."""
        md_dir = tmp_path / "Doc"
        md_dir.mkdir()
        (md_dir / "Tab A.md").write_text("# Tab A\n", encoding="utf-8")
        (md_dir / "Parent.md").write_text("# Parent\n", encoding="utf-8")
        sub = md_dir / "Parent"
        sub.mkdir()
        (sub / "Child.md").write_text("# Child\n", encoding="utf-8")

        client = _mock_client()
        call_count = 0

        def mock_batch_update(doc_id: str, requests: list[Request]) -> list[Response]:
            nonlocal call_count
            call_count += 1
            for r in requests:
                if r.addDocumentTab is not None:
                    title = ""
                    if r.addDocumentTab.tabProperties:
                        title = r.addDocumentTab.tabProperties.title or ""
                    return [
                        Response(
                            addDocumentTab=AddDocumentTabResponse(
                                tabProperties=TabProperties(
                                    tabId=f"t.{call_count}",
                                    title=title,
                                )
                            )
                        )
                    ]
            return []

        client.batch_update.side_effect = mock_batch_update
        uploader = Uploader(client=client)

        uploader.create_from_directory(md_dir)

        add_tab_reqs: list[tuple[str, str | None]] = []
        for call in client.batch_update.call_args_list:
            for req in call[0][1]:
                if req.addDocumentTab and req.addDocumentTab.tabProperties:
                    props = req.addDocumentTab.tabProperties
                    add_tab_reqs.append((props.title or "", props.parentTabId))

        titles = [t for t, _ in add_tab_reqs]
        assert "Parent" not in titles, "Parent should use default tab (rename), not addDocumentTab"
        assert "Child" in titles, "Child should be created via addDocumentTab"

        child_entry = next(e for e in add_tab_reqs if e[0] == "Child")
        assert child_entry[1] == "t.0", "Child should be nested under the default tab (Parent)"

    def test_files_sorted_alphabetically(self, tmp_path: Path) -> None:
        md_dir = tmp_path / "Sorted"
        md_dir.mkdir()
        (md_dir / "Zebra.md").write_text("z\n", encoding="utf-8")
        (md_dir / "Alpha.md").write_text("a\n", encoding="utf-8")
        (md_dir / "Middle.md").write_text("m\n", encoding="utf-8")

        client = _mock_client()
        client.batch_update.return_value = [
            Response(addDocumentTab=AddDocumentTabResponse(tabProperties=TabProperties(tabId="t.x")))
        ]
        uploader = Uploader(client=client)

        uploader.create_from_directory(md_dir)

        first_batch = client.batch_update.call_args_list[0]
        rename_req = first_batch[0][1][0]
        assert rename_req.updateDocumentTabProperties is not None
        tab_props = rename_req.updateDocumentTabProperties.tabProperties
        assert tab_props is not None
        assert tab_props.title == "Alpha"


class TestGetFirstTabId:
    def test_returns_tab_id(self) -> None:
        doc = Document(tabs=[Tab(tabProperties=TabProperties(tabId="t.123"))])
        assert _get_first_tab_id(doc) == "t.123"

    def test_no_tabs_returns_empty(self) -> None:
        doc = Document(tabs=[])
        assert _get_first_tab_id(doc) == ""

    def test_no_tab_properties_returns_empty(self) -> None:
        doc = Document(tabs=[Tab()])
        assert _get_first_tab_id(doc) == ""


class TestFindTargetTab:
    def test_none_tab_id_returns_first(self) -> None:
        tab = Tab(tabProperties=TabProperties(tabId="t.0", title="First"))
        doc = Document(tabs=[tab])
        assert _find_target_tab(doc, None) is tab

    def test_finds_by_tab_id(self) -> None:
        tab1 = Tab(tabProperties=TabProperties(tabId="t.0", title="First"))
        tab2 = Tab(tabProperties=TabProperties(tabId="t.1", title="Second"))
        doc = Document(tabs=[tab1, tab2])
        assert _find_target_tab(doc, "t.1") is tab2

    def test_finds_nested_tab(self) -> None:
        child = Tab(tabProperties=TabProperties(tabId="t.child", title="Child"))
        parent = Tab(
            tabProperties=TabProperties(tabId="t.parent", title="Parent"),
            childTabs=[child],
        )
        doc = Document(tabs=[parent])
        assert _find_target_tab(doc, "t.child") is child

    def test_not_found_returns_none(self) -> None:
        doc = Document(tabs=[Tab(tabProperties=TabProperties(tabId="t.0"))])
        assert _find_target_tab(doc, "t.missing") is None

    def test_no_tabs_returns_none(self) -> None:
        doc = Document(tabs=[])
        assert _find_target_tab(doc, None) is None


class TestBuildTabMap:
    def test_simple_tabs(self) -> None:
        t1 = Tab(tabProperties=TabProperties(tabId="t.0", title="Tab A"))
        t2 = Tab(tabProperties=TabProperties(tabId="t.1", title="Tab B"))
        doc = Document(tabs=[t1, t2])
        tab_map = _build_tab_map(doc)
        assert "Tab A" in tab_map
        assert "Tab B" in tab_map
        assert tab_map["Tab A"] is t1

    def test_nested_tabs(self) -> None:
        child = Tab(tabProperties=TabProperties(tabId="t.c", title="Child"))
        parent = Tab(
            tabProperties=TabProperties(tabId="t.p", title="Parent"),
            childTabs=[child],
        )
        doc = Document(tabs=[parent])
        tab_map = _build_tab_map(doc)
        assert "Parent" in tab_map
        assert "Parent/Child" in tab_map

    def test_empty_tabs(self) -> None:
        doc = Document(tabs=[])
        assert _build_tab_map(doc) == {}


# ------------------------------------------------------------------
# Update flow tests (Phase 3.9)
# ------------------------------------------------------------------


def _doc_with_content(
    text: str = "Hello world\n",
    tab_id: str = "t.0",
    document_id: str = "doc-123",
) -> Document:
    """Create a Document with a single tab containing a simple paragraph."""
    from google_docs_markdown.models.document import Body, DocumentTab, NamedStyle, NamedStyles
    from google_docs_markdown.models.elements import (
        Paragraph,
        ParagraphElement,
        SectionBreak,
        StructuralElement,
        TextRun,
    )
    from google_docs_markdown.models.styles import ParagraphStyle, TextStyle

    return Document(
        documentId=document_id,
        title="Test Doc",
        tabs=[
            Tab(
                tabProperties=TabProperties(tabId=tab_id, title="Main"),
                documentTab=DocumentTab(
                    body=Body(
                        content=[
                            StructuralElement(
                                startIndex=0,
                                endIndex=1,
                                sectionBreak=SectionBreak(),
                            ),
                            StructuralElement(
                                startIndex=1,
                                endIndex=1 + len(text),
                                paragraph=Paragraph(
                                    elements=[
                                        ParagraphElement(
                                            startIndex=1,
                                            endIndex=1 + len(text),
                                            textRun=TextRun(
                                                content=text,
                                                textStyle=TextStyle(),
                                            ),
                                        )
                                    ],
                                    paragraphStyle=ParagraphStyle(namedStyleType="NORMAL_TEXT"),
                                ),
                            ),
                        ]
                    ),
                    namedStyles=NamedStyles(
                        styles=[
                            NamedStyle(
                                namedStyleType="NORMAL_TEXT",
                                textStyle=TextStyle(),
                            )
                        ]
                    ),
                ),
            )
        ],
    )


class TestUpdateDocument:
    def test_no_changes_returns_false(self) -> None:
        doc = _doc_with_content("Hello\n")
        client = _mock_client()
        client.get_document.return_value = doc

        uploader = Uploader(client=client)

        from google_docs_markdown.markdown_serializer import MarkdownSerializer

        serializer = MarkdownSerializer()
        assert doc.tabs is not None
        canonical = serializer.serialize(
            doc.tabs[0].documentTab,  # type: ignore[arg-type]
            document_id="doc-123",
            tab_id="t.0",
        )

        result = uploader.update_document("doc-123", canonical)
        assert result is False
        client.batch_update.assert_not_called()

    def test_with_changes_returns_true(self) -> None:
        doc = _doc_with_content("Hello\n")
        client = _mock_client()
        client.get_document.return_value = doc
        client.batch_update.return_value = []

        uploader = Uploader(client=client)
        result = uploader.update_document("doc-123", "Completely different content\n")
        assert result is True
        assert client.batch_update.called

    def test_specific_tab_id(self) -> None:
        doc = _doc_with_content("Hello\n", tab_id="t.42")
        client = _mock_client()
        client.get_document.return_value = doc
        client.batch_update.return_value = []

        uploader = Uploader(client=client)
        result = uploader.update_document("doc-123", "Changed\n", tab_id="t.42")
        assert result is True

    def test_missing_tab_raises(self) -> None:
        doc = _doc_with_content("Hello\n", tab_id="t.0")
        client = _mock_client()
        client.get_document.return_value = doc

        uploader = Uploader(client=client)
        with pytest.raises(ValueError, match="No tab found"):
            uploader.update_document("doc-123", "text\n", tab_id="t.missing")

    def test_tab_without_content_raises(self) -> None:
        doc = Document(
            documentId="doc-123",
            tabs=[Tab(tabProperties=TabProperties(tabId="t.0", title="Empty"))],
        )
        client = _mock_client()
        client.get_document.return_value = doc

        uploader = Uploader(client=client)
        with pytest.raises(ValueError, match="has no content"):
            uploader.update_document("doc-123", "text\n")


class TestUpdateFromDirectory:
    def test_matching_tabs_updated(self, tmp_path: Path) -> None:
        doc = _doc_with_content("Hello\n", tab_id="t.0")
        assert doc.tabs is not None
        doc.tabs[0].tabProperties.title = "Main"  # type: ignore[union-attr]

        md_dir = tmp_path / "doc"
        md_dir.mkdir()
        (md_dir / "Main.md").write_text("Updated content\n", encoding="utf-8")

        client = _mock_client()
        client.get_document.return_value = doc
        client.batch_update.return_value = []

        uploader = Uploader(client=client)
        results = uploader.update_from_directory("doc-123", md_dir)
        assert "Main" in results

    def test_nonexistent_directory_raises(self) -> None:
        client = _mock_client()
        uploader = Uploader(client=client)
        with pytest.raises(FileNotFoundError):
            uploader.update_from_directory("doc-123", "/nonexistent")

    def test_unmatched_tab_returns_false(self, tmp_path: Path) -> None:
        doc = _doc_with_content("Hello\n", tab_id="t.0")
        assert doc.tabs is not None
        doc.tabs[0].tabProperties.title = "Main"  # type: ignore[union-attr]

        md_dir = tmp_path / "doc"
        md_dir.mkdir()
        (md_dir / "Other.md").write_text("Content\n", encoding="utf-8")

        client = _mock_client()
        client.get_document.return_value = doc

        uploader = Uploader(client=client)
        results = uploader.update_from_directory("doc-123", md_dir)
        assert results.get("Other") is False
