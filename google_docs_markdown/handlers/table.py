"""TableHandler — Markdown pipe tables."""

from __future__ import annotations

from typing import Any

from google_docs_markdown.handlers.base import BlockElementHandler
from google_docs_markdown.handlers.context import DeserContext, SerContext
from google_docs_markdown.models.elements import TableCell


def _escape_pipe(text: str) -> str:
    """Escape literal pipe characters so they don't break table structure."""
    return text.replace("|", "\\|")


class TableHandler(BlockElementHandler):
    def serialize_match(self, element: Any) -> bool:
        return hasattr(element, "table") and element.table is not None

    def serialize(self, element: Any, ctx: SerContext) -> str | None:
        table = element.table
        if not table.tableRows:
            return None

        rows: list[list[str]] = []
        header_row_count = 0

        for row in table.tableRows:
            cells: list[str] = []
            for cell in row.tableCells or []:
                cells.append(self._serialize_cell_content(cell, ctx))
            rows.append(cells)
            if row.tableRowStyle and row.tableRowStyle.tableHeader:
                header_row_count += 1

        if not rows:
            return None

        col_count = table.columns or (max(len(r) for r in rows) if rows else 0)
        for r in rows:
            while len(r) < col_count:
                r.append("")

        separator = "| " + " | ".join("---" for _ in range(col_count)) + " |"

        lines: list[str] = []
        for i, r in enumerate(rows):
            line = "| " + " | ".join(r) + " |"
            lines.append(line)
            if i == max(header_row_count - 1, 0):
                lines.append(separator)

        return "\n".join(lines)

    def _serialize_cell_content(self, cell: TableCell, ctx: SerContext) -> str:
        if not cell.content:
            return ""
        if ctx.collect_paragraph_text is None:
            return ""

        parts: list[str] = []
        for element in cell.content:
            if element.paragraph:
                text = ctx.collect_paragraph_text(element.paragraph.elements or [])
                if text:
                    parts.append(text)

        result = "<br>".join(parts)
        return _escape_pipe(result)

    def deserialize_match(self, token: Any) -> bool:
        return False

    def deserialize(self, token: Any, ctx: DeserContext) -> list[Any]:
        return []
