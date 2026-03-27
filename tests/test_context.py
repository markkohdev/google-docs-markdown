"""Tests for DocumentContext, SerContext, and DeserContext.

Verifies that ``from_document_tab()`` and ``from_metadata()`` produce
equivalent contexts for the same document, and that lookup methods
respect the named style hierarchy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google_docs_markdown.handlers.context import (
    DeserContext,
    DocumentContext,
    SerContext,
    optional_color_to_hex,
)
from google_docs_markdown.models.common import (
    Color,
    Dimension,
    OptionalColor,
    RgbColor,
    WeightedFontFamily,
)
from google_docs_markdown.models.document import (
    Body,
    DocumentTab,
    NamedStyle,
    NamedStyles,
)
from google_docs_markdown.models.styles import TextStyle

RESOURCES_DIR = Path(__file__).parent / "resources" / "document_jsons"
SINGLE_TAB_JSON = RESOURCES_DIR / "Markdown_Conversion_Example_-_Single-Tab.json"


# ---------------------------------------------------------------------------
# optional_color_to_hex tests
# ---------------------------------------------------------------------------


class TestOptionalColorToHex:
    def test_none(self) -> None:
        assert optional_color_to_hex(None) is None

    def test_no_color(self) -> None:
        assert optional_color_to_hex(OptionalColor()) is None

    def test_red(self) -> None:
        color = OptionalColor(color=Color(rgbColor=RgbColor(red=1.0, green=0.0, blue=0.0)))
        assert optional_color_to_hex(color) == "#FF0000"

    def test_black(self) -> None:
        color = OptionalColor(color=Color(rgbColor=RgbColor(red=0.0, green=0.0, blue=0.0)))
        assert optional_color_to_hex(color) == "#000000"

    def test_partial_rgb(self) -> None:
        color = OptionalColor(color=Color(rgbColor=RgbColor(green=0.5)))
        assert optional_color_to_hex(color) == "#007F00"


# ---------------------------------------------------------------------------
# DocumentContext.from_document_tab tests
# ---------------------------------------------------------------------------


def _named_styles(
    *,
    normal_font: str = "Arial",
    normal_size: float = 11.0,
    heading1_size: float | None = None,
    heading1_color: OptionalColor | None = None,
    heading1_font: str | None = None,
) -> NamedStyles:
    styles = [
        NamedStyle(
            namedStyleType="NORMAL_TEXT",
            textStyle=TextStyle(
                weightedFontFamily=WeightedFontFamily(fontFamily=normal_font, weight=400),
                fontSize=Dimension(magnitude=normal_size, unit="PT"),
            ),
        ),
    ]
    if heading1_size or heading1_color or heading1_font:
        ts = TextStyle()
        if heading1_size:
            ts.fontSize = Dimension(magnitude=heading1_size, unit="PT")
        if heading1_color:
            ts.foregroundColor = heading1_color
        if heading1_font:
            ts.weightedFontFamily = WeightedFontFamily(fontFamily=heading1_font, weight=400)
        styles.append(NamedStyle(namedStyleType="HEADING_1", textStyle=ts))
    return NamedStyles(styles=styles)


class TestDocumentContextFromDocumentTab:
    def test_basic_defaults(self) -> None:
        tab = DocumentTab(
            body=Body(content=[]),
            namedStyles=_named_styles(normal_font="Proxima Nova", normal_size=11.0),
        )
        ctx = DocumentContext.from_document_tab(tab)
        assert ctx.default_font == "Proxima Nova"
        assert ctx.default_font_size == 11.0
        assert ctx.default_fg_color == "#000000"
        assert ctx.default_link_color == "#1155CC"

    def test_heading_sizes_stored(self) -> None:
        tab = DocumentTab(
            body=Body(content=[]),
            namedStyles=_named_styles(heading1_size=20.0),
        )
        ctx = DocumentContext.from_document_tab(tab)
        assert ctx.named_style_sizes["HEADING_1"] == 20.0
        assert ctx.named_style_sizes.get("NORMAL_TEXT") == 11.0

    def test_heading_font_stored(self) -> None:
        tab = DocumentTab(
            body=Body(content=[]),
            namedStyles=_named_styles(heading1_font="Times New Roman"),
        )
        ctx = DocumentContext.from_document_tab(tab)
        assert ctx.named_style_fonts["HEADING_1"] == "Times New Roman"

    def test_heading_color_stored(self) -> None:
        red = OptionalColor(color=Color(rgbColor=RgbColor(red=1.0, green=0.0, blue=0.0)))
        tab = DocumentTab(
            body=Body(content=[]),
            namedStyles=_named_styles(heading1_color=red),
        )
        ctx = DocumentContext.from_document_tab(tab)
        assert ctx.named_style_colors["HEADING_1"] == "#FF0000"

    def test_no_named_styles(self) -> None:
        tab = DocumentTab(body=Body(content=[]))
        ctx = DocumentContext.from_document_tab(tab)
        assert ctx.default_font is None
        assert ctx.default_font_size is None
        assert ctx.default_fg_color == "#000000"

    def test_document_and_tab_ids(self) -> None:
        tab = DocumentTab(body=Body(content=[]))
        ctx = DocumentContext.from_document_tab(tab, document_id="doc123", tab_id="t.0")
        assert ctx.document_id == "doc123"
        assert ctx.tab_id == "t.0"

    def test_with_real_fixture(self) -> None:
        from google_docs_markdown.models import Document

        with open(SINGLE_TAB_JSON) as f:
            raw = json.load(f)
        doc = Document.model_validate(raw)
        tab = doc.tabs[0].documentTab  # type: ignore[index]
        assert tab is not None
        ctx = DocumentContext.from_document_tab(tab)
        assert ctx.default_font is not None
        assert ctx.default_font_size is not None
        assert len(ctx.named_style_sizes) > 0


# ---------------------------------------------------------------------------
# DocumentContext.from_metadata tests
# ---------------------------------------------------------------------------


class TestDocumentContextFromMetadata:
    def test_basic_metadata(self) -> None:
        metadata: dict[str, Any] = {
            "documentId": "abc",
            "tabId": "t.0",
            "defaultStyles": {
                "font": "Arial",
                "fontSize": 11.0,
            },
        }
        ctx = DocumentContext.from_metadata(metadata)
        assert ctx.default_font == "Arial"
        assert ctx.default_font_size == 11.0
        assert ctx.document_id == "abc"
        assert ctx.tab_id == "t.0"

    def test_heading_styles(self) -> None:
        metadata: dict[str, Any] = {
            "defaultStyles": {
                "font": "Arial",
                "fontSize": 11.0,
                "headingStyles": {
                    "HEADING_1": {"fontSize": 20.0, "color": "#FF0000", "font": "Times"},
                    "HEADING_2": {"fontSize": 16.0},
                },
            },
        }
        ctx = DocumentContext.from_metadata(metadata)
        assert ctx.named_style_sizes["HEADING_1"] == 20.0
        assert ctx.named_style_sizes["HEADING_2"] == 16.0
        assert ctx.named_style_colors["HEADING_1"] == "#FF0000"
        assert ctx.named_style_fonts["HEADING_1"] == "Times"

    def test_link_color(self) -> None:
        metadata: dict[str, Any] = {
            "defaultStyles": {"linkColor": "#0000FF"},
        }
        ctx = DocumentContext.from_metadata(metadata)
        assert ctx.default_link_color == "#0000FF"

    def test_date_defaults(self) -> None:
        metadata: dict[str, Any] = {
            "defaultStyles": {
                "dateDefaults": {
                    "format": "DATE_FORMAT_ISO8601",
                    "locale": "en",
                },
            },
        }
        ctx = DocumentContext.from_metadata(metadata)
        assert ctx.date_defaults is not None
        assert ctx.date_defaults["format"] == "DATE_FORMAT_ISO8601"

    def test_empty_metadata(self) -> None:
        ctx = DocumentContext.from_metadata({})
        assert ctx.default_font is None
        assert ctx.default_font_size is None
        assert ctx.default_fg_color == "#000000"
        assert ctx.default_link_color == "#1155CC"

    def test_normal_text_size_in_named_styles(self) -> None:
        metadata: dict[str, Any] = {
            "defaultStyles": {"fontSize": 12.0},
        }
        ctx = DocumentContext.from_metadata(metadata)
        assert ctx.named_style_sizes.get("NORMAL_TEXT") == 12.0


# ---------------------------------------------------------------------------
# DocumentContext equivalence tests
# ---------------------------------------------------------------------------


class TestDocumentContextEquivalence:
    """Verify that from_document_tab and from_metadata produce equivalent contexts."""

    def test_round_trip_through_metadata(self) -> None:
        """Build from DocumentTab, serialize metadata, rebuild from metadata.

        The reconstructed context should have equivalent lookup behavior.
        """
        tab = DocumentTab(
            body=Body(content=[]),
            namedStyles=_named_styles(
                normal_font="Proxima Nova",
                normal_size=11.0,
                heading1_size=20.0,
                heading1_font="Georgia",
            ),
        )
        original = DocumentContext.from_document_tab(tab)

        metadata: dict[str, Any] = {
            "defaultStyles": {
                "font": original.default_font,
                "fontSize": original.default_font_size,
                "headingStyles": {},
            },
        }
        for style_name in ("HEADING_1",):
            entry: dict[str, Any] = {}
            if style_name in original.named_style_sizes:
                entry["fontSize"] = original.named_style_sizes[style_name]
            font = original.named_style_fonts.get(style_name)
            if font and font != original.default_font:
                entry["font"] = font
            if entry:
                metadata["defaultStyles"]["headingStyles"][style_name] = entry

        reconstructed = DocumentContext.from_metadata(metadata)

        assert original.expected_font("NORMAL_TEXT") == reconstructed.expected_font("NORMAL_TEXT")
        assert original.expected_font_size("NORMAL_TEXT") == reconstructed.expected_font_size("NORMAL_TEXT")
        assert original.expected_font_size("HEADING_1") == reconstructed.expected_font_size("HEADING_1")
        assert original.expected_font("HEADING_1") == reconstructed.expected_font("HEADING_1")


# ---------------------------------------------------------------------------
# Lookup method tests
# ---------------------------------------------------------------------------


class TestDocumentContextLookups:
    def test_expected_font_size_default(self) -> None:
        ctx = DocumentContext(default_font_size=11.0)
        assert ctx.expected_font_size(None) == 11.0
        assert ctx.expected_font_size("NORMAL_TEXT") == 11.0

    def test_expected_font_size_heading_override(self) -> None:
        ctx = DocumentContext(
            default_font_size=11.0,
            named_style_sizes={"HEADING_1": 20.0},
        )
        assert ctx.expected_font_size("HEADING_1") == 20.0
        assert ctx.expected_font_size("NORMAL_TEXT") == 11.0

    def test_expected_color_default(self) -> None:
        ctx = DocumentContext(default_fg_color="#000000")
        assert ctx.expected_color(None) == "#000000"

    def test_expected_color_heading_override(self) -> None:
        ctx = DocumentContext(
            default_fg_color="#000000",
            named_style_colors={"HEADING_1": "#FF0000"},
        )
        assert ctx.expected_color("HEADING_1") == "#FF0000"
        assert ctx.expected_color("NORMAL_TEXT") == "#000000"

    def test_expected_color_none_entry(self) -> None:
        ctx = DocumentContext(
            default_fg_color="#000000",
            named_style_colors={"HEADING_1": None},
        )
        assert ctx.expected_color("HEADING_1") == "#000000"

    def test_expected_font_default(self) -> None:
        ctx = DocumentContext(default_font="Arial")
        assert ctx.expected_font(None) == "Arial"

    def test_expected_font_heading_override(self) -> None:
        ctx = DocumentContext(
            default_font="Arial",
            named_style_fonts={"HEADING_1": "Georgia"},
        )
        assert ctx.expected_font("HEADING_1") == "Georgia"
        assert ctx.expected_font("NORMAL_TEXT") == "Arial"


# ---------------------------------------------------------------------------
# SerContext tests
# ---------------------------------------------------------------------------


class TestSerContext:
    def test_initial_state(self) -> None:
        ctx = SerContext(doc=DocumentContext())
        assert ctx.current_para_style is None
        assert ctx.footnote_refs == []
        assert ctx.date_defaults is None
        assert ctx.pending_style_props is None

    def test_mutable_fields(self) -> None:
        ctx = SerContext(doc=DocumentContext())
        ctx.current_para_style = "HEADING_1"
        ctx.footnote_refs.append(("fn1", "1"))
        ctx.date_defaults = {"format": "ISO"}
        assert ctx.current_para_style == "HEADING_1"
        assert len(ctx.footnote_refs) == 1


# ---------------------------------------------------------------------------
# DeserContext tests
# ---------------------------------------------------------------------------


class TestDeserContext:
    def test_initial_state(self) -> None:
        ctx = DeserContext(doc=DocumentContext())
        assert ctx.index == 1
        assert ctx.tab_id == ""
        assert ctx.segment_id == ""
        assert ctx.requests == []

    def test_advance(self) -> None:
        ctx = DeserContext(doc=DocumentContext())
        ctx.advance(5)
        assert ctx.index == 6

    def test_emit(self) -> None:
        ctx = DeserContext(doc=DocumentContext())
        ctx.emit({"insertText": {"text": "hello"}})
        ctx.emit({"insertText": {"text": "world"}})
        assert len(ctx.requests) == 2

    def test_emit_multiple(self) -> None:
        ctx = DeserContext(doc=DocumentContext())
        ctx.emit(
            {"insertText": {"text": "a"}},
            {"insertText": {"text": "b"}},
        )
        assert len(ctx.requests) == 2
