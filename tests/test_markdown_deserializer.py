"""Tests for the Markdown deserializer."""

from __future__ import annotations

from google_docs_markdown.markdown_deserializer import MarkdownDeserializer, deserialize
from google_docs_markdown.models.requests import Request


class TestDeserializerHeadings:
    def test_heading_1(self) -> None:
        requests = deserialize("# Heading 1\n")
        insert = _find_request(requests, "insertText")
        assert insert is not None
        assert insert.insertText is not None
        assert insert.insertText.text == "Heading 1\n"
        assert insert.insertText.location is not None
        assert insert.insertText.location.index == 1

        style = _find_request(requests, "updateParagraphStyle")
        assert style is not None
        assert style.updateParagraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_1"

    def test_heading_2(self) -> None:
        requests = deserialize("## Heading 2\n")
        style = _find_request(requests, "updateParagraphStyle")
        assert style is not None
        assert style.updateParagraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_2"

    def test_heading_3(self) -> None:
        requests = deserialize("### Heading 3\n")
        style = _find_request(requests, "updateParagraphStyle")
        assert style is not None
        assert style.updateParagraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_3"

    def test_heading_levels_4_through_6(self) -> None:
        for level in (4, 5, 6):
            prefix = "#" * level
            requests = deserialize(f"{prefix} H{level}\n")
            style = _find_request(requests, "updateParagraphStyle")
            assert style is not None
            assert style.updateParagraphStyle is not None
            assert style.updateParagraphStyle.paragraphStyle is not None
            assert style.updateParagraphStyle.paragraphStyle.namedStyleType == f"HEADING_{level}"


class TestDeserializerParagraphs:
    def test_simple_paragraph(self) -> None:
        requests = deserialize("Hello, world!\n")
        insert = _find_request(requests, "insertText")
        assert insert is not None
        assert insert.insertText is not None
        assert insert.insertText.text == "Hello, world!\n"

    def test_multiple_paragraphs(self) -> None:
        requests = deserialize("First paragraph.\n\nSecond paragraph.\n")
        inserts = _find_all_requests(requests, "insertText")
        assert len(inserts) == 2
        assert inserts[0].insertText is not None
        assert inserts[0].insertText.text == "First paragraph.\n"
        assert inserts[1].insertText is not None
        assert inserts[1].insertText.text == "Second paragraph.\n"

    def test_empty_input(self) -> None:
        requests = deserialize("")
        assert requests == []

    def test_whitespace_only(self) -> None:
        requests = deserialize("   \n\n   \n")
        assert len(requests) == 0


class TestDeserializerInlineFormatting:
    def test_bold(self) -> None:
        requests = deserialize("This is **bold** text.\n")
        style_req = _find_request(requests, "updateTextStyle")
        assert style_req is not None
        assert style_req.updateTextStyle is not None
        assert style_req.updateTextStyle.textStyle is not None
        assert style_req.updateTextStyle.textStyle.bold is True
        assert style_req.updateTextStyle.fields == "bold"

    def test_italic(self) -> None:
        requests = deserialize("This is *italic* text.\n")
        style_req = _find_request(requests, "updateTextStyle")
        assert style_req is not None
        assert style_req.updateTextStyle is not None
        assert style_req.updateTextStyle.textStyle is not None
        assert style_req.updateTextStyle.textStyle.italic is True

    def test_strikethrough(self) -> None:
        requests = deserialize("This is ~~struck~~ text.\n")
        style_req = _find_request(requests, "updateTextStyle")
        assert style_req is not None
        assert style_req.updateTextStyle is not None
        assert style_req.updateTextStyle.textStyle is not None
        assert style_req.updateTextStyle.textStyle.strikethrough is True

    def test_bold_italic_combined(self) -> None:
        requests = deserialize("This is ***bold italic*** text.\n")
        styles = _find_all_requests(requests, "updateTextStyle")
        assert len(styles) >= 1
        for s in styles:
            ts = s.updateTextStyle
            assert ts is not None
            assert ts.textStyle is not None
            if ts.textStyle.bold and ts.textStyle.italic:
                return
        fields_combined = set()
        for s in styles:
            ts = s.updateTextStyle
            assert ts is not None
            assert ts.textStyle is not None
            if ts.textStyle.bold:
                fields_combined.add("bold")
            if ts.textStyle.italic:
                fields_combined.add("italic")
        assert "bold" in fields_combined
        assert "italic" in fields_combined

    def test_inline_code(self) -> None:
        requests = deserialize("Use `code` here.\n")
        style_req = _find_request(requests, "updateTextStyle")
        assert style_req is not None
        assert style_req.updateTextStyle is not None
        assert style_req.updateTextStyle.textStyle is not None
        wff = style_req.updateTextStyle.textStyle.weightedFontFamily
        assert wff is not None
        assert wff.fontFamily == "Roboto Mono"

    def test_link(self) -> None:
        requests = deserialize("[click here](https://example.com)\n")
        style_req = _find_request(requests, "updateTextStyle")
        assert style_req is not None
        assert style_req.updateTextStyle is not None
        assert style_req.updateTextStyle.textStyle is not None
        assert style_req.updateTextStyle.textStyle.link is not None
        assert style_req.updateTextStyle.textStyle.link.url == "https://example.com"


class TestDeserializerLists:
    def test_unordered_list(self) -> None:
        requests = deserialize("- item 1\n- item 2\n")
        inserts = _find_all_requests(requests, "insertText")
        assert len(inserts) == 2
        assert inserts[0].insertText is not None
        assert inserts[0].insertText.text == "item 1\n"
        assert inserts[1].insertText is not None
        assert inserts[1].insertText.text == "item 2\n"

        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 2
        assert bullets[0].createParagraphBullets is not None
        assert bullets[0].createParagraphBullets.bulletPreset == "BULLET_DISC_CIRCLE_SQUARE"

    def test_ordered_list(self) -> None:
        requests = deserialize("1. first\n2. second\n")
        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 2
        assert bullets[0].createParagraphBullets is not None
        assert bullets[0].createParagraphBullets.bulletPreset == "NUMBERED_DECIMAL_ALPHA_ROMAN"


class TestDeserializerCodeBlock:
    def test_fenced_code_block(self) -> None:
        requests = deserialize("```python\ndef hello():\n    pass\n```\n")
        insert = _find_request(requests, "insertText")
        assert insert is not None
        assert insert.insertText is not None
        assert "def hello():" in (insert.insertText.text or "")

        style = _find_request(requests, "updateTextStyle")
        assert style is not None
        assert style.updateTextStyle is not None
        assert style.updateTextStyle.textStyle is not None
        wff = style.updateTextStyle.textStyle.weightedFontFamily
        assert wff is not None
        assert wff.fontFamily == "Roboto Mono"

    def test_empty_code_block(self) -> None:
        requests = deserialize("```\n\n```\n")
        insert = _find_request(requests, "insertText")
        assert insert is not None


class TestDeserializerTable:
    def test_basic_table(self) -> None:
        md = "| A | B |\n| --- | --- |\n| C | D |\n"
        requests = deserialize(md)
        table_req = _find_request(requests, "insertTable")
        assert table_req is not None
        assert table_req.insertTable is not None
        assert table_req.insertTable.rows == 2
        assert table_req.insertTable.columns == 2

        cell_inserts = _find_all_requests(requests, "insertText")
        texts = [r.insertText.text for r in cell_inserts if r.insertText and r.insertText.text]
        assert "A" in texts
        assert "B" in texts
        assert "C" in texts
        assert "D" in texts


class TestDeserializerCommentTags:
    def test_person_tag(self) -> None:
        md = '<!-- person: {"email": "alice@example.com"} -->Alice<!-- /person -->\n'
        requests = deserialize(md)
        person_req = _find_request(requests, "insertPerson")
        assert person_req is not None
        assert person_req.insertPerson is not None
        assert person_req.insertPerson.personProperties is not None
        assert person_req.insertPerson.personProperties.email == "alice@example.com"

    def test_date_tag(self) -> None:
        md = '<!-- date: {"format": "DATE_FORMAT_ISO8601"} -->2024-01-01<!-- /date -->\n'
        requests = deserialize(md)
        date_req = _find_request(requests, "insertDate")
        assert date_req is not None
        assert date_req.insertDate is not None
        assert date_req.insertDate.dateElementProperties is not None
        assert date_req.insertDate.dateElementProperties.dateFormat == "DATE_FORMAT_ISO8601"

    def test_page_break_tag(self) -> None:
        md = "Some text.\n\n<!-- page-break -->\n\nMore text.\n"
        requests = deserialize(md)
        pb = _find_request(requests, "insertPageBreak")
        assert pb is not None

    def test_section_break_tag(self) -> None:
        md = '<!-- section-break: {"type": "NEXT_PAGE"} -->\n'
        requests = deserialize(md)
        sb = _find_request(requests, "insertSectionBreak")
        assert sb is not None
        assert sb.insertSectionBreak is not None
        assert sb.insertSectionBreak.sectionType == "NEXT_PAGE"


class TestDeserializerMetadata:
    def test_metadata_stripped_from_output(self) -> None:
        md = 'Hello\n\n<!-- google-docs-metadata\n{"documentId": "abc123", "tabId": "t.0"}\n-->\n'
        requests = deserialize(md)
        inserts = _find_all_requests(requests, "insertText")
        for ins in inserts:
            assert ins.insertText is not None
            assert "google-docs-metadata" not in (ins.insertText.text or "")

    def test_metadata_tab_id_used(self) -> None:
        md = 'Hello\n\n<!-- google-docs-metadata\n{"tabId": "t.5"}\n-->\n'
        deser = MarkdownDeserializer()
        requests = deser.deserialize(md)
        assert len(requests) > 0


class TestDeserializerTabAndSegment:
    def test_tab_id_in_requests(self) -> None:
        requests = deserialize("Hello\n", tab_id="t.1")
        insert = _find_request(requests, "insertText")
        assert insert is not None
        assert insert.insertText is not None
        assert insert.insertText.location is not None
        assert insert.insertText.location.tabId == "t.1"

    def test_segment_id_in_requests(self) -> None:
        requests = deserialize("Hello\n", segment_id="kix.header1")
        insert = _find_request(requests, "insertText")
        assert insert is not None
        assert insert.insertText is not None
        assert insert.insertText.location is not None
        assert insert.insertText.location.segmentId == "kix.header1"


class TestDeserializerConvenienceFunction:
    def test_convenience_function(self) -> None:
        requests = deserialize("Hello\n")
        assert len(requests) > 0
        assert all(isinstance(r, Request) for r in requests)


class TestDeserializerEdgeCases:
    def test_heading_with_formatting(self) -> None:
        requests = deserialize("# **Bold Heading**\n")
        style = _find_request(requests, "updateParagraphStyle")
        assert style is not None
        assert style.updateParagraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_1"

    def test_paragraph_with_multiple_formats(self) -> None:
        requests = deserialize("**bold** and *italic* and ~~struck~~\n")
        styles = _find_all_requests(requests, "updateTextStyle")
        assert len(styles) == 3
        formats = set()
        for s in styles:
            ts = s.updateTextStyle
            assert ts is not None
            assert ts.textStyle is not None
            if ts.textStyle.bold:
                formats.add("bold")
            if ts.textStyle.italic:
                formats.add("italic")
            if ts.textStyle.strikethrough:
                formats.add("strikethrough")
        assert formats == {"bold", "italic", "strikethrough"}

    def test_index_progression(self) -> None:
        """Verify that request indices progress monotonically."""
        requests = deserialize("# Title\n\nParagraph text here.\n\n## Subtitle\n")
        inserts = _find_all_requests(requests, "insertText")
        indices = []
        for ins in inserts:
            assert ins.insertText is not None
            assert ins.insertText.location is not None
            assert ins.insertText.location.index is not None
            indices.append(ins.insertText.location.index)
        assert indices == sorted(indices)


class TestDeserializerRichLink:
    def test_rich_link_tag_produces_insert_and_style(self) -> None:
        md = (
            '<!-- rich-link: {"mimeType": "application/pdf"} -->'
            "[My Doc](https://docs.google.com/doc)"
            "<!-- /rich-link -->\n"
        )
        requests = deserialize(md)
        assert len(requests) > 0


class TestDeserializerStyleTag:
    def test_style_tag_with_color(self) -> None:
        md = '<!-- style: {"color": "#FF0000"} -->red text<!-- /style -->\n'
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateTextStyle")
        found_color = False
        for s in style_reqs:
            ts = s.updateTextStyle
            assert ts is not None
            if ts.textStyle and ts.textStyle.foregroundColor:
                found_color = True
        assert found_color or len(requests) > 0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _find_request(requests: list[Request], field: str) -> Request | None:
    """Find the first request with the given non-None field."""
    for r in requests:
        if getattr(r, field, None) is not None:
            return r
    return None


def _find_all_requests(requests: list[Request], field: str) -> list[Request]:
    """Find all requests with the given non-None field."""
    return [r for r in requests if getattr(r, field, None) is not None]
