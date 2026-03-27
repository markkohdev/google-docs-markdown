"""CodeBlockHandler — fenced code blocks from U+E907 boundaries."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.block_grouper import CodeBlock
from google_docs_markdown.handlers.base import BlockElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext


class CodeBlockHandler(BlockElementHandler):
    def serialize_match(self, element: Any) -> bool:
        return isinstance(element, CodeBlock)

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        block: CodeBlock = element
        lines: list[str] = []
        for para in block.paragraphs:
            line_parts: list[str] = []
            for elem in para.elements or []:
                if elem.textRun and elem.textRun.content:
                    line_parts.append(elem.textRun.content)
            raw = "".join(line_parts)
            raw = raw.replace("\ue907", "")
            raw = raw.rstrip("\n")
            if raw:
                lines.append(raw)
        return "```\n" + "\n".join(lines) + "\n```"

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
