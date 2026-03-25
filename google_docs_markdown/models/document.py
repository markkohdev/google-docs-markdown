"""Generated Pydantic models for Google Docs API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from google_docs_markdown.models.base import GoogleDocsBaseModel

if TYPE_CHECKING:
    from google_docs_markdown.models.common import (
        Background,
        BackgroundSuggestionState,
        Dimension,
        Size,
        SizeSuggestionState,
    )
    from google_docs_markdown.models.elements import StructuralElement
    from google_docs_markdown.models.styles import (
        ParagraphStyle,
        ParagraphStyleSuggestionState,
        TextStyle,
        TextStyleSuggestionState,
    )


class Document(GoogleDocsBaseModel):
    """Document model from Google Docs API."""

    body: Body | None = None
    documentId: str | None = None
    documentStyle: DocumentStyle | None = None
    footers: dict[str, Any] | None = None
    footnotes: dict[str, Any] | None = None
    headers: dict[str, Any] | None = None
    inlineObjects: dict[str, Any] | None = None
    lists: dict[str, Any] | None = None
    namedRanges: dict[str, Any] | None = None
    namedStyles: NamedStyles | None = None
    positionedObjects: dict[str, Any] | None = None
    revisionId: str | None = None
    suggestedDocumentStyleChanges: dict[str, Any] | None = None
    suggestedNamedStylesChanges: dict[str, Any] | None = None
    suggestionsViewMode: (
        Literal[
            "DEFAULT_FOR_CURRENT_ACCESS",
            "SUGGESTIONS_INLINE",
            "PREVIEW_SUGGESTIONS_ACCEPTED",
            "PREVIEW_WITHOUT_SUGGESTIONS",
        ]
        | None
    ) = None
    tabs: list[Tab] | None = None
    title: str | None = None


class DocumentTab(GoogleDocsBaseModel):
    """DocumentTab model from Google Docs API."""

    body: Body | None = None
    documentStyle: DocumentStyle | None = None
    footers: dict[str, Any] | None = None
    footnotes: dict[str, Any] | None = None
    headers: dict[str, Any] | None = None
    inlineObjects: dict[str, Any] | None = None
    lists: dict[str, Any] | None = None
    namedRanges: dict[str, Any] | None = None
    namedStyles: NamedStyles | None = None
    positionedObjects: dict[str, Any] | None = None
    suggestedDocumentStyleChanges: dict[str, Any] | None = None
    suggestedNamedStylesChanges: dict[str, Any] | None = None


class Body(GoogleDocsBaseModel):
    """Body model from Google Docs API."""

    content: list[StructuralElement] | None = None


class Tab(GoogleDocsBaseModel):
    """Tab model from Google Docs API."""

    childTabs: list[Tab] | None = None
    documentTab: DocumentTab | None = None
    tabProperties: TabProperties | None = None


class TabProperties(GoogleDocsBaseModel):
    """TabProperties model from Google Docs API."""

    iconEmoji: str | None = None
    index: int | None = None
    nestingLevel: int | None = None
    parentTabId: str | None = None
    tabId: str | None = None
    title: str | None = None


class DocumentStyle(GoogleDocsBaseModel):
    """DocumentStyle model from Google Docs API."""

    background: Background | None = None
    defaultFooterId: str | None = None
    defaultHeaderId: str | None = None
    documentFormat: DocumentFormat | None = None
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
    pageSize: Size | None = None
    useCustomHeaderFooterMargins: bool | None = None
    useEvenPageHeaderFooter: bool | None = None
    useFirstPageHeaderFooter: bool | None = None


class DocumentFormat(GoogleDocsBaseModel):
    """DocumentFormat model from Google Docs API."""

    documentMode: Literal["DOCUMENT_MODE_UNSPECIFIED", "PAGES", "PAGELESS"] | None = None


class DocumentStyleSuggestionState(GoogleDocsBaseModel):
    """DocumentStyleSuggestionState model from Google Docs API."""

    backgroundSuggestionState: BackgroundSuggestionState | None = None
    defaultFooterIdSuggested: bool | None = None
    defaultHeaderIdSuggested: bool | None = None
    evenPageFooterIdSuggested: bool | None = None
    evenPageHeaderIdSuggested: bool | None = None
    firstPageFooterIdSuggested: bool | None = None
    firstPageHeaderIdSuggested: bool | None = None
    flipPageOrientationSuggested: bool | None = None
    marginBottomSuggested: bool | None = None
    marginFooterSuggested: bool | None = None
    marginHeaderSuggested: bool | None = None
    marginLeftSuggested: bool | None = None
    marginRightSuggested: bool | None = None
    marginTopSuggested: bool | None = None
    pageNumberStartSuggested: bool | None = None
    pageSizeSuggestionState: SizeSuggestionState | None = None
    useCustomHeaderFooterMarginsSuggested: bool | None = None
    useEvenPageHeaderFooterSuggested: bool | None = None
    useFirstPageHeaderFooterSuggested: bool | None = None


class NamedStyles(GoogleDocsBaseModel):
    """NamedStyles model from Google Docs API."""

    styles: list[NamedStyle] | None = None


class NamedStyle(GoogleDocsBaseModel):
    """NamedStyle model from Google Docs API."""

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
    paragraphStyle: ParagraphStyle | None = None
    textStyle: TextStyle | None = None


class NamedStyleSuggestionState(GoogleDocsBaseModel):
    """NamedStyleSuggestionState model from Google Docs API."""

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
    paragraphStyleSuggestionState: ParagraphStyleSuggestionState | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None


class NamedStylesSuggestionState(GoogleDocsBaseModel):
    """NamedStylesSuggestionState model from Google Docs API."""

    stylesSuggestionStates: list[NamedStyleSuggestionState] | None = None
