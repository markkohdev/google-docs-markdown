"""Generated Pydantic models for Google Docs API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from google_docs_markdown.models.base import GoogleDocsBaseModel

if TYPE_CHECKING:
    from google_docs_markdown.models.common import (
        Dimension,
        Link,
        OptionalColor,
        Shading,
        ShadingSuggestionState,
        TableColumnProperties,
        WeightedFontFamily,
    )


class ParagraphStyle(GoogleDocsBaseModel):
    """ParagraphStyle model from Google Docs API."""

    alignment: Literal["ALIGNMENT_UNSPECIFIED", "START", "CENTER", "END", "JUSTIFIED"] | None = None
    avoidWidowAndOrphan: bool | None = None
    borderBetween: ParagraphBorder | None = None
    borderBottom: ParagraphBorder | None = None
    borderLeft: ParagraphBorder | None = None
    borderRight: ParagraphBorder | None = None
    borderTop: ParagraphBorder | None = None
    direction: Literal["CONTENT_DIRECTION_UNSPECIFIED", "LEFT_TO_RIGHT", "RIGHT_TO_LEFT"] | None = None
    headingId: str | None = None
    indentEnd: Dimension | None = None
    indentFirstLine: Dimension | None = None
    indentStart: Dimension | None = None
    keepLinesTogether: bool | None = None
    keepWithNext: bool | None = None
    lineSpacing: float | None = None
    namedStyleType: (
        Literal[
            "NAMED_STYLE_TYPE_UNSPECIFIED",
            "NORMAL_TEXT",
            "TITLE",
            "SUBTITLE",
            "HEADING_1",
            "HEADING_2",
            "HEADING_3",
            "HEADING_4",
            "HEADING_5",
            "HEADING_6",
        ]
        | None
    ) = None
    pageBreakBefore: bool | None = None
    shading: Shading | None = None
    spaceAbove: Dimension | None = None
    spaceBelow: Dimension | None = None
    spacingMode: Literal["SPACING_MODE_UNSPECIFIED", "NEVER_COLLAPSE", "COLLAPSE_LISTS"] | None = None
    tabStops: list[TabStop] | None = None


class TextStyle(GoogleDocsBaseModel):
    """TextStyle model from Google Docs API."""

    backgroundColor: OptionalColor | None = None
    baselineOffset: Literal["BASELINE_OFFSET_UNSPECIFIED", "NONE", "SUPERSCRIPT", "SUBSCRIPT"] | None = None
    bold: bool | None = None
    fontSize: Dimension | None = None
    foregroundColor: OptionalColor | None = None
    italic: bool | None = None
    link: Link | None = None
    smallCaps: bool | None = None
    strikethrough: bool | None = None
    underline: bool | None = None
    weightedFontFamily: WeightedFontFamily | None = None


class TableCellStyle(GoogleDocsBaseModel):
    """TableCellStyle model from Google Docs API."""

    backgroundColor: OptionalColor | None = None
    borderBottom: TableCellBorder | None = None
    borderLeft: TableCellBorder | None = None
    borderRight: TableCellBorder | None = None
    borderTop: TableCellBorder | None = None
    columnSpan: int | None = None
    contentAlignment: (
        Literal["CONTENT_ALIGNMENT_UNSPECIFIED", "CONTENT_ALIGNMENT_UNSUPPORTED", "TOP", "MIDDLE", "BOTTOM"] | None
    ) = None
    paddingBottom: Dimension | None = None
    paddingLeft: Dimension | None = None
    paddingRight: Dimension | None = None
    paddingTop: Dimension | None = None
    rowSpan: int | None = None


class TableRowStyle(GoogleDocsBaseModel):
    """TableRowStyle model from Google Docs API."""

    minRowHeight: Dimension | None = None
    preventOverflow: bool | None = None
    tableHeader: bool | None = None


class TableStyle(GoogleDocsBaseModel):
    """TableStyle model from Google Docs API."""

    tableColumnProperties: list[TableColumnProperties] | None = None


class SectionStyle(GoogleDocsBaseModel):
    """SectionStyle model from Google Docs API."""

    columnProperties: list[SectionColumnProperties] | None = None
    columnSeparatorStyle: Literal["COLUMN_SEPARATOR_STYLE_UNSPECIFIED", "NONE", "BETWEEN_EACH_COLUMN"] | None = None
    contentDirection: Literal["CONTENT_DIRECTION_UNSPECIFIED", "LEFT_TO_RIGHT", "RIGHT_TO_LEFT"] | None = None
    defaultFooterId: str | None = None
    defaultHeaderId: str | None = None
    evenPageFooterId: str | None = None
    evenPageHeaderId: str | None = None
    firstPageFooterId: str | None = None
    firstPageHeaderId: str | None = None
    flipPageOrientation: bool | None = None
    marginBottom: Dimension | None = None
    marginFooter: Dimension | None = None
    marginHeader: Dimension | None = None
    marginLeft: Dimension | None = None
    marginRight: Dimension | None = None
    marginTop: Dimension | None = None
    pageNumberStart: int | None = None
    sectionType: Literal["SECTION_TYPE_UNSPECIFIED", "CONTINUOUS", "NEXT_PAGE"] | None = None
    useFirstPageHeaderFooter: bool | None = None


class SectionColumnProperties(GoogleDocsBaseModel):
    """SectionColumnProperties model from Google Docs API."""

    paddingEnd: Dimension | None = None
    width: Dimension | None = None


class ParagraphBorder(GoogleDocsBaseModel):
    """ParagraphBorder model from Google Docs API."""

    color: OptionalColor | None = None
    dashStyle: Literal["DASH_STYLE_UNSPECIFIED", "SOLID", "DOT", "DASH"] | None = None
    padding: Dimension | None = None
    width: Dimension | None = None


class TableCellBorder(GoogleDocsBaseModel):
    """TableCellBorder model from Google Docs API."""

    color: OptionalColor | None = None
    dashStyle: Literal["DASH_STYLE_UNSPECIFIED", "SOLID", "DOT", "DASH"] | None = None
    width: Dimension | None = None


class Bullet(GoogleDocsBaseModel):
    """Bullet model from Google Docs API."""

    listId: str | None = None
    nestingLevel: int | None = None
    textStyle: TextStyle | None = None


class NestingLevel(GoogleDocsBaseModel):
    """NestingLevel model from Google Docs API."""

    bulletAlignment: Literal["BULLET_ALIGNMENT_UNSPECIFIED", "START", "CENTER", "END"] | None = None
    glyphFormat: str | None = None
    glyphSymbol: str | None = None
    glyphType: (
        Literal[
            "GLYPH_TYPE_UNSPECIFIED", "NONE", "DECIMAL", "ZERO_DECIMAL", "UPPER_ALPHA", "ALPHA", "UPPER_ROMAN", "ROMAN"
        ]
        | None
    ) = None
    indentFirstLine: Dimension | None = None
    indentStart: Dimension | None = None
    startNumber: int | None = None
    textStyle: TextStyle | None = None


class TabStop(GoogleDocsBaseModel):
    """TabStop model from Google Docs API."""

    alignment: Literal["TAB_STOP_ALIGNMENT_UNSPECIFIED", "START", "CENTER", "END"] | None = None
    offset: Dimension | None = None


class ParagraphStyleSuggestionState(GoogleDocsBaseModel):
    """ParagraphStyleSuggestionState model from Google Docs API."""

    alignmentSuggested: bool | None = None
    avoidWidowAndOrphanSuggested: bool | None = None
    borderBetweenSuggested: bool | None = None
    borderBottomSuggested: bool | None = None
    borderLeftSuggested: bool | None = None
    borderRightSuggested: bool | None = None
    borderTopSuggested: bool | None = None
    directionSuggested: bool | None = None
    headingIdSuggested: bool | None = None
    indentEndSuggested: bool | None = None
    indentFirstLineSuggested: bool | None = None
    indentStartSuggested: bool | None = None
    keepLinesTogetherSuggested: bool | None = None
    keepWithNextSuggested: bool | None = None
    lineSpacingSuggested: bool | None = None
    namedStyleTypeSuggested: bool | None = None
    pageBreakBeforeSuggested: bool | None = None
    shadingSuggestionState: ShadingSuggestionState | None = None
    spaceAboveSuggested: bool | None = None
    spaceBelowSuggested: bool | None = None
    spacingModeSuggested: bool | None = None


class TextStyleSuggestionState(GoogleDocsBaseModel):
    """TextStyleSuggestionState model from Google Docs API."""

    backgroundColorSuggested: bool | None = None
    baselineOffsetSuggested: bool | None = None
    boldSuggested: bool | None = None
    fontSizeSuggested: bool | None = None
    foregroundColorSuggested: bool | None = None
    italicSuggested: bool | None = None
    linkSuggested: bool | None = None
    smallCapsSuggested: bool | None = None
    strikethroughSuggested: bool | None = None
    underlineSuggested: bool | None = None
    weightedFontFamilySuggested: bool | None = None


class TableCellStyleSuggestionState(GoogleDocsBaseModel):
    """TableCellStyleSuggestionState model from Google Docs API."""

    backgroundColorSuggested: bool | None = None
    borderBottomSuggested: bool | None = None
    borderLeftSuggested: bool | None = None
    borderRightSuggested: bool | None = None
    borderTopSuggested: bool | None = None
    columnSpanSuggested: bool | None = None
    contentAlignmentSuggested: bool | None = None
    paddingBottomSuggested: bool | None = None
    paddingLeftSuggested: bool | None = None
    paddingRightSuggested: bool | None = None
    paddingTopSuggested: bool | None = None
    rowSpanSuggested: bool | None = None


class TableRowStyleSuggestionState(GoogleDocsBaseModel):
    """TableRowStyleSuggestionState model from Google Docs API."""

    minRowHeightSuggested: bool | None = None


class BulletSuggestionState(GoogleDocsBaseModel):
    """BulletSuggestionState model from Google Docs API."""

    listIdSuggested: bool | None = None
    nestingLevelSuggested: bool | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None


class NestingLevelSuggestionState(GoogleDocsBaseModel):
    """NestingLevelSuggestionState model from Google Docs API."""

    bulletAlignmentSuggested: bool | None = None
    glyphFormatSuggested: bool | None = None
    glyphSymbolSuggested: bool | None = None
    glyphTypeSuggested: bool | None = None
    indentFirstLineSuggested: bool | None = None
    indentStartSuggested: bool | None = None
    startNumberSuggested: bool | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None
