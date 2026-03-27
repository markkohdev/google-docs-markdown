"""StyleHandler — non-default style extraction for ``<!-- style -->`` wrapping."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import SerContext, optional_color_to_hex
from google_docs_markdown.models.styles import TextStyle

_HEADING_STYLES = frozenset(
    {"TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6"}
)


class StyleHandler(TagElementHandler):
    TAG_TYPE = TagType.STYLE

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    @staticmethod
    def extract_non_default_style(style: TextStyle | None, ctx: SerContext) -> dict[str, Any] | None:
        """Return a dict of non-default style properties, or None if all defaults.

        For heading paragraphs, font-size is always suppressed.
        Colors and fonts are compared against the named style defaults.
        """
        if not style:
            return None

        props: dict[str, Any] = {}
        doc = ctx.doc
        para = ctx.current_para_style
        is_heading = para in _HEADING_STYLES

        fg = optional_color_to_hex(style.foregroundColor)
        if fg and style.link and style.link.url:
            if fg == doc.default_link_color:
                fg = None
        if fg:
            expected_color = doc.expected_color(para)
            if fg != expected_color:
                props["color"] = fg

        bg = optional_color_to_hex(style.backgroundColor)
        if bg:
            props["background-color"] = bg

        if not is_heading and style.fontSize and style.fontSize.magnitude is not None:
            expected_size = doc.expected_font_size(para)
            if style.fontSize.magnitude != expected_size:
                props["font-size"] = style.fontSize.magnitude

        if style.weightedFontFamily and style.weightedFontFamily.fontFamily:
            font = style.weightedFontFamily.fontFamily
            expected_font = doc.expected_font(para)
            if font != expected_font:
                props["font-family"] = font

        if style.baselineOffset and style.baselineOffset not in (
            "BASELINE_OFFSET_UNSPECIFIED",
            "NONE",
        ):
            props["baseline-offset"] = style.baselineOffset

        if style.smallCaps:
            props["small-caps"] = True

        return props or None
