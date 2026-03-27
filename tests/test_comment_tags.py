"""Tests for the comment tag serialization and parsing system."""

from __future__ import annotations

from google_docs_markdown.comment_tags import (
    TagType,
    closing_tag,
    opening_tag,
    parse_tags,
    self_closing_tag,
    wrap_tag,
)


class TestOpeningTag:
    def test_no_data(self) -> None:
        assert opening_tag(TagType.PAGE_BREAK) == "<!-- page-break -->"

    def test_with_data(self) -> None:
        result = opening_tag(TagType.PERSON, {"email": "a@b.com"})
        assert result == '<!-- person: {"email": "a@b.com"} -->'

    def test_string_tag_type(self) -> None:
        assert opening_tag("custom-tag") == "<!-- custom-tag -->"

    def test_with_data_string_type(self) -> None:
        result = opening_tag("section-break", {"type": "CONTINUOUS"})
        assert result == '<!-- section-break: {"type": "CONTINUOUS"} -->'

    def test_empty_dict_is_treated_as_no_data(self) -> None:
        assert opening_tag(TagType.EQUATION, {}) == "<!-- equation -->"


class TestClosingTag:
    def test_basic(self) -> None:
        assert closing_tag(TagType.PERSON) == "<!-- /person -->"

    def test_string_type(self) -> None:
        assert closing_tag("style") == "<!-- /style -->"


class TestWrapTag:
    def test_basic(self) -> None:
        result = wrap_tag(TagType.PERSON, "Mark Koh", {"email": "mk@x.com"})
        assert result == '<!-- person: {"email": "mk@x.com"} -->Mark Koh<!-- /person -->'

    def test_no_data(self) -> None:
        result = wrap_tag(TagType.SUGGESTION, "text")
        assert result == "<!-- suggestion -->text<!-- /suggestion -->"

    def test_style(self) -> None:
        result = wrap_tag(TagType.STYLE, "**bold red**", {"color": "#FF0000"})
        assert result == '<!-- style: {"color": "#FF0000"} -->**bold red**<!-- /style -->'


class TestSelfClosingTag:
    def test_basic(self) -> None:
        result = self_closing_tag(TagType.TABLE_OF_CONTENTS)
        assert result == "<!-- table-of-contents -->"

    def test_with_data(self) -> None:
        result = self_closing_tag(TagType.AUTO_TEXT, {"type": "PAGE_NUMBER"})
        assert result == '<!-- auto-text: {"type": "PAGE_NUMBER"} -->'


class TestParseTags:
    def test_self_closing(self) -> None:
        text = "hello <!-- page-break --> world"
        tags = parse_tags(text)
        assert len(tags) == 1
        assert tags[0].tag_type == "page-break"
        assert tags[0].data is None
        assert tags[0].content is None

    def test_self_closing_with_data(self) -> None:
        text = '<!-- section-break: {"type": "CONTINUOUS"} -->'
        tags = parse_tags(text)
        assert len(tags) == 1
        assert tags[0].tag_type == "section-break"
        assert tags[0].data == {"type": "CONTINUOUS"}
        assert tags[0].content is None

    def test_wrapping_tag(self) -> None:
        text = '<!-- person: {"email": "a@b.com"} -->Alice<!-- /person -->'
        tags = parse_tags(text)
        assert len(tags) == 1
        assert tags[0].tag_type == "person"
        assert tags[0].data == {"email": "a@b.com"}
        assert tags[0].content == "Alice"

    def test_multiple_tags(self) -> None:
        text = '<!-- page-break --> hello <!-- person: {"email": "x@y.com"} -->Bob<!-- /person --> <!-- equation -->'
        tags = parse_tags(text)
        assert len(tags) == 3
        assert tags[0].tag_type == "page-break"
        assert tags[1].tag_type == "person"
        assert tags[1].content == "Bob"
        assert tags[2].tag_type == "equation"

    def test_nested_content_with_markdown(self) -> None:
        text = '<!-- style: {"color": "#FF0000"} -->**bold text**<!-- /style -->'
        tags = parse_tags(text)
        assert len(tags) == 1
        assert tags[0].content == "**bold text**"

    def test_roundtrip_wrap_tag(self) -> None:
        original_data = {"email": "test@example.com"}
        original_content = "Test User"
        tag_str = wrap_tag(TagType.PERSON, original_content, original_data)
        parsed = parse_tags(tag_str)
        assert len(parsed) == 1
        assert parsed[0].data == original_data
        assert parsed[0].content == original_content

    def test_empty_text(self) -> None:
        assert parse_tags("") == []

    def test_no_tags(self) -> None:
        assert parse_tags("just regular markdown text") == []

    def test_tag_spans(self) -> None:
        text = "before <!-- title --> after"
        tags = parse_tags(text)
        assert len(tags) == 1
        assert text[tags[0].start : tags[0].end] == "<!-- title -->"


class TestTagTypeEnum:
    def test_str_conversion(self) -> None:
        assert str(TagType.PERSON) == "person"
        assert str(TagType.RICH_LINK) == "rich-link"

    def test_all_types_produce_valid_tags(self) -> None:
        for tag_type in TagType:
            tag = opening_tag(tag_type)
            assert tag.startswith("<!-- ")
            assert tag.endswith(" -->")
