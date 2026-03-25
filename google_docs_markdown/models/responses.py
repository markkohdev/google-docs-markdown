"""Generated Pydantic models for Google Docs API."""

from __future__ import annotations

from google_docs_markdown.models.base import GoogleDocsBaseModel


class Response(GoogleDocsBaseModel):
    """Response model from Google Docs API."""

    createFooter: CreateFooterResponse | None = None
    createFootnote: CreateFootnoteResponse | None = None
    createHeader: CreateHeaderResponse | None = None
    createNamedRange: CreateNamedRangeResponse | None = None
    insertInlineImage: InsertInlineImageResponse | None = None
    insertInlineSheetsChart: InsertInlineSheetsChartResponse | None = None
    replaceAllText: ReplaceAllTextResponse | None = None


class BatchUpdateDocumentResponse(GoogleDocsBaseModel):
    """BatchUpdateDocumentResponse model from Google Docs API."""

    documentId: str | None = None
    replies: list[Response] | None = None
    writeControl: WriteControl | None = None


class CreateFooterResponse(GoogleDocsBaseModel):
    """CreateFooterResponse model from Google Docs API."""

    footerId: str | None = None


class CreateHeaderResponse(GoogleDocsBaseModel):
    """CreateHeaderResponse model from Google Docs API."""

    headerId: str | None = None


class CreateFootnoteResponse(GoogleDocsBaseModel):
    """CreateFootnoteResponse model from Google Docs API."""

    footnoteId: str | None = None


class CreateNamedRangeResponse(GoogleDocsBaseModel):
    """CreateNamedRangeResponse model from Google Docs API."""

    namedRangeId: str | None = None


class InsertInlineImageResponse(GoogleDocsBaseModel):
    """InsertInlineImageResponse model from Google Docs API."""

    objectId: str | None = None


class InsertInlineSheetsChartResponse(GoogleDocsBaseModel):
    """InsertInlineSheetsChartResponse model from Google Docs API."""

    objectId: str | None = None


class ReplaceAllTextResponse(GoogleDocsBaseModel):
    """ReplaceAllTextResponse model from Google Docs API."""

    occurrencesChanged: int | None = None
