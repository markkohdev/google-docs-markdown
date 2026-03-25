"""Generated Pydantic models for Google Docs API."""

from __future__ import annotations

from typing import Literal

from google_docs_markdown.models.base import GoogleDocsBaseModel


class Request(GoogleDocsBaseModel):
    """Request model from Google Docs API."""

    createFooter: CreateFooterRequest | None = None
    createFootnote: CreateFootnoteRequest | None = None
    createHeader: CreateHeaderRequest | None = None
    createNamedRange: CreateNamedRangeRequest | None = None
    createParagraphBullets: CreateParagraphBulletsRequest | None = None
    deleteContentRange: DeleteContentRangeRequest | None = None
    deleteFooter: DeleteFooterRequest | None = None
    deleteHeader: DeleteHeaderRequest | None = None
    deleteNamedRange: DeleteNamedRangeRequest | None = None
    deleteParagraphBullets: DeleteParagraphBulletsRequest | None = None
    deletePositionedObject: DeletePositionedObjectRequest | None = None
    deleteTableColumn: DeleteTableColumnRequest | None = None
    deleteTableRow: DeleteTableRowRequest | None = None
    insertInlineImage: InsertInlineImageRequest | None = None
    insertPageBreak: InsertPageBreakRequest | None = None
    insertPerson: InsertPersonRequest | None = None
    insertSectionBreak: InsertSectionBreakRequest | None = None
    insertTable: InsertTableRequest | None = None
    insertTableColumn: InsertTableColumnRequest | None = None
    insertTableRow: InsertTableRowRequest | None = None
    insertText: InsertTextRequest | None = None
    mergeTableCells: MergeTableCellsRequest | None = None
    pinTableHeaderRows: PinTableHeaderRowsRequest | None = None
    replaceAllText: ReplaceAllTextRequest | None = None
    replaceImage: ReplaceImageRequest | None = None
    replaceNamedRangeContent: ReplaceNamedRangeContentRequest | None = None
    unmergeTableCells: UnmergeTableCellsRequest | None = None
    updateDocumentStyle: UpdateDocumentStyleRequest | None = None
    updateParagraphStyle: UpdateParagraphStyleRequest | None = None
    updateSectionStyle: UpdateSectionStyleRequest | None = None
    updateTableCellStyle: UpdateTableCellStyleRequest | None = None
    updateTableColumnProperties: UpdateTableColumnPropertiesRequest | None = None
    updateTableRowStyle: UpdateTableRowStyleRequest | None = None
    updateTextStyle: UpdateTextStyleRequest | None = None


class BatchUpdateDocumentRequest(GoogleDocsBaseModel):
    """BatchUpdateDocumentRequest model from Google Docs API."""

    requests: list[Request] | None = None
    writeControl: WriteControl | None = None


class CreateFooterRequest(GoogleDocsBaseModel):
    """CreateFooterRequest model from Google Docs API."""

    sectionBreakLocation: Location | None = None
    type: Literal["HEADER_FOOTER_TYPE_UNSPECIFIED", "DEFAULT"] | None = None


class CreateHeaderRequest(GoogleDocsBaseModel):
    """CreateHeaderRequest model from Google Docs API."""

    sectionBreakLocation: Location | None = None
    type: Literal["HEADER_FOOTER_TYPE_UNSPECIFIED", "DEFAULT"] | None = None


class CreateFootnoteRequest(GoogleDocsBaseModel):
    """CreateFootnoteRequest model from Google Docs API."""

    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None


class CreateNamedRangeRequest(GoogleDocsBaseModel):
    """CreateNamedRangeRequest model from Google Docs API."""

    name: str | None = None
    range: Range | None = None


class CreateParagraphBulletsRequest(GoogleDocsBaseModel):
    """CreateParagraphBulletsRequest model from Google Docs API."""

    bulletPreset: (
        Literal[
            "BULLET_GLYPH_PRESET_UNSPECIFIED",
            "BULLET_DISC_CIRCLE_SQUARE",
            "BULLET_DIAMONDX_ARROW3D_SQUARE",
            "BULLET_CHECKBOX",
            "BULLET_ARROW_DIAMOND_DISC",
            "BULLET_STAR_CIRCLE_SQUARE",
            "BULLET_ARROW3D_CIRCLE_SQUARE",
            "BULLET_LEFTTRIANGLE_DIAMOND_DISC",
            "BULLET_DIAMONDX_HOLLOWDIAMOND_SQUARE",
            "BULLET_DIAMOND_CIRCLE_SQUARE",
            "NUMBERED_DECIMAL_ALPHA_ROMAN",
            "NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS",
            "NUMBERED_DECIMAL_NESTED",
            "NUMBERED_UPPERALPHA_ALPHA_ROMAN",
            "NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL",
            "NUMBERED_ZERODECIMAL_ALPHA_ROMAN",
        ]
        | None
    ) = None
    range: Range | None = None


class DeleteContentRangeRequest(GoogleDocsBaseModel):
    """DeleteContentRangeRequest model from Google Docs API."""

    range: Range | None = None


class DeleteFooterRequest(GoogleDocsBaseModel):
    """DeleteFooterRequest model from Google Docs API."""

    footerId: str | None = None
    tabId: str | None = None


class DeleteHeaderRequest(GoogleDocsBaseModel):
    """DeleteHeaderRequest model from Google Docs API."""

    headerId: str | None = None
    tabId: str | None = None


class DeleteNamedRangeRequest(GoogleDocsBaseModel):
    """DeleteNamedRangeRequest model from Google Docs API."""

    name: str | None = None
    namedRangeId: str | None = None
    tabsCriteria: TabsCriteria | None = None


class DeleteParagraphBulletsRequest(GoogleDocsBaseModel):
    """DeleteParagraphBulletsRequest model from Google Docs API."""

    range: Range | None = None


class DeletePositionedObjectRequest(GoogleDocsBaseModel):
    """DeletePositionedObjectRequest model from Google Docs API."""

    objectId: str | None = None
    tabId: str | None = None


class DeleteTableColumnRequest(GoogleDocsBaseModel):
    """DeleteTableColumnRequest model from Google Docs API."""

    tableCellLocation: TableCellLocation | None = None


class DeleteTableRowRequest(GoogleDocsBaseModel):
    """DeleteTableRowRequest model from Google Docs API."""

    tableCellLocation: TableCellLocation | None = None


class InsertInlineImageRequest(GoogleDocsBaseModel):
    """InsertInlineImageRequest model from Google Docs API."""

    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None
    objectSize: Size | None = None
    uri: str | None = None


class InsertPageBreakRequest(GoogleDocsBaseModel):
    """InsertPageBreakRequest model from Google Docs API."""

    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None


class InsertPersonRequest(GoogleDocsBaseModel):
    """InsertPersonRequest model from Google Docs API."""

    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None
    personProperties: PersonProperties | None = None


class InsertSectionBreakRequest(GoogleDocsBaseModel):
    """InsertSectionBreakRequest model from Google Docs API."""

    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None
    sectionType: Literal["SECTION_TYPE_UNSPECIFIED", "CONTINUOUS", "NEXT_PAGE"] | None = None


class InsertTableRequest(GoogleDocsBaseModel):
    """InsertTableRequest model from Google Docs API."""

    columns: int | None = None
    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None
    rows: int | None = None


class InsertTableColumnRequest(GoogleDocsBaseModel):
    """InsertTableColumnRequest model from Google Docs API."""

    insertRight: bool | None = None
    tableCellLocation: TableCellLocation | None = None


class InsertTableRowRequest(GoogleDocsBaseModel):
    """InsertTableRowRequest model from Google Docs API."""

    insertBelow: bool | None = None
    tableCellLocation: TableCellLocation | None = None


class InsertTextRequest(GoogleDocsBaseModel):
    """InsertTextRequest model from Google Docs API."""

    endOfSegmentLocation: EndOfSegmentLocation | None = None
    location: Location | None = None
    text: str | None = None


class MergeTableCellsRequest(GoogleDocsBaseModel):
    """MergeTableCellsRequest model from Google Docs API."""

    tableRange: TableRange | None = None


class PinTableHeaderRowsRequest(GoogleDocsBaseModel):
    """PinTableHeaderRowsRequest model from Google Docs API."""

    pinnedHeaderRowsCount: int | None = None
    tableStartLocation: Location | None = None


class ReplaceAllTextRequest(GoogleDocsBaseModel):
    """ReplaceAllTextRequest model from Google Docs API."""

    containsText: SubstringMatchCriteria | None = None
    replaceText: str | None = None
    tabsCriteria: TabsCriteria | None = None


class ReplaceImageRequest(GoogleDocsBaseModel):
    """ReplaceImageRequest model from Google Docs API."""

    imageObjectId: str | None = None
    imageReplaceMethod: Literal["IMAGE_REPLACE_METHOD_UNSPECIFIED", "CENTER_CROP"] | None = None
    tabId: str | None = None
    uri: str | None = None


class ReplaceNamedRangeContentRequest(GoogleDocsBaseModel):
    """ReplaceNamedRangeContentRequest model from Google Docs API."""

    namedRangeId: str | None = None
    namedRangeName: str | None = None
    tabsCriteria: TabsCriteria | None = None
    text: str | None = None


class UnmergeTableCellsRequest(GoogleDocsBaseModel):
    """UnmergeTableCellsRequest model from Google Docs API."""

    tableRange: TableRange | None = None


class UpdateDocumentStyleRequest(GoogleDocsBaseModel):
    """UpdateDocumentStyleRequest model from Google Docs API."""

    documentStyle: DocumentStyle | None = None
    fields: str | None = None
    tabId: str | None = None


class UpdateParagraphStyleRequest(GoogleDocsBaseModel):
    """UpdateParagraphStyleRequest model from Google Docs API."""

    fields: str | None = None
    paragraphStyle: ParagraphStyle | None = None
    range: Range | None = None


class UpdateSectionStyleRequest(GoogleDocsBaseModel):
    """UpdateSectionStyleRequest model from Google Docs API."""

    fields: str | None = None
    range: Range | None = None
    sectionStyle: SectionStyle | None = None


class UpdateTableCellStyleRequest(GoogleDocsBaseModel):
    """UpdateTableCellStyleRequest model from Google Docs API."""

    fields: str | None = None
    tableCellStyle: TableCellStyle | None = None
    tableRange: TableRange | None = None
    tableStartLocation: Location | None = None


class UpdateTableColumnPropertiesRequest(GoogleDocsBaseModel):
    """UpdateTableColumnPropertiesRequest model from Google Docs API."""

    columnIndices: list[int] | None = None
    fields: str | None = None
    tableColumnProperties: TableColumnProperties | None = None
    tableStartLocation: Location | None = None


class UpdateTableRowStyleRequest(GoogleDocsBaseModel):
    """UpdateTableRowStyleRequest model from Google Docs API."""

    fields: str | None = None
    rowIndices: list[int] | None = None
    tableRowStyle: TableRowStyle | None = None
    tableStartLocation: Location | None = None


class UpdateTextStyleRequest(GoogleDocsBaseModel):
    """UpdateTextStyleRequest model from Google Docs API."""

    fields: str | None = None
    range: Range | None = None
    textStyle: TextStyle | None = None
