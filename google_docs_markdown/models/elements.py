"""Generated Pydantic models for Google Docs API."""

from __future__ import annotations

from typing import Any, Literal

from google_docs_markdown.models.base import GoogleDocsBaseModel


class StructuralElement(GoogleDocsBaseModel):
    """StructuralElement model from Google Docs API."""

    endIndex: int | None = None
    paragraph: Paragraph | None = None
    sectionBreak: SectionBreak | None = None
    startIndex: int | None = None
    table: Table | None = None
    tableOfContents: TableOfContents | None = None


class Paragraph(GoogleDocsBaseModel):
    """Paragraph model from Google Docs API."""

    bullet: Bullet | None = None
    elements: list[ParagraphElement] | None = None
    paragraphStyle: ParagraphStyle | None = None
    positionedObjectIds: list[str] | None = None
    suggestedBulletChanges: dict[str, Any] | None = None
    suggestedParagraphStyleChanges: dict[str, Any] | None = None
    suggestedPositionedObjectIds: dict[str, Any] | None = None


class Table(GoogleDocsBaseModel):
    """Table model from Google Docs API."""

    columns: int | None = None
    rows: int | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    tableRows: list[TableRow] | None = None
    tableStyle: TableStyle | None = None


class TableOfContents(GoogleDocsBaseModel):
    """TableOfContents model from Google Docs API."""

    content: list[StructuralElement] | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None


class SectionBreak(GoogleDocsBaseModel):
    """SectionBreak model from Google Docs API."""

    sectionStyle: SectionStyle | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None


class TableRow(GoogleDocsBaseModel):
    """TableRow model from Google Docs API."""

    endIndex: int | None = None
    startIndex: int | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTableRowStyleChanges: dict[str, Any] | None = None
    tableCells: list[TableCell] | None = None
    tableRowStyle: TableRowStyle | None = None


class TableCell(GoogleDocsBaseModel):
    """TableCell model from Google Docs API."""

    content: list[StructuralElement] | None = None
    endIndex: int | None = None
    startIndex: int | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTableCellStyleChanges: dict[str, Any] | None = None
    tableCellStyle: TableCellStyle | None = None


class ParagraphElement(GoogleDocsBaseModel):
    """ParagraphElement model from Google Docs API."""

    autoText: AutoText | None = None
    columnBreak: ColumnBreak | None = None
    endIndex: int | None = None
    equation: Equation | None = None
    footnoteReference: FootnoteReference | None = None
    horizontalRule: HorizontalRule | None = None
    inlineObjectElement: InlineObjectElement | None = None
    pageBreak: PageBreak | None = None
    person: Person | None = None
    richLink: RichLink | None = None
    startIndex: int | None = None
    textRun: TextRun | None = None


class TextRun(GoogleDocsBaseModel):
    """TextRun model from Google Docs API."""

    content: str | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class AutoText(GoogleDocsBaseModel):
    """AutoText model from Google Docs API."""

    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None
    type: Literal["TYPE_UNSPECIFIED", "PAGE_NUMBER", "PAGE_COUNT"] | None = None


class ColumnBreak(GoogleDocsBaseModel):
    """ColumnBreak model from Google Docs API."""

    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class PageBreak(GoogleDocsBaseModel):
    """PageBreak model from Google Docs API."""

    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class HorizontalRule(GoogleDocsBaseModel):
    """HorizontalRule model from Google Docs API."""

    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class Equation(GoogleDocsBaseModel):
    """Equation model from Google Docs API."""

    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None


class FootnoteReference(GoogleDocsBaseModel):
    """FootnoteReference model from Google Docs API."""

    footnoteId: str | None = None
    footnoteNumber: str | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class Person(GoogleDocsBaseModel):
    """Person model from Google Docs API."""

    personId: str | None = None
    personProperties: PersonProperties | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class RichLink(GoogleDocsBaseModel):
    """RichLink model from Google Docs API."""

    richLinkId: str | None = None
    richLinkProperties: RichLinkProperties | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None


class InlineObjectElement(GoogleDocsBaseModel):
    """InlineObjectElement model from Google Docs API."""

    inlineObjectId: str | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedTextStyleChanges: dict[str, Any] | None = None
    textStyle: TextStyle | None = None
