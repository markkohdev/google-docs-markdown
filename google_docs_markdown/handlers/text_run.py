"""TextRunHandler — processes TextRun elements with all inline formatting."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.comment_tags import TagType, wrap_tag
from google_docs_markdown.handlers.base import ElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.handlers.inline_format import InlineCodeHandler
from google_docs_markdown.handlers.style import StyleHandler

_CHIP_PLACEHOLDER = "<!-- chip-placeholder -->"


def _split_whitespace(text: str) -> tuple[str, str, str]:
    """Split *text* into ``(leading_ws, inner, trailing_ws)``."""
    stripped = text.lstrip()
    leading = text[: len(text) - len(stripped)]
    inner = stripped.rstrip()
    trailing = stripped[len(inner) :]
    return leading, inner, trailing


def _apply_inline_formatting(
    text: str,
    *,
    bold: bool,
    italic: bool,
    strikethrough: bool = False,
    underline: bool = False,
) -> str:
    """Wrap text in Markdown formatting markers, preserving surrounding whitespace."""
    if not text or (not bold and not italic and not strikethrough and not underline):
        return text

    leading, inner, trailing = _split_whitespace(text)
    if not inner:
        return text

    if bold and italic:
        inner = f"***{inner}***"
    elif bold:
        inner = f"**{inner}**"
    elif italic:
        inner = f"*{inner}*"

    if strikethrough:
        inner = f"~~{inner}~~"

    if underline:
        inner = f"<u>{inner}</u>"

    return f"{leading}{inner}{trailing}"


def _apply_link(text: str, url: str) -> str:
    """Wrap text in a Markdown link, preserving surrounding whitespace."""
    if not text:
        return text
    leading, inner, trailing = _split_whitespace(text)
    if not inner:
        return text
    return f"{leading}[{inner}]({url}){trailing}"


def _apply_backtick_wrap(text: str) -> str:
    """Wrap text in backtick delimiters for inline code, preserving whitespace."""
    if not text:
        return text
    leading, inner, trailing = _split_whitespace(text)
    if not inner:
        return text
    if "`" not in inner:
        return f"{leading}`{inner}`{trailing}"
    return f"{leading}`` {inner} ``{trailing}"


class TextRunHandler(ElementHandler):
    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "textRun") and element.textRun is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        text_run = element.textRun
        content = text_run.content
        if content is None:
            return None

        content = content.replace("\ue907", _CHIP_PLACEHOLDER)
        if not content:
            return None

        has_chip = _CHIP_PLACEHOLDER in content

        style = text_run.textStyle
        bold = style and style.bold
        italic = style and style.italic
        strikethrough = style and style.strikethrough
        link = style and style.link
        underline = style and style.underline and not link

        has_formatting = bold or italic or strikethrough or underline
        if has_formatting and not has_chip:
            content = _apply_inline_formatting(
                content,
                bold=bool(bold),
                italic=bool(italic),
                strikethrough=bool(strikethrough),
                underline=bool(underline),
            )
        elif has_formatting and has_chip:
            parts = content.split(_CHIP_PLACEHOLDER)
            formatted_parts = []
            for part in parts:
                if part:
                    part = _apply_inline_formatting(
                        part,
                        bold=bool(bold),
                        italic=bool(italic),
                        strikethrough=bool(strikethrough),
                        underline=bool(underline),
                    )
                formatted_parts.append(part)
            content = _CHIP_PLACEHOLDER.join(formatted_parts)

        if link and link.url:
            content = _apply_link(content, link.url)

        style_props = StyleHandler.extract_non_default_style(style, ctx)

        if InlineCodeHandler.is_inline_code_style(style) and text_run.content and text_run.content.strip():
            content = _apply_backtick_wrap(content)
            if style_props:
                for key in ("color", "font-family", "font-size"):
                    style_props.pop(key, None)
                if not style_props:
                    style_props = None

        if not (text_run.content and text_run.content.strip()):
            style_props = None
        ctx.pending_style_props = style_props

        if text_run.suggestedInsertionIds:
            suggestion_id = text_run.suggestedInsertionIds[0]
            content = wrap_tag(
                TagType.SUGGESTION,
                content,
                {"id": suggestion_id, "type": "insertion"},
            )
        elif text_run.suggestedDeletionIds:
            suggestion_id = text_run.suggestedDeletionIds[0]
            content = wrap_tag(
                TagType.SUGGESTION,
                content,
                {"id": suggestion_id, "type": "deletion"},
            )

        result: str = content
        return result

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
