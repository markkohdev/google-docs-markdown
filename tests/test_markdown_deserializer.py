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


class TestDeserializerTableFormatting:
    def test_bold_headers_emit_bold_style_requests(self) -> None:
        md = "| **A** | **B** |\n| --- | --- |\n| C | D |\n"
        requests = deserialize(md)

        bold_reqs = [
            r
            for r in _find_all_requests(requests, "updateTextStyle")
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is True
        ]
        assert len(bold_reqs) == 2

        cell_inserts = _find_all_requests(requests, "insertText")
        texts = [r.insertText.text for r in cell_inserts if r.insertText and r.insertText.text]
        assert "A" in texts
        assert "B" in texts
        for t in texts:
            assert "**" not in t

    def test_non_bold_headers_no_bold_style(self) -> None:
        md = "| A | B |\n| --- | --- |\n| C | D |\n"
        requests = deserialize(md)

        bold_reqs = [
            r
            for r in _find_all_requests(requests, "updateTextStyle")
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is True
        ]
        assert len(bold_reqs) == 0

    def test_table_emits_pin_header_rows_request(self) -> None:
        md = "| A | B |\n| --- | --- |\n| C | D |\n"
        requests = deserialize(md)

        pin_req = _find_request(requests, "pinTableHeaderRows")
        assert pin_req is not None
        assert pin_req.pinTableHeaderRows is not None
        assert pin_req.pinTableHeaderRows.pinnedHeaderRowsCount == 1
        assert pin_req.pinTableHeaderRows.tableStartLocation is not None

    def test_bold_header_pin_combined(self) -> None:
        md = "| **H1** | **H2** |\n| --- | --- |\n| D1 | D2 |\n"
        requests = deserialize(md)

        pin_req = _find_request(requests, "pinTableHeaderRows")
        assert pin_req is not None
        assert pin_req.pinTableHeaderRows is not None
        assert pin_req.pinTableHeaderRows.pinnedHeaderRowsCount == 1

        bold_reqs = [
            r
            for r in _find_all_requests(requests, "updateTextStyle")
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is True
        ]
        assert len(bold_reqs) == 2


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
        assert date_req.insertDate.dateElementProperties.timestamp == "2024-01-01T12:00:00Z"

    def test_date_tag_no_data_reconstructs_timestamp(self) -> None:
        md = "<!-- date -->2026-01-08<!-- /date -->\n"
        requests = deserialize(md)
        date_req = _find_request(requests, "insertDate")
        assert date_req is not None
        assert date_req.insertDate is not None
        assert date_req.insertDate.dateElementProperties is not None
        assert date_req.insertDate.dateElementProperties.timestamp == "2026-01-08T12:00:00Z"

    def test_date_tag_explicit_timestamp_preserved(self) -> None:
        md = '<!-- date: {"timestamp": "2025-06-15T09:30:00Z"} -->Jun 15<!-- /date -->\n'
        requests = deserialize(md)
        date_req = _find_request(requests, "insertDate")
        assert date_req is not None
        assert date_req.insertDate is not None
        assert date_req.insertDate.dateElementProperties is not None
        assert date_req.insertDate.dateElementProperties.timestamp == "2025-06-15T09:30:00Z"

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


class TestDeserializerTagsInLists:
    """Person, date, and other tags inside list items must produce proper API requests."""

    def test_person_tag_in_list_item(self) -> None:
        md = '- **Lead:** <!-- person: {"email": "alice@x.com"} -->Alice<!-- /person -->\n'
        requests = deserialize(md)
        person = _find_request(requests, "insertPerson")
        assert person is not None
        assert person.insertPerson is not None
        assert person.insertPerson.personProperties is not None
        assert person.insertPerson.personProperties.email == "alice@x.com"

        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 1

    def test_date_tag_in_list_item(self) -> None:
        md = "- Date: <!-- date -->2026-01-08<!-- /date -->\n"
        requests = deserialize(md)
        date_req = _find_request(requests, "insertDate")
        assert date_req is not None
        assert date_req.insertDate is not None

        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 1

    def test_multiple_list_items_with_tags(self) -> None:
        md = (
            '- <!-- person: {"email": "a@x.com"} -->Alice<!-- /person -->\n'
            '- <!-- person: {"email": "b@x.com"} -->Bob<!-- /person -->\n'
        )
        requests = deserialize(md)
        persons = _find_all_requests(requests, "insertPerson")
        assert len(persons) == 2
        emails = {
            p.insertPerson.personProperties.email for p in persons if p.insertPerson and p.insertPerson.personProperties
        }
        assert emails == {"a@x.com", "b@x.com"}

        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 2

    def test_ordered_list_with_person_tag(self) -> None:
        md = '1. Contact: <!-- person: {"email": "c@x.com"} -->Charlie<!-- /person -->\n'
        requests = deserialize(md)
        person = _find_request(requests, "insertPerson")
        assert person is not None

        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 1
        assert bullets[0].createParagraphBullets is not None
        assert bullets[0].createParagraphBullets.bulletPreset == "NUMBERED_DECIMAL_ALPHA_ROMAN"

    def test_list_item_with_bold_and_person_tag(self) -> None:
        md = '- **Lead:** <!-- person: {"email": "d@x.com"} -->Dana<!-- /person -->\n'
        requests = deserialize(md)
        person = _find_request(requests, "insertPerson")
        assert person is not None

        bold_reqs = [
            r
            for r in _find_all_requests(requests, "updateTextStyle")
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold
        ]
        assert len(bold_reqs) >= 1

    def test_list_item_without_tags_unchanged(self) -> None:
        md = "- plain item 1\n- plain item 2\n"
        requests = deserialize(md)
        assert _find_request(requests, "insertPerson") is None
        inserts = _find_all_requests(requests, "insertText")
        assert len(inserts) == 2


class TestDeserializerTagsInHeadings:
    """Comment tags inside headings must be dispatched properly."""

    def test_heading_with_suggestion_tag(self) -> None:
        md = '### <!-- suggestion: {"id": "s1", "type": "insertion"} -->Suggested heading\n<!-- /suggestion -->\n'
        requests = deserialize(md)
        style = _find_request(requests, "updateParagraphStyle")
        assert style is not None
        assert style.updateParagraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_3"

    def test_heading_without_tags_unchanged(self) -> None:
        md = "## Normal heading\n"
        requests = deserialize(md)
        style = _find_request(requests, "updateParagraphStyle")
        assert style is not None
        assert style.updateParagraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle is not None
        assert style.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_2"


class TestDeserializerFormattingWithTags:
    """Inline formatting (bold, italic) is preserved on text around tags."""

    def test_bold_text_before_person_tag(self) -> None:
        md = '**Leader:** <!-- person: {"email": "e@x.com"} -->Eve<!-- /person -->\n'
        requests = deserialize(md)

        person = _find_request(requests, "insertPerson")
        assert person is not None

        bold_reqs = [
            r
            for r in _find_all_requests(requests, "updateTextStyle")
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold
        ]
        assert len(bold_reqs) >= 1

    def test_italic_text_around_date_tag(self) -> None:
        md = "*Created:* <!-- date -->2026-01-01<!-- /date -->\n"
        requests = deserialize(md)

        date_req = _find_request(requests, "insertDate")
        assert date_req is not None

        italic_reqs = [
            r
            for r in _find_all_requests(requests, "updateTextStyle")
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.italic
        ]
        assert len(italic_reqs) >= 1

    def test_bold_does_not_leak_to_person_chip(self) -> None:
        """Bold on 'Lead:' must not leak onto the unformatted space before the person chip."""
        md = '**Lead:** <!-- person: {"email": "x@y.com"} -->Name<!-- /person -->\n'
        requests = deserialize(md)

        person = _find_request(requests, "insertPerson")
        assert person is not None

        style_reqs = _find_all_requests(requests, "updateTextStyle")
        bold_true = [
            r
            for r in style_reqs
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is True
        ]
        bold_false = [
            r
            for r in style_reqs
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is False
        ]
        assert len(bold_true) >= 1, "Bold should be applied to 'Lead:'"
        assert len(bold_false) >= 1, "Bold should be explicitly cleared on trailing text"

    def test_formatting_clear_prevents_inheritance(self) -> None:
        """Unformatted text after bold must get an explicit bold=false reset."""
        md = '**bold** plain <!-- person: {"email": "a@b.com"} -->A<!-- /person -->\n'
        requests = deserialize(md)

        style_reqs = _find_all_requests(requests, "updateTextStyle")
        bold_false = [
            r
            for r in style_reqs
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is False
        ]
        assert len(bold_false) >= 1, "Unformatted text after bold should get explicit clear"


class TestTitleSubtitleDeserialization:
    """Verify <!-- title --> and <!-- subtitle --> markers produce correct named styles."""

    def test_title_marker_produces_title_style(self) -> None:
        md = "<!-- title -->\n# My Title\n"
        requests = deserialize(md)
        style_req = _find_request(requests, "updateParagraphStyle")
        assert style_req is not None
        assert style_req.updateParagraphStyle is not None
        assert style_req.updateParagraphStyle.paragraphStyle is not None
        assert style_req.updateParagraphStyle.paragraphStyle.namedStyleType == "TITLE"

    def test_subtitle_marker_produces_subtitle_style(self) -> None:
        md = "<!-- subtitle -->\n*My Subtitle*\n"
        requests = deserialize(md)
        style_req = _find_request(requests, "updateParagraphStyle")
        assert style_req is not None
        assert style_req.updateParagraphStyle is not None
        assert style_req.updateParagraphStyle.paragraphStyle is not None
        assert style_req.updateParagraphStyle.paragraphStyle.namedStyleType == "SUBTITLE"

    def test_heading_without_title_marker_stays_heading(self) -> None:
        md = "# Normal Heading\n"
        requests = deserialize(md)
        style_req = _find_request(requests, "updateParagraphStyle")
        assert style_req is not None
        assert style_req.updateParagraphStyle is not None
        assert style_req.updateParagraphStyle.paragraphStyle is not None
        assert style_req.updateParagraphStyle.paragraphStyle.namedStyleType == "HEADING_1"


class TestBoldItalicWithTags:
    """Verify bold/italic formatting works alongside comment tags."""

    def test_bold_italic_with_style_tag(self) -> None:
        """Bold and italic formatting must survive when mixed with style tags."""
        md = (
            "This text **should be bold**. This text *should be italic*. "
            '<!-- style: {"color": "#E06666"} -->colored<!-- /style -->\n'
        )
        requests = deserialize(md)

        style_reqs = _find_all_requests(requests, "updateTextStyle")
        bold_on = [
            r
            for r in style_reqs
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.bold is True
        ]
        italic_on = [
            r
            for r in style_reqs
            if r.updateTextStyle and r.updateTextStyle.textStyle and r.updateTextStyle.textStyle.italic is True
        ]
        assert len(bold_on) >= 1, "Bold should be applied"
        assert len(italic_on) >= 1, "Italic should be applied"

    def test_all_text_content_present(self) -> None:
        """All text content must be emitted in insertText requests."""
        md = "**bold** normal *italic*\n"
        requests = deserialize(md)

        text_reqs = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in text_reqs if r.insertText and r.insertText.text)
        assert "bold" in all_text
        assert "normal" in all_text
        assert "italic" in all_text


class TestDeserializerImageProps:
    """Image deserialization with image-props comment tag."""

    def test_image_with_props_sets_object_size(self) -> None:
        md = '![photo](https://example.com/img.png)<!-- image-props: {"width": 200.0, "height": 100.0} -->\n'
        requests = deserialize(md)
        img_req = _find_request(requests, "insertInlineImage")
        assert img_req is not None
        assert img_req.insertInlineImage is not None
        assert img_req.insertInlineImage.uri == "https://example.com/img.png"
        assert img_req.insertInlineImage.objectSize is not None
        assert img_req.insertInlineImage.objectSize.width is not None
        assert img_req.insertInlineImage.objectSize.width.magnitude == 200.0
        assert img_req.insertInlineImage.objectSize.height is not None
        assert img_req.insertInlineImage.objectSize.height.magnitude == 100.0

    def test_image_without_props_no_object_size(self) -> None:
        md = "![alt](https://example.com/img.png)\n"
        requests = deserialize(md)
        img_req = _find_request(requests, "insertInlineImage")
        assert img_req is not None
        assert img_req.insertInlineImage is not None
        assert img_req.insertInlineImage.uri == "https://example.com/img.png"
        assert img_req.insertInlineImage.objectSize is None

    def test_image_props_with_only_width(self) -> None:
        md = '![](https://example.com/x.png)<!-- image-props: {"width": 150.0} -->\n'
        requests = deserialize(md)
        img_req = _find_request(requests, "insertInlineImage")
        assert img_req is not None
        assert img_req.insertInlineImage is not None
        assert img_req.insertInlineImage.objectSize is not None
        assert img_req.insertInlineImage.objectSize.width is not None
        assert img_req.insertInlineImage.objectSize.width.magnitude == 150.0
        assert img_req.insertInlineImage.objectSize.height is None


class TestHtmlBlockInterTagText:
    """Regression tests for text between comment tags in html_block lines."""

    def test_style_with_inline_code_between(self) -> None:
        """Text + backtick code between style tags should all be emitted."""
        md = (
            '<!-- style: {"font-size": 12.0} -->bigger text<!-- /style -->'
            '`code`<!-- style: {"font-size": 12.0} --> inline<!-- /style -->\n'
        )
        requests = deserialize(md)

        text_reqs = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in text_reqs if r.insertText and r.insertText.text)
        assert "bigger text" in all_text
        assert "code" in all_text
        assert "inline" in all_text

    def test_plain_text_between_tags_emitted(self) -> None:
        """Plain text between two self-closing tags should not be dropped."""
        md = "<!-- page-break -->some text<!-- page-break -->\n"
        requests = deserialize(md)

        text_reqs = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in text_reqs if r.insertText and r.insertText.text)
        assert "some text" in all_text

    def test_pure_comment_tag_block(self) -> None:
        """A pure comment tag html_block still works normally."""
        md = "<!-- page-break -->\n"
        requests = deserialize(md)
        pb = _find_request(requests, "insertPageBreak")
        assert pb is not None


class TestDeserializerFootnotes:
    """Footnote references emit CreateFootnoteRequest; definitions are stripped."""

    def test_footnote_ref_emits_create_footnote(self) -> None:
        md = "Hello[^1] world\n"
        requests = deserialize(md)
        fn = _find_request(requests, "createFootnote")
        assert fn is not None
        assert fn.createFootnote is not None
        assert fn.createFootnote.location is not None

    def test_footnote_ref_text_stripped(self) -> None:
        """The literal ``[^1]`` text must not appear in any insertText request."""
        md = "Hello[^1] world\n"
        requests = deserialize(md)
        inserts = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in inserts if r.insertText and r.insertText.text)
        assert "[^1]" not in all_text
        assert "Hello" in all_text
        assert "world" in all_text

    def test_footnote_ref_location_index(self) -> None:
        """CreateFootnoteRequest should point to the position after preceding text."""
        md = "Hello[^1] world\n"
        requests = deserialize(md)
        fn = _find_request(requests, "createFootnote")
        assert fn is not None
        assert fn.createFootnote is not None
        assert fn.createFootnote.location is not None
        assert fn.createFootnote.location.index == 6  # after "Hello" (index 1 + 5)

    def test_multiple_footnote_refs(self) -> None:
        md = "A[^1] B[^2] C\n"
        requests = deserialize(md)
        fns = _find_all_requests(requests, "createFootnote")
        assert len(fns) == 2

    def test_footnote_definition_stripped(self) -> None:
        """Footnote definitions like ``[^1]: text`` must not produce insertText."""
        md = "Hello[^1] world\n\n[^1]: This is a footnote\n"
        requests = deserialize(md)
        inserts = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in inserts if r.insertText and r.insertText.text)
        assert "[^1]: This is a footnote" not in all_text

    def test_footnote_ref_with_tab_id(self) -> None:
        md = "Text[^1] here\n"
        requests = deserialize(md, tab_id="t.1")
        fn = _find_request(requests, "createFootnote")
        assert fn is not None
        assert fn.createFootnote is not None
        assert fn.createFootnote.location is not None
        assert fn.createFootnote.location.tabId == "t.1"


class TestDeserializerHeaderFooter:
    """Header and footer comment tag blocks produce create requests."""

    def test_header_tag_produces_create_header(self) -> None:
        md = '<!-- header: {"id": "kix.abc123"} -->\nHeader content here\n<!-- /header -->\n'
        requests = deserialize(md)
        header_req = _find_request(requests, "createHeader")
        assert header_req is not None
        assert header_req.createHeader is not None
        assert header_req.createHeader.type == "DEFAULT"
        assert header_req.createHeader.sectionBreakLocation is not None
        assert header_req.createHeader.sectionBreakLocation.index == 0

    def test_footer_tag_produces_create_footer(self) -> None:
        md = '<!-- footer: {"id": "kix.def456"} -->\nFooter content here\n<!-- /footer -->\n'
        requests = deserialize(md)
        footer_req = _find_request(requests, "createFooter")
        assert footer_req is not None
        assert footer_req.createFooter is not None
        assert footer_req.createFooter.type == "DEFAULT"
        assert footer_req.createFooter.sectionBreakLocation is not None
        assert footer_req.createFooter.sectionBreakLocation.index == 0

    def test_header_tag_with_tab_id(self) -> None:
        md = '<!-- header: {"id": "kix.h1"} -->\nContent\n<!-- /header -->\n'
        requests = deserialize(md, tab_id="t.2")
        header_req = _find_request(requests, "createHeader")
        assert header_req is not None
        assert header_req.createHeader is not None
        assert header_req.createHeader.sectionBreakLocation is not None
        assert header_req.createHeader.sectionBreakLocation.tabId == "t.2"

    def test_footer_tag_with_tab_id(self) -> None:
        md = '<!-- footer: {"id": "kix.f1"} -->\nContent\n<!-- /footer -->\n'
        requests = deserialize(md, tab_id="t.3")
        footer_req = _find_request(requests, "createFooter")
        assert footer_req is not None
        assert footer_req.createFooter is not None
        assert footer_req.createFooter.sectionBreakLocation is not None
        assert footer_req.createFooter.sectionBreakLocation.tabId == "t.3"


# ---------------------------------------------------------------------------
# Paragraph alignment deserialization tests (Feature 2)
# ---------------------------------------------------------------------------


class TestDeserializerAlignment:
    def test_center_alignment(self) -> None:
        md = '<!-- align: {"value": "center"} -->\nCentered text\n'
        requests = deserialize(md)
        insert = _find_request(requests, "insertText")
        assert insert is not None
        assert insert.insertText is not None
        assert "Centered text" in (insert.insertText.text or "")

        style_reqs = _find_all_requests(requests, "updateParagraphStyle")
        align_req = None
        for s in style_reqs:
            ps = s.updateParagraphStyle
            if ps and ps.paragraphStyle and ps.paragraphStyle.alignment == "CENTER":
                align_req = s
        assert align_req is not None
        assert align_req.updateParagraphStyle is not None
        assert align_req.updateParagraphStyle.fields == "alignment"

    def test_right_alignment(self) -> None:
        md = '<!-- align: {"value": "right"} -->\nRight aligned\n'
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateParagraphStyle")
        align_req = None
        for s in style_reqs:
            ps = s.updateParagraphStyle
            if ps and ps.paragraphStyle and ps.paragraphStyle.alignment == "END":
                align_req = s
        assert align_req is not None

    def test_justify_alignment(self) -> None:
        md = '<!-- align: {"value": "justify"} -->\nJustified text\n'
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateParagraphStyle")
        align_req = None
        for s in style_reqs:
            ps = s.updateParagraphStyle
            if ps and ps.paragraphStyle and ps.paragraphStyle.alignment == "JUSTIFIED":
                align_req = s
        assert align_req is not None

    def test_no_alignment_tag_no_alignment_request(self) -> None:
        md = "Normal paragraph\n"
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateParagraphStyle")
        for s in style_reqs:
            ps = s.updateParagraphStyle
            if ps and ps.paragraphStyle:
                assert ps.paragraphStyle.alignment is None or ps.fields != "alignment"

    def test_alignment_with_heading(self) -> None:
        md = '<!-- align: {"value": "center"} -->\n# Centered Heading\n'
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateParagraphStyle")
        found_heading = False
        found_alignment = False
        for s in style_reqs:
            ps = s.updateParagraphStyle
            if ps and ps.paragraphStyle:
                if ps.paragraphStyle.namedStyleType == "HEADING_1":
                    found_heading = True
                if ps.paragraphStyle.alignment == "CENTER":
                    found_alignment = True
        assert found_heading
        assert found_alignment


# ---------------------------------------------------------------------------
# Superscript/subscript deserialization tests (Feature 3)
# ---------------------------------------------------------------------------


class TestDeserializerSuperSubscript:
    def test_superscript(self) -> None:
        md = "E=mc<sup>2</sup>\n"
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateTextStyle")
        sup_req = None
        for s in style_reqs:
            ts = s.updateTextStyle
            if ts and ts.textStyle and ts.textStyle.baselineOffset == "SUPERSCRIPT":
                sup_req = s
        assert sup_req is not None
        assert sup_req.updateTextStyle is not None
        assert "baselineOffset" in (sup_req.updateTextStyle.fields or "")

    def test_subscript(self) -> None:
        md = "H<sub>2</sub>O\n"
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateTextStyle")
        sub_req = None
        for s in style_reqs:
            ts = s.updateTextStyle
            if ts and ts.textStyle and ts.textStyle.baselineOffset == "SUBSCRIPT":
                sub_req = s
        assert sub_req is not None
        assert sub_req.updateTextStyle is not None
        assert "baselineOffset" in (sub_req.updateTextStyle.fields or "")

    def test_superscript_text_content(self) -> None:
        md = "x<sup>n</sup> value\n"
        requests = deserialize(md)
        inserts = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in inserts if r.insertText and r.insertText.text)
        assert "x" in all_text
        assert "n" in all_text
        assert "value" in all_text

    def test_subscript_text_content(self) -> None:
        md = "CO<sub>2</sub> emissions\n"
        requests = deserialize(md)
        inserts = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in inserts if r.insertText and r.insertText.text)
        assert "CO" in all_text
        assert "2" in all_text
        assert "emissions" in all_text

    def test_no_baseline_offset_for_normal_text(self) -> None:
        md = "Normal text\n"
        requests = deserialize(md)
        style_reqs = _find_all_requests(requests, "updateTextStyle")
        for s in style_reqs:
            ts = s.updateTextStyle
            if ts and ts.textStyle:
                assert ts.textStyle.baselineOffset is None


# ---------------------------------------------------------------------------
# Checklist deserialization tests (Feature 4)
# ---------------------------------------------------------------------------


class TestDeserializerChecklist:
    def test_unchecked_checkbox(self) -> None:
        md = "- [ ] Todo item\n"
        requests = deserialize(md)
        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 1
        assert bullets[0].createParagraphBullets is not None
        assert bullets[0].createParagraphBullets.bulletPreset == "BULLET_CHECKBOX"

        inserts = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in inserts if r.insertText and r.insertText.text)
        assert "Todo item" in all_text
        assert "[ ]" not in all_text

    def test_checked_checkbox(self) -> None:
        md = "- [x] Done item\n"
        requests = deserialize(md)
        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 1
        assert bullets[0].createParagraphBullets is not None
        assert bullets[0].createParagraphBullets.bulletPreset == "BULLET_CHECKBOX"

        inserts = _find_all_requests(requests, "insertText")
        all_text = "".join(r.insertText.text for r in inserts if r.insertText and r.insertText.text)
        assert "Done item" in all_text
        assert "[x]" not in all_text

    def test_mixed_checkbox_and_regular(self) -> None:
        md = "- [ ] Task one\n- Regular item\n"
        requests = deserialize(md)
        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 2
        presets = [b.createParagraphBullets.bulletPreset for b in bullets if b.createParagraphBullets]
        assert "BULLET_CHECKBOX" in presets
        assert "BULLET_DISC_CIRCLE_SQUARE" in presets

    def test_regular_bullet_unchanged(self) -> None:
        md = "- Regular bullet\n"
        requests = deserialize(md)
        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 1
        assert bullets[0].createParagraphBullets is not None
        assert bullets[0].createParagraphBullets.bulletPreset == "BULLET_DISC_CIRCLE_SQUARE"

    def test_multiple_checkboxes(self) -> None:
        md = "- [ ] First\n- [x] Second\n- [ ] Third\n"
        requests = deserialize(md)
        bullets = _find_all_requests(requests, "createParagraphBullets")
        assert len(bullets) == 3
        for b in bullets:
            assert b.createParagraphBullets is not None
            assert b.createParagraphBullets.bulletPreset == "BULLET_CHECKBOX"


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
