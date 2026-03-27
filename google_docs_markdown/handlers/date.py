"""DateHandler — ``<!-- date: {...} -->displayText<!-- /date -->``."""

from __future__ import annotations

from typing import Any, cast

from google_docs_markdown.comment_tags import TagType, wrap_tag
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import Location
from google_docs_markdown.models.elements import DateElementProperties
from google_docs_markdown.models.requests import InsertDateRequest, Request


class DateHandler(TagElementHandler):
    TAG_TYPE = TagType.DATE

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "dateElement") and element.dateElement is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        date_elem = element.dateElement
        props = date_elem.dateElementProperties
        if not props:
            return None
        display = props.displayText or ""

        format_props: dict[str, str] = {}
        if props.dateFormat:
            format_props["format"] = props.dateFormat
        if props.locale:
            format_props["locale"] = props.locale
        if props.timeFormat:
            format_props["timeFormat"] = props.timeFormat
        if props.timeZoneId:
            format_props["timeZoneId"] = props.timeZoneId

        if ctx.date_defaults is None and format_props:
            ctx.date_defaults = format_props

        inline_data: dict[str, Any] = {}
        if ctx.date_defaults:
            for key, value in format_props.items():
                if ctx.date_defaults.get(key) != value:
                    inline_data[key] = value
        else:
            inline_data.update(format_props)

        if props.timestamp and not (display and props.timestamp.startswith(display)):
            inline_data["timestamp"] = props.timestamp

        return wrap_tag(TagType.DATE, display, inline_data or None)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        data = token.data or {}

        date_defaults = ctx.doc.date_defaults or {}
        merged = dict(date_defaults)
        merged.update(data)

        date_props = DateElementProperties(
            dateFormat=cast(Any, merged.get("format")),
            locale=merged.get("locale"),
            timeFormat=cast(Any, merged.get("timeFormat")),
            timeZoneId=merged.get("timeZoneId"),
            timestamp=merged.get("timestamp"),
        )

        return [
            Request(
                insertDate=InsertDateRequest(
                    dateElementProperties=date_props,
                    location=Location(
                        index=ctx.index,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                )
            )
        ]
