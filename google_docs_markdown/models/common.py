"""Generated Pydantic models for Google Docs API."""

from __future__ import annotations

from typing import Any, List, Literal

from google_docs_markdown.models.base import GoogleDocsBaseModel


class Color(GoogleDocsBaseModel):
    """Color model from Google Docs API."""

    rgbColor: RgbColor | None = None


class OptionalColor(GoogleDocsBaseModel):
    """OptionalColor model from Google Docs API."""

    color: Color | None = None


class RgbColor(GoogleDocsBaseModel):
    """RgbColor model from Google Docs API."""

    blue: float | None = None
    green: float | None = None
    red: float | None = None


class Background(GoogleDocsBaseModel):
    """Background model from Google Docs API."""

    color: OptionalColor | None = None


class Shading(GoogleDocsBaseModel):
    """Shading model from Google Docs API."""

    backgroundColor: OptionalColor | None = None


class Dimension(GoogleDocsBaseModel):
    """Dimension model from Google Docs API."""

    magnitude: float | None = None
    unit: Literal["UNIT_UNSPECIFIED", "PT"] | None = None


class Size(GoogleDocsBaseModel):
    """Size model from Google Docs API."""

    height: Dimension | None = None
    width: Dimension | None = None


class Link(GoogleDocsBaseModel):
    """Link model from Google Docs API."""

    bookmark: BookmarkLink | None = None
    bookmarkId: str | None = None
    heading: HeadingLink | None = None
    headingId: str | None = None
    tabId: str | None = None
    url: str | None = None


class WeightedFontFamily(GoogleDocsBaseModel):
    """WeightedFontFamily model from Google Docs API."""

    fontFamily: str | None = None
    weight: int | None = None


class Location(GoogleDocsBaseModel):
    """Location model from Google Docs API."""

    index: int | None = None
    segmentId: str | None = None
    tabId: str | None = None


class Range(GoogleDocsBaseModel):
    """Range model from Google Docs API."""

    endIndex: int | None = None
    segmentId: str | None = None
    startIndex: int | None = None
    tabId: str | None = None


class EndOfSegmentLocation(GoogleDocsBaseModel):
    """EndOfSegmentLocation model from Google Docs API."""

    segmentId: str | None = None
    tabId: str | None = None


class TableCellLocation(GoogleDocsBaseModel):
    """TableCellLocation model from Google Docs API."""

    columnIndex: int | None = None
    rowIndex: int | None = None
    tableStartLocation: Location | None = None


class TableRange(GoogleDocsBaseModel):
    """TableRange model from Google Docs API."""

    columnSpan: int | None = None
    rowSpan: int | None = None
    tableCellLocation: TableCellLocation | None = None


class InlineObject(GoogleDocsBaseModel):
    """InlineObject model from Google Docs API."""

    inlineObjectProperties: InlineObjectProperties | None = None
    objectId: str | None = None
    suggestedDeletionIds: List[str] | None = None
    suggestedInlineObjectPropertiesChanges: dict[str, Any] | None = None
    suggestedInsertionId: str | None = None


class InlineObjectProperties(GoogleDocsBaseModel):
    """InlineObjectProperties model from Google Docs API."""

    embeddedObject: EmbeddedObject | None = None


class PositionedObject(GoogleDocsBaseModel):
    """PositionedObject model from Google Docs API."""

    objectId: str | None = None
    positionedObjectProperties: PositionedObjectProperties | None = None
    suggestedDeletionIds: List[str] | None = None
    suggestedInsertionId: str | None = None
    suggestedPositionedObjectPropertiesChanges: dict[str, Any] | None = None


class PositionedObjectPositioning(GoogleDocsBaseModel):
    """PositionedObjectPositioning model from Google Docs API."""

    layout: (
        Literal[
            "POSITIONED_OBJECT_LAYOUT_UNSPECIFIED",
            "WRAP_TEXT",
            "BREAK_LEFT",
            "BREAK_RIGHT",
            "BREAK_LEFT_RIGHT",
            "IN_FRONT_OF_TEXT",
            "BEHIND_TEXT",
        ]
        | None
    ) = None
    leftOffset: Dimension | None = None
    topOffset: Dimension | None = None


class PositionedObjectProperties(GoogleDocsBaseModel):
    """PositionedObjectProperties model from Google Docs API."""

    embeddedObject: EmbeddedObject | None = None
    positioning: PositionedObjectPositioning | None = None


class EmbeddedObject(GoogleDocsBaseModel):
    """EmbeddedObject model from Google Docs API."""

    description: str | None = None
    embeddedDrawingProperties: EmbeddedDrawingProperties | None = None
    embeddedObjectBorder: EmbeddedObjectBorder | None = None
    imageProperties: ImageProperties | None = None
    linkedContentReference: LinkedContentReference | None = None
    marginBottom: Dimension | None = None
    marginLeft: Dimension | None = None
    marginRight: Dimension | None = None
    marginTop: Dimension | None = None
    size: Size | None = None
    title: str | None = None


class EmbeddedObjectBorder(GoogleDocsBaseModel):
    """EmbeddedObjectBorder model from Google Docs API."""

    color: OptionalColor | None = None
    dashStyle: Literal["DASH_STYLE_UNSPECIFIED", "SOLID", "DOT", "DASH"] | None = None
    propertyState: Literal["RENDERED", "NOT_RENDERED"] | None = None
    width: Dimension | None = None


class ImageProperties(GoogleDocsBaseModel):
    """ImageProperties model from Google Docs API."""

    angle: float | None = None
    brightness: float | None = None
    contentUri: str | None = None
    contrast: float | None = None
    cropProperties: CropProperties | None = None
    sourceUri: str | None = None
    transparency: float | None = None


class SheetsChartReference(GoogleDocsBaseModel):
    """SheetsChartReference model from Google Docs API."""

    chartId: int | None = None
    spreadsheetId: str | None = None


class LinkedContentReference(GoogleDocsBaseModel):
    """LinkedContentReference model from Google Docs API."""

    sheetsChartReference: SheetsChartReference | None = None


class ObjectReferences(GoogleDocsBaseModel):
    """ObjectReferences model from Google Docs API."""

    objectIds: List[str] | None = None


class List(GoogleDocsBaseModel):
    """List model from Google Docs API."""

    listProperties: ListProperties | None = None
    suggestedDeletionIds: List[str] | None = None
    suggestedInsertionId: str | None = None
    suggestedListPropertiesChanges: dict[str, Any] | None = None


class ListProperties(GoogleDocsBaseModel):
    """ListProperties model from Google Docs API."""

    nestingLevels: List[NestingLevel] | None = None


class NamedRange(GoogleDocsBaseModel):
    """NamedRange model from Google Docs API."""

    name: str | None = None
    namedRangeId: str | None = None
    ranges: List[Range] | None = None


class NamedRanges(GoogleDocsBaseModel):
    """NamedRanges model from Google Docs API."""

    name: str | None = None
    namedRanges: List[NamedRange] | None = None


class TabsCriteria(GoogleDocsBaseModel):
    """TabsCriteria model from Google Docs API."""

    tabIds: List[str] | None = None


class BookmarkLink(GoogleDocsBaseModel):
    """BookmarkLink model from Google Docs API."""

    id: str | None = None
    tabId: str | None = None


class HeadingLink(GoogleDocsBaseModel):
    """HeadingLink model from Google Docs API."""

    id: str | None = None
    tabId: str | None = None


class Header(GoogleDocsBaseModel):
    """Header model from Google Docs API."""

    content: List[StructuralElement] | None = None
    headerId: str | None = None


class Footer(GoogleDocsBaseModel):
    """Footer model from Google Docs API."""

    content: List[StructuralElement] | None = None
    footerId: str | None = None


class Footnote(GoogleDocsBaseModel):
    """Footnote model from Google Docs API."""

    content: List[StructuralElement] | None = None
    footnoteId: str | None = None


class RichLinkProperties(GoogleDocsBaseModel):
    """RichLinkProperties model from Google Docs API."""

    mimeType: str | None = None
    title: str | None = None
    uri: str | None = None


class PersonProperties(GoogleDocsBaseModel):
    """PersonProperties model from Google Docs API."""

    email: str | None = None
    name: str | None = None


class TableColumnProperties(GoogleDocsBaseModel):
    """TableColumnProperties model from Google Docs API."""

    width: Dimension | None = None
    widthType: Literal["WIDTH_TYPE_UNSPECIFIED", "EVENLY_DISTRIBUTED", "FIXED_WIDTH"] | None = None


class BackgroundSuggestionState(GoogleDocsBaseModel):
    """BackgroundSuggestionState model from Google Docs API."""

    backgroundColorSuggested: bool | None = None


class ShadingSuggestionState(GoogleDocsBaseModel):
    """ShadingSuggestionState model from Google Docs API."""

    backgroundColorSuggested: bool | None = None


class SizeSuggestionState(GoogleDocsBaseModel):
    """SizeSuggestionState model from Google Docs API."""

    heightSuggested: bool | None = None
    widthSuggested: bool | None = None


class ImagePropertiesSuggestionState(GoogleDocsBaseModel):
    """ImagePropertiesSuggestionState model from Google Docs API."""

    angleSuggested: bool | None = None
    brightnessSuggested: bool | None = None
    contentUriSuggested: bool | None = None
    contrastSuggested: bool | None = None
    cropPropertiesSuggestionState: CropPropertiesSuggestionState | None = None
    sourceUriSuggested: bool | None = None
    transparencySuggested: bool | None = None


class InlineObjectPropertiesSuggestionState(GoogleDocsBaseModel):
    """InlineObjectPropertiesSuggestionState model from Google Docs API."""

    embeddedObjectSuggestionState: EmbeddedObjectSuggestionState | None = None


class EmbeddedObjectBorderSuggestionState(GoogleDocsBaseModel):
    """EmbeddedObjectBorderSuggestionState model from Google Docs API."""

    colorSuggested: bool | None = None
    dashStyleSuggested: bool | None = None
    propertyStateSuggested: bool | None = None
    widthSuggested: bool | None = None


class EmbeddedObjectSuggestionState(GoogleDocsBaseModel):
    """EmbeddedObjectSuggestionState model from Google Docs API."""

    descriptionSuggested: bool | None = None
    embeddedDrawingPropertiesSuggestionState: EmbeddedDrawingPropertiesSuggestionState | None = None
    embeddedObjectBorderSuggestionState: EmbeddedObjectBorderSuggestionState | None = None
    imagePropertiesSuggestionState: ImagePropertiesSuggestionState | None = None
    linkedContentReferenceSuggestionState: LinkedContentReferenceSuggestionState | None = None
    marginBottomSuggested: bool | None = None
    marginLeftSuggested: bool | None = None
    marginRightSuggested: bool | None = None
    marginTopSuggested: bool | None = None
    sizeSuggestionState: SizeSuggestionState | None = None
    titleSuggested: bool | None = None


class PositionedObjectPositioningSuggestionState(GoogleDocsBaseModel):
    """PositionedObjectPositioningSuggestionState model from Google Docs API."""

    layoutSuggested: bool | None = None
    leftOffsetSuggested: bool | None = None
    topOffsetSuggested: bool | None = None


class PositionedObjectPropertiesSuggestionState(GoogleDocsBaseModel):
    """PositionedObjectPropertiesSuggestionState model from Google Docs API."""

    embeddedObjectSuggestionState: EmbeddedObjectSuggestionState | None = None
    positioningSuggestionState: PositionedObjectPositioningSuggestionState | None = None


class SheetsChartReferenceSuggestionState(GoogleDocsBaseModel):
    """SheetsChartReferenceSuggestionState model from Google Docs API."""

    chartIdSuggested: bool | None = None
    spreadsheetIdSuggested: bool | None = None


class LinkedContentReferenceSuggestionState(GoogleDocsBaseModel):
    """LinkedContentReferenceSuggestionState model from Google Docs API."""

    sheetsChartReferenceSuggestionState: SheetsChartReferenceSuggestionState | None = None


class ListPropertiesSuggestionState(GoogleDocsBaseModel):
    """ListPropertiesSuggestionState model from Google Docs API."""

    nestingLevelsSuggestionStates: List[NestingLevelSuggestionState] | None = None


class SuggestedBullet(GoogleDocsBaseModel):
    """SuggestedBullet model from Google Docs API."""

    bullet: Bullet | None = None
    bulletSuggestionState: BulletSuggestionState | None = None


class SuggestedDocumentStyle(GoogleDocsBaseModel):
    """SuggestedDocumentStyle model from Google Docs API."""

    documentStyle: DocumentStyle | None = None
    documentStyleSuggestionState: DocumentStyleSuggestionState | None = None


class SuggestedInlineObjectProperties(GoogleDocsBaseModel):
    """SuggestedInlineObjectProperties model from Google Docs API."""

    inlineObjectProperties: InlineObjectProperties | None = None
    inlineObjectPropertiesSuggestionState: InlineObjectPropertiesSuggestionState | None = None


class SuggestedListProperties(GoogleDocsBaseModel):
    """SuggestedListProperties model from Google Docs API."""

    listProperties: ListProperties | None = None
    listPropertiesSuggestionState: ListPropertiesSuggestionState | None = None


class SuggestedNamedStyles(GoogleDocsBaseModel):
    """SuggestedNamedStyles model from Google Docs API."""

    namedStyles: NamedStyles | None = None
    namedStylesSuggestionState: NamedStylesSuggestionState | None = None


class SuggestedParagraphStyle(GoogleDocsBaseModel):
    """SuggestedParagraphStyle model from Google Docs API."""

    paragraphStyle: ParagraphStyle | None = None
    paragraphStyleSuggestionState: ParagraphStyleSuggestionState | None = None


class SuggestedPositionedObjectProperties(GoogleDocsBaseModel):
    """SuggestedPositionedObjectProperties model from Google Docs API."""

    positionedObjectProperties: PositionedObjectProperties | None = None
    positionedObjectPropertiesSuggestionState: PositionedObjectPropertiesSuggestionState | None = None


class SuggestedTableCellStyle(GoogleDocsBaseModel):
    """SuggestedTableCellStyle model from Google Docs API."""

    tableCellStyle: TableCellStyle | None = None
    tableCellStyleSuggestionState: TableCellStyleSuggestionState | None = None


class SuggestedTableRowStyle(GoogleDocsBaseModel):
    """SuggestedTableRowStyle model from Google Docs API."""

    tableRowStyle: TableRowStyle | None = None
    tableRowStyleSuggestionState: TableRowStyleSuggestionState | None = None


class SuggestedTextStyle(GoogleDocsBaseModel):
    """SuggestedTextStyle model from Google Docs API."""

    textStyle: TextStyle | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None


class CropProperties(GoogleDocsBaseModel):
    """CropProperties model from Google Docs API."""

    angle: float | None = None
    offsetBottom: float | None = None
    offsetLeft: float | None = None
    offsetRight: float | None = None
    offsetTop: float | None = None


class CropPropertiesSuggestionState(GoogleDocsBaseModel):
    """CropPropertiesSuggestionState model from Google Docs API."""

    angleSuggested: bool | None = None
    offsetBottomSuggested: bool | None = None
    offsetLeftSuggested: bool | None = None
    offsetRightSuggested: bool | None = None
    offsetTopSuggested: bool | None = None


class WriteControl(GoogleDocsBaseModel):
    """WriteControl model from Google Docs API."""

    requiredRevisionId: str | None = None
    targetRevisionId: str | None = None


class SubstringMatchCriteria(GoogleDocsBaseModel):
    """SubstringMatchCriteria model from Google Docs API."""

    matchCase: bool | None = None
    searchByRegex: bool | None = None
    text: str | None = None
