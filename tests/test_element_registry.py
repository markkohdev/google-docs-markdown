"""Tests for the element registry shared constants."""

from __future__ import annotations

from google_docs_markdown.element_registry import (
    CODE_BLOCK_MARKER,
    DEFAULT_LINK_COLOR,
    HEADING_PREFIX,
    HEADING_STYLES,
    INLINE_CODE_COLOR,
    INLINE_MARKER_TO_STYLE_FIELD,
    MD_HEADING_LEVEL_TO_STYLE,
    MONOSPACE_FONT,
    ORDERED_GLYPH_TYPES,
    TAG_TO_REQUEST_FIELD,
    InlineMarker,
)


class TestHeadingConstants:
    def test_heading_prefix_maps_all_levels(self) -> None:
        assert HEADING_PREFIX["TITLE"] == "#"
        assert HEADING_PREFIX["HEADING_1"] == "#"
        assert HEADING_PREFIX["HEADING_2"] == "##"
        assert HEADING_PREFIX["HEADING_3"] == "###"
        assert HEADING_PREFIX["HEADING_4"] == "####"
        assert HEADING_PREFIX["HEADING_5"] == "#####"
        assert HEADING_PREFIX["HEADING_6"] == "######"

    def test_heading_styles_frozenset(self) -> None:
        assert "TITLE" in HEADING_STYLES
        assert "SUBTITLE" in HEADING_STYLES
        assert "HEADING_1" in HEADING_STYLES
        assert "HEADING_6" in HEADING_STYLES
        assert "NORMAL_TEXT" not in HEADING_STYLES

    def test_md_heading_level_to_style(self) -> None:
        assert MD_HEADING_LEVEL_TO_STYLE[1] == "HEADING_1"
        assert MD_HEADING_LEVEL_TO_STYLE[6] == "HEADING_6"


class TestListConstants:
    def test_ordered_glyph_types(self) -> None:
        assert "DECIMAL" in ORDERED_GLYPH_TYPES
        assert "ROMAN" in ORDERED_GLYPH_TYPES
        assert "UPPER_ALPHA" in ORDERED_GLYPH_TYPES
        assert "BULLET" not in ORDERED_GLYPH_TYPES


class TestCodeConstants:
    def test_code_block_marker(self) -> None:
        assert CODE_BLOCK_MARKER == "\ue907"

    def test_monospace_font(self) -> None:
        assert MONOSPACE_FONT == "Roboto Mono"

    def test_inline_code_color(self) -> None:
        assert INLINE_CODE_COLOR == "#188037"


class TestInlineMarkerConstants:
    def test_inline_markers(self) -> None:
        assert InlineMarker.BOLD == "**"
        assert InlineMarker.ITALIC == "*"
        assert InlineMarker.STRIKETHROUGH == "~~"
        assert InlineMarker.UNDERLINE == "<u>"
        assert InlineMarker.INLINE_CODE == "`"

    def test_marker_to_style_field(self) -> None:
        assert INLINE_MARKER_TO_STYLE_FIELD["**"] == "bold"
        assert INLINE_MARKER_TO_STYLE_FIELD["*"] == "italic"
        assert INLINE_MARKER_TO_STYLE_FIELD["~~"] == "strikethrough"
        assert INLINE_MARKER_TO_STYLE_FIELD["`"] == "inline_code"


class TestDefaultConstants:
    def test_default_link_color(self) -> None:
        assert DEFAULT_LINK_COLOR == "#1155CC"


class TestTagToRequestField:
    def test_person_mapping(self) -> None:
        assert TAG_TO_REQUEST_FIELD["person"] == "insertPerson"

    def test_date_mapping(self) -> None:
        assert TAG_TO_REQUEST_FIELD["date"] == "insertDate"

    def test_page_break_mapping(self) -> None:
        assert TAG_TO_REQUEST_FIELD["page-break"] == "insertPageBreak"

    def test_style_mapping(self) -> None:
        assert TAG_TO_REQUEST_FIELD["style"] == "updateTextStyle"
