"""PersonHandler — ``<!-- person: {"email": "..."} -->Name<!-- /person -->``."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, wrap_tag
from google_docs_markdown.handlers.base import TagElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.common import Location, PersonProperties
from google_docs_markdown.models.requests import InsertPersonRequest, Request


class PersonHandler(TagElementHandler):
    TAG_TYPE = TagType.PERSON

    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "person") and element.person is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        person = element.person
        props = person.personProperties
        if not props:
            return None
        name = props.name or props.email or ""
        data: dict[str, Any] = {}
        if props.email:
            data["email"] = props.email
        return wrap_tag(TagType.PERSON, name, data)

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        data = token.data or {}
        email = data.get("email")
        if not email:
            return []
        return [
            Request(
                insertPerson=InsertPersonRequest(
                    personProperties=PersonProperties(email=email),
                    location=Location(
                        index=ctx.index,
                        segmentId=ctx.segment_id or None,
                        tabId=ctx.tab_id or None,
                    ),
                )
            )
        ]
