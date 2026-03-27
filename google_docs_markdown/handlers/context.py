"""Three-layer context architecture for handler-based serialization/deserialization.

Layer 1 — DocumentContext (frozen, shared between ser and deser):
    Document-level defaults and lookup methods.  Populated from
    ``DocumentTab.namedStyles`` (serialization) or the embedded
    ``<!-- google-docs-metadata ... -->`` block (deserialization).

Layer 2 — SerContext / DeserContext (mutable, direction-specific):
    Traversal state, accumulators, and callbacks set by the orchestrator.

Layer 3 — Paragraph scope (transient):
    ``ctx.current_para_style`` is set/cleared by the orchestrator per
    paragraph.  Handlers read it but never set it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from google_docs_markdown.models.common import OptionalColor
from google_docs_markdown.models.document import DocumentTab
from google_docs_markdown.models.elements import ParagraphElement, StructuralElement

_DEFAULT_LINK_COLOR = "#1155CC"


def optional_color_to_hex(color: OptionalColor | None) -> str | None:
    """Convert an OptionalColor to a hex string like ``#FF0000``.

    Returns ``None`` if the color is unset, transparent, or has no RGB values.
    Black (``#000000``) is returned as a valid color — callers compare
    against the document default to decide whether to suppress it.
    """
    if not color or not color.color or not color.color.rgbColor:
        return None
    rgb = color.color.rgbColor
    r = int((rgb.red or 0) * 255)
    g = int((rgb.green or 0) * 255)
    b = int((rgb.blue or 0) * 255)
    return f"#{r:02X}{g:02X}{b:02X}"


@dataclass(frozen=True)
class DocumentContext:
    """Frozen, document-level defaults shared between serialization and deserialization."""

    default_font: str | None = None
    default_font_size: float | None = None
    default_fg_color: str = "#000000"
    default_link_color: str = _DEFAULT_LINK_COLOR
    named_style_sizes: dict[str, float] = field(default_factory=dict)
    named_style_colors: dict[str, str | None] = field(default_factory=dict)
    named_style_fonts: dict[str, str | None] = field(default_factory=dict)
    date_defaults: dict[str, str] | None = None
    document_id: str | None = None
    tab_id: str | None = None

    @classmethod
    def from_document_tab(
        cls,
        tab: DocumentTab,
        *,
        document_id: str | None = None,
        tab_id: str | None = None,
    ) -> DocumentContext:
        """Build context from a ``DocumentTab``'s named styles (serialization path)."""
        default_font: str | None = None
        default_font_size: float | None = None
        default_fg_color = "#000000"
        named_style_sizes: dict[str, float] = {}
        named_style_colors: dict[str, str | None] = {}
        named_style_fonts: dict[str, str | None] = {}

        if tab.namedStyles and tab.namedStyles.styles:
            for ns in tab.namedStyles.styles:
                if not ns.namedStyleType or not ns.textStyle:
                    continue
                ts = ns.textStyle
                if ts.fontSize and ts.fontSize.magnitude is not None:
                    named_style_sizes[ns.namedStyleType] = ts.fontSize.magnitude
                named_style_colors[ns.namedStyleType] = optional_color_to_hex(ts.foregroundColor)
                if ts.weightedFontFamily and ts.weightedFontFamily.fontFamily:
                    named_style_fonts[ns.namedStyleType] = ts.weightedFontFamily.fontFamily
                if ns.namedStyleType == "NORMAL_TEXT":
                    if ts.weightedFontFamily and ts.weightedFontFamily.fontFamily:
                        default_font = ts.weightedFontFamily.fontFamily
                    if ts.fontSize and ts.fontSize.magnitude is not None:
                        default_font_size = ts.fontSize.magnitude
                    fg = optional_color_to_hex(ts.foregroundColor)
                    if fg:
                        default_fg_color = fg

        return cls(
            default_font=default_font,
            default_font_size=default_font_size,
            default_fg_color=default_fg_color,
            named_style_sizes=named_style_sizes,
            named_style_colors=named_style_colors,
            named_style_fonts=named_style_fonts,
            document_id=document_id,
            tab_id=tab_id,
        )

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> DocumentContext:
        """Build context from the parsed ``<!-- google-docs-metadata ... -->`` block.

        This is the deserialization path — reconstructs the same defaults
        that were captured during serialization.
        """
        ds = metadata.get("defaultStyles") or {}

        default_font = ds.get("font")
        default_font_size = ds.get("fontSize")
        default_link_color = ds.get("linkColor", _DEFAULT_LINK_COLOR)
        date_defaults = ds.get("dateDefaults")

        named_style_sizes: dict[str, float] = {}
        named_style_colors: dict[str, str | None] = {}
        named_style_fonts: dict[str, str | None] = {}

        if default_font_size is not None:
            named_style_sizes["NORMAL_TEXT"] = default_font_size

        heading_styles = ds.get("headingStyles") or {}
        for style_name, entry in heading_styles.items():
            if "fontSize" in entry:
                named_style_sizes[style_name] = entry["fontSize"]
            if "color" in entry:
                named_style_colors[style_name] = entry["color"]
            if "font" in entry:
                named_style_fonts[style_name] = entry["font"]

        return cls(
            default_font=default_font,
            default_font_size=default_font_size,
            default_fg_color="#000000",
            default_link_color=default_link_color,
            named_style_sizes=named_style_sizes,
            named_style_colors=named_style_colors,
            named_style_fonts=named_style_fonts,
            date_defaults=date_defaults,
            document_id=metadata.get("documentId"),
            tab_id=metadata.get("tabId"),
        )

    def expected_font_size(self, style_name: str | None) -> float | None:
        """Return the expected font size for a named style, falling back to default."""
        if style_name and style_name in self.named_style_sizes:
            return self.named_style_sizes[style_name]
        return self.default_font_size

    def expected_color(self, style_name: str | None) -> str:
        """Return the expected foreground color for a named style, falling back to default."""
        if style_name and style_name in self.named_style_colors:
            color = self.named_style_colors[style_name]
            if color is not None:
                return color
        return self.default_fg_color

    def expected_font(self, style_name: str | None) -> str | None:
        """Return the expected font family for a named style, falling back to default."""
        if style_name and style_name in self.named_style_fonts:
            font = self.named_style_fonts[style_name]
            if font is not None:
                return font
        return self.default_font


@dataclass
class SerContext:
    """Mutable serialization context passed to handlers."""

    doc: DocumentContext
    current_para_style: str | None = None
    footnote_refs: list[tuple[str, str]] = field(default_factory=list)
    date_defaults: dict[str, str] | None = None
    inline_objects: dict[str, Any] | None = None
    lists_context: dict[str, Any] | None = None
    body_content: list[StructuralElement] | None = None
    document_id: str | None = None
    tab_id: str | None = None
    pending_style_props: dict[str, Any] | None = None

    collect_paragraph_text: Callable[[list[ParagraphElement]], str] | None = None
    visit_block: Callable[[Any], str | None] | None = None


@dataclass
class DeserContext:
    """Mutable deserialization context passed to handlers."""

    doc: DocumentContext
    index: int = 1
    tab_id: str = ""
    segment_id: str = ""
    requests: list[Any] = field(default_factory=list)

    def advance(self, length: int) -> None:
        """Move the insertion index forward by *length* characters."""
        self.index += length

    def emit(self, *reqs: Any) -> None:
        """Append one or more API requests to the accumulator."""
        self.requests.extend(reqs)
