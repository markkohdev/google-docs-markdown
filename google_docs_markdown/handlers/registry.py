"""Handler registry for dispatching elements to their handlers."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.handlers.base import ElementHandler


class HandlerRegistry:
    """Indexes handlers and dispatches elements/tokens to the matching handler.

    Maintains three ordered handler lists for three dispatch levels:

    * **paragraph_element** — ``ParagraphElement`` inline items (person, date, text run, …)
    * **structural** — ``StructuralElement`` items (table, section break, TOC)
    * **block** — composite blocks from the block grouper (``ListBlock``, ``CodeBlock``)
    """

    def __init__(
        self,
        paragraph_element_handlers: list[ElementHandler] | None = None,
        structural_handlers: list[ElementHandler] | None = None,
        block_handlers: list[ElementHandler] | None = None,
    ) -> None:
        self._para_handlers = list(paragraph_element_handlers or [])
        self._struct_handlers = list(structural_handlers or [])
        self._block_handlers = list(block_handlers or [])
        self._all_handlers = self._para_handlers + self._struct_handlers + self._block_handlers

    def match_paragraph_element(self, element: Any) -> ElementHandler | None:
        """Find the handler for a ``ParagraphElement``."""
        for h in self._para_handlers:
            if h.serialize_match(element):
                return h
        return None

    def match_structural(self, element: Any) -> ElementHandler | None:
        """Find the handler for a ``StructuralElement``."""
        for h in self._struct_handlers:
            if h.serialize_match(element):
                return h
        return None

    def match_block(self, block: Any) -> ElementHandler | None:
        """Find the handler for a composite ``Block``."""
        for h in self._block_handlers:
            if h.serialize_match(block):
                return h
        return None

    def match_deserialize(self, token: Any) -> ElementHandler | None:
        """Find the handler for a Markdown AST token or parsed tag."""
        for h in self._all_handlers:
            if h.deserialize_match(token):
                return h
        return None

    def get_handler(self, handler_type: type) -> ElementHandler | None:
        """Look up a handler by its class (useful for direct access)."""
        for h in self._all_handlers:
            if isinstance(h, handler_type):
                return h
        return None

    @classmethod
    def default(cls) -> HandlerRegistry:
        """Build a registry with all built-in handlers."""
        from google_docs_markdown.handlers.breaks import (
            AutoTextHandler,
            ColumnBreakHandler,
            EquationHandler,
            HorizontalRuleHandler,
            PageBreakHandler,
            SectionBreakHandler,
        )
        from google_docs_markdown.handlers.code_block import CodeBlockHandler
        from google_docs_markdown.handlers.date import DateHandler
        from google_docs_markdown.handlers.footnote import FootnoteRefHandler
        from google_docs_markdown.handlers.image import ImageHandler
        from google_docs_markdown.handlers.list_handler import ListHandler
        from google_docs_markdown.handlers.person import PersonHandler
        from google_docs_markdown.handlers.rich_link import RichLinkHandler
        from google_docs_markdown.handlers.style import StyleHandler
        from google_docs_markdown.handlers.suggestion import SuggestionHandler
        from google_docs_markdown.handlers.table import TableHandler
        from google_docs_markdown.handlers.text_run import TextRunHandler
        from google_docs_markdown.handlers.toc import TableOfContentsHandler

        paragraph_element_handlers: list[ElementHandler] = [
            PersonHandler(),
            DateHandler(),
            RichLinkHandler(),
            FootnoteRefHandler(),
            ImageHandler(),
            HorizontalRuleHandler(),
            PageBreakHandler(),
            ColumnBreakHandler(),
            AutoTextHandler(),
            EquationHandler(),
            StyleHandler(),
            SuggestionHandler(),
            TextRunHandler(),
        ]

        structural_handlers: list[ElementHandler] = [
            TableHandler(),
            SectionBreakHandler(),
            TableOfContentsHandler(),
        ]

        block_handlers: list[ElementHandler] = [
            ListHandler(),
            CodeBlockHandler(),
        ]

        return cls(
            paragraph_element_handlers=paragraph_element_handlers,
            structural_handlers=structural_handlers,
            block_handlers=block_handlers,
        )


__all__ = ["HandlerRegistry"]
