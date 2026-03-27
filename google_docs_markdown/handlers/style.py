"""StyleHandler — non-default style extraction for ``<!-- style -->`` wrapping."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType
from google_docs_markdown.element_registry import HEADING_STYLES
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext, optional_color_to_hex
from google_docs_markdown.models.styles import TextStyle


class StyleHandler(TagElementHandler):
    TAG_TYPE = TagType.STYLE

    def serialize_match(self, element: Any) -> bool:
        return False

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        return None

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        from google_docs_markdown.models.common import (
            Color,
            Location,
            OptionalColor,
            Range,
            RgbColor,
        )
        from google_docs_markdown.models.requests import (
            InsertTextRequest,
            Request,
            UpdateTextStyleRequest,
        )

        data = getattr(token, "data", None) or {}
        content = getattr(token, "content", "") or ""
        if not content:
            return []

        start_index = ctx.index
        requests: list[Any] = [
            Request(
                insertText=InsertTextRequest(
                    text=content,
                    location=Location(
                        index=start_index,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                )
            )
        ]
        ctx.advance(len(content))

        style_kwargs: dict[str, Any] = {}
        fields: list[str] = []

        if "color" in data:
            hex_color = data["color"]
            r = int(hex_color[1:3], 16) / 255.0
            g = int(hex_color[3:5], 16) / 255.0
            b = int(hex_color[5:7], 16) / 255.0
            style_kwargs["foregroundColor"] = OptionalColor(color=Color(rgbColor=RgbColor(red=r, green=g, blue=b)))
            fields.append("foregroundColor")

        if "background-color" in data:
            hex_color = data["background-color"]
            r = int(hex_color[1:3], 16) / 255.0
            g = int(hex_color[3:5], 16) / 255.0
            b = int(hex_color[5:7], 16) / 255.0
            style_kwargs["backgroundColor"] = OptionalColor(color=Color(rgbColor=RgbColor(red=r, green=g, blue=b)))
            fields.append("backgroundColor")

        if "font-size" in data:
            from google_docs_markdown.models.common import Dimension

            style_kwargs["fontSize"] = Dimension(magnitude=data["font-size"], unit="PT")
            fields.append("fontSize")

        if "font-family" in data:
            from google_docs_markdown.models.common import WeightedFontFamily

            style_kwargs["weightedFontFamily"] = WeightedFontFamily(fontFamily=data["font-family"])
            fields.append("weightedFontFamily")

        if "baseline-offset" in data:
            style_kwargs["baselineOffset"] = data["baseline-offset"]
            fields.append("baselineOffset")

        if "small-caps" in data:
            style_kwargs["smallCaps"] = True
            fields.append("smallCaps")

        if fields:
            requests.append(
                Request(
                    updateTextStyle=UpdateTextStyleRequest(
                        range=Range(
                            startIndex=start_index,
                            endIndex=start_index + len(content),
                            segmentId=ctx.segment_id or None,
                            tabId=ctx.tab_id or None,
                        ),
                        textStyle=TextStyle(**style_kwargs),
                        fields=",".join(fields),
                    )
                )
            )

        return requests

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
        is_heading = para in HEADING_STYLES

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
