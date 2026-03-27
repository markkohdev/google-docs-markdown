# Google Docs Markdown - Development Plan

**Created:** 2026-01-08  
**Last Updated:** 2026-03-27 (Phases 3.1–3.3 complete — per-element handler architecture, context layer, handler migration)  
**Status:** Phase 1 — **complete** (1.1–1.7 done; remaining 1.4 items deferred to Phase 3 by design); **Phase 2.1–2.6 — complete**; **Phase 3.1–3.3 — complete** (context layer, handler infrastructure, handler migration done); **Phase 3.4+ — in progress** (element registry, source map, deserializer, diff engine, `uploader.py` still to do)

## Overview

This document outlines the development plan for building the Google Docs Markdown tool. The plan is organized into phases, starting with a Minimum Viable Product (MVP) and progressively adding features.

**Important:** Multi-tab Google Docs support is integrated from Phase 1. All documents are treated as multi-tab documents (even single-tab ones), creating directory structures named after the document title, with each tab saved as a separate markdown file. Tabs can be nested (contain both content and child tabs), and this nested structure must be handled recursively.

Unit tests and documentation should be written for each component and function as they are implemented.

## Development Phases

### Phase 1: Foundation & MVP (Core Download with Multi-Tab Support)
**Goal:** Get basic Google Docs → Markdown conversion working, including multi-tab documents

#### 1.1: Project Setup ✅
- [x] Set up proper project structure
- [x] Configure development dependencies (pytest, black, ruff, mypy)
- [x] Set up basic CI/CD (GitHub Actions with tests, linting, formatting, type checking)
- [x] Create `.gitignore` and development documentation

#### 1.2: Google Docs API Transport & Client ✅
- [x] Create `google_docs_markdown/transport.py` (`GoogleDocsTransport` — low-level, returns raw API dicts)
- [x] Create `google_docs_markdown/client.py` (`GoogleDocsClient` — composes transport, returns Pydantic models)
- [x] Implement authentication using Application Default Credentials
- [x] Create wrapper for Google Docs API (`documents().get()`)
- [x] Handle authentication errors gracefully
- [x] Include retry logic for transient failures
- [x] Extract document ID from URLs
- [x] Retrieve tab information (names, IDs) for multi-tab documents

#### 1.3: Pydantic Model Generation (Foundational Work) ✅
- [x] Create `scripts/generate_models.py` script
- [x] Implement parser to extract TypedDict definitions from `google-api-python-client-stubs` schemas.pyi
- [x] Convert TypedDict classes to Pydantic models following conversion patterns
- [x] Handle forward references and circular dependencies
- [x] Organize models into appropriate files (`google_docs_markdown/models/`)
- [x] Create base model configuration (`base.py`)
- [x] Generate all Pydantic models (100+ models)
- [x] Review and test generated models with sample API responses
- [x] Separate transport (raw dicts) from client (Pydantic models) — `GoogleDocsTransport` and `GoogleDocsClient`
- [x] `GoogleDocsClient` returns Pydantic models and accepts Pydantic models for batch updates
- [x] `GoogleDocsTransport` returns raw dicts for use cases like downloading test fixtures
- [x] Test API round-trip (dict → Pydantic → dict)

#### 1.4: Basic Downloader (Docs → Markdown) ✅
- [x] Create `google_docs_markdown/downloader.py`
- [x] Create `google_docs_markdown/markdown_serializer.py` implementing Visitor Pattern for Pydantic → Markdown conversion
- [x] Implement `MarkdownSerializer` visitor class to traverse Pydantic models
- [x] Treat every document as multi-tab (use `DocumentTab` Pydantic model as fundamental object)
- [x] Handle nested tab structures recursively (tabs can contain both content and child tabs)
- [x] Use `GoogleDocsClient` (Pydantic models) for document retrieval
- [x] Implement basic text extraction from Pydantic `TextRun` models
- [x] Handle headings (up to arbitrary depth) from `Paragraph` models with heading styles
- [x] Handle paragraphs from `Paragraph` Pydantic models
- [x] Handle basic formatting (bold, italic) from `TextStyle` models
- [x] Handle line breaks
- [x] Ensure deterministic output (normalize whitespace)
- [x] Create directory structure named after document title (or user-provided output directory)
- [x] Download each tab (including nested tabs) as a separate markdown file named after the tab (e.g., `My Doc/Tab 1.md`)
- [x] Name markdown files after tab names (sanitize filenames)
- [x] Handle nested tabs with appropriate naming convention (e.g., `Tab 1/Subtab A.md`)
- [ ] Ensure Location/Range objects include `tabId` when working with multi-tab documents (API client ready; objects created in later tasks)
- [ ] Handle `segmentId` in Location/Range objects for headers/footers/footnotes (API client ready; objects created in later tasks)

#### 1.5: CLI - Download Command ✅
- [x] Create `google_docs_markdown/cli.py` using `typer`
- [x] Implement `download` command (calls `Downloader.download_to_files`)
- [x] Support document URL/ID input (with interactive prompt via typer)
- [x] Support output directory path (`--output` / `-o`)
- [x] Add `--tabs` flag for selective tab download (specify which tabs to download)
- [x] Add `--force` / `-f` flag for overwriting existing files and deleting stale files without prompting
- [x] Add file conflict handling (`FileConflictError`) — prompts user to overwrite when files already exist
- [x] Add stale file cleanup — detects `.md` files left over from removed tabs and offers to delete them
- [x] Add interactive prompts for missing arguments (document URL prompted by typer)
- [x] Update `pyproject.toml` entry point (`google-docs-markdown` and `gdm` aliases)

#### 1.6: Python API - Basic Interface ✅
- [x] Create `Downloader` class in `downloader.py` (named `Downloader`, not `GoogleDocMarkdown`)
- [x] Implement `download(document_id)` → returns dict of tab_path → markdown (all docs treated as multi-tab)
- [x] Implement `download_to_files(document_id, output_path, overwrite=True)` → saves to directory, returns dict of tab_path → file Path. Raises `FileConflictError` when `overwrite=False` and files exist.
- [x] Implement `get_document_title(document_id)` → returns title (available via `GoogleDocsClient.get_document().title`)
- [x] Implement `get_tabs(document_id)` → returns list of `TabSummary` objects with tab names/IDs/nesting (available via `Document.tabs`)
- [x] Implement `get_nested_tabs(document_id, tab_id)` → returns nested `TabSummary` children within a tab
- [x] `extract_document_id(url)` → available as `GoogleDocsClient.extract_document_id()` (static method)
- [x] `find_stale_files(output_dir, current_files)` → returns stale `.md` files from previous downloads
- [x] `remove_empty_dirs(root)` → cleans up empty directories after stale file removal

#### 1.7: Testing ✅
- [x] Test with example Google Doc from `example_markdown/google_doc_urls.txt` (integration — requires live API) ✅
- [x] Test with multi-tab Google Doc (integration — requires live API; skips nested-tab assertions when live doc lacks nested tabs) ✅
- [x] Create unit tests for transport and client (including tab detection) ✅
- [x] Create unit tests for `MarkdownSerializer` ✅
- [x] Create unit tests for `Downloader` (including file conflict handling, stale file detection, overwrite flag) ✅
- [x] Create unit tests for CLI `download` command (including `--force`, conflict prompts, stale cleanup) ✅
- [x] Create unit tests for CLI `list-tabs` command ✅
- [x] Create integration tests for end-to-end download (`tests/test_integration.py` — 12 tests, marked `@pytest.mark.integration`) ✅
- [x] Verify deterministic output (same doc → same markdown) ✅
- [x] Test directory creation and file naming for multi-tab documents ✅
- [x] Test selective tab download with `--tabs` flag ✅

**Deliverable:** Can download Google Docs as Markdown (creates directory structure with markdown files inside, named after document title)

---

### Phase 2: Enhanced Markdown Features
**Goal:** Support more complex document structures (applies to all tabs in multi-tab documents)

Phase 2 is broken into sub-phases ordered by complexity and dependency. Each sub-phase can be implemented and tested independently.

#### Phase 2.1: Simple Inline and Block Elements (no state tracking needed) ✅

These elements can be handled by extending `MarkdownSerializer` with additional `_visit_*` branches. No changes to the serializer's stateless architecture required.

##### 2.1.1: Links and Inline Formatting
- [x] Handle links (`TextStyle.link.url` → `[text](url)`)
- [x] Handle strikethrough (`TextStyle.strikethrough` → `~~text~~`)
- [x] Handle underline (convert to HTML `<u>` tag; auto-underline on links is suppressed)
- [x] Handle rich links (`RichLink.richLinkProperties` → `[title](uri)`). **Note:** `RichLink` is a first-class `ParagraphElement` for reading, but there is no `insertRichLink` batchUpdate request — on upload, falls back to a regular hyperlink
- [x] Handle horizontal rules (`HorizontalRule` → `---`)
- [x] Handle footnote references (`FootnoteReference` → `[^N]`) and footnote content from `DocumentTab.footnotes`

##### 2.1.2: Testing
- [x] Unit tests for each new element type (29 new tests: 8 inline formatting, 7 link helper, 14 serializer tests covering links, strikethrough, underline, horizontal rules, rich links, footnotes, and combined formatting)
- [x] Fixture-based integration tests (existing fixture tests continue to pass)

#### Phase 2.2: Lists (requires stateful serialization + `DocumentTab.lists` context) ✅

Lists require a significant change to the serializer: consecutive `Paragraph` elements with `bullet` fields must be grouped, and the `DocumentTab.lists` dict must be consulted to determine ordered vs. unordered. This is the first feature that requires cross-paragraph state.

**Architecture note:** Option (b) was implemented — a pre-processing "block grouper" pass (`block_grouper.py`) groups structural elements into typed blocks before serializing. This also benefits code block detection (Phase 2.4).

##### 2.2.1: List Support
- [x] Refactor serializer to use block grouper pre-processing pass (`block_grouper.py`)
- [x] Handle unordered lists (`Paragraph.bullet` + `glyphType == GLYPH_TYPE_UNSPECIFIED` → `- item`)
- [x] Handle ordered lists (`Paragraph.bullet` + `glyphType` in `DECIMAL`/`UPPER_ALPHA`/etc. → `1. item`)
- [x] Handle nested lists via `bullet.nestingLevel` (4-space indentation per level)
- [x] Handle list item spacing (single newline between items, blank line before/after list)
- [x] Look up list type via `DocumentTab.lists[listId].listProperties.nestingLevels[n].glyphType`

##### 2.2.2: Testing
- [x] Unit tests for ordered, unordered, and nested lists (10 block grouper tests + 11 serializer list tests)
- [x] Test list grouping across consecutive paragraphs
- [x] Fixture-based test verifying real document lists render with bullet markers

#### Phase 2.3: Tables ✅

##### 2.3.1: Table Support
- [x] Handle `Table` structural element → Markdown pipe table
- [x] Traverse `TableRow` → `TableCell` → `content[]` (recursive `StructuralElement` list)
- [x] Handle header rows (`tableRowStyle.tableHeader`)
- [x] Handle cell content (can contain paragraphs with formatting)
- [x] Generate separator row (`| --- | --- |`)

##### 2.3.2: Testing
- [x] Unit tests with fixture table data
- [x] Test tables with formatted cell content

#### Phase 2.4: Code Blocks (U+E907 boundary markers + monospace font heuristic) ✅

Google Docs code blocks are NOT a formal API element. They are detected via a combination of `U+E907` boundary markers and monospace font. See `TECH_SPEC.md` Section 5.9 for full details.

##### 2.4.1: Code Block Detection and Serialization
- [x] Detect code block boundaries via `U+E907` (`\ue907`) bookend characters in `TextRun.content`
- [x] Monospace font detection helper (`_paragraph_has_monospace_font`) supports `Roboto Mono`, `Courier New`, `Consolas`, `Source Code Pro`
- [x] Group consecutive paragraphs between U+E907 bookends into `CodeBlock` objects via `block_grouper.py`
- [x] Emit bare fenced code blocks with no language identifier (API does not expose language)
- [x] Strip `U+E907` characters from Markdown output (not meaningful to users)
- [x] Strip `U+E907` from inline `TextRun.content` in `_visit_text_run` (handles non-code-block occurrences like smart chip placeholders)
- [ ] Preserve `U+E907` positions in internal representation for round-trip fidelity (deferred to Phase 3 — upload needs index mapping)

##### 2.4.2: Testing
- [x] Unit tests for code block detection and serialization (5 block grouper tests + 12 serializer tests covering single/multi-line code blocks, U+E907 stripping, mixed content)

#### Phase 2.5: Images ✅

##### 2.5.1: Image Support
- [x] Handle `InlineObjectElement` → `![alt](url)` via `_visit_inline_object` in `markdown_serializer.py`
- [x] Look up image data in `DocumentTab.inlineObjects[objectId].inlineObjectProperties.embeddedObject`
- [x] Handle image alt text (from `description` or `title` if available, falls back to empty string)
- [x] Generate Markdown image references with Google-hosted `contentUri` URLs
- [ ] Download images from `contentUri` to local `imgs/` directory within the document's output folder (deferred to Phase 6 — image storage integration)
- [ ] Generate Markdown image references with local paths (deferred to Phase 6)

##### 2.5.2: Testing
- [x] Unit tests for image reference generation (inline object lookup, alt text handling, missing/invalid objects, integration with paragraph rendering)

#### Phase 2.6: Non-Markdown Elements, Metadata Strategy, and Suggestions

This sub-phase handles Google Docs features that have no direct Markdown equivalent. It absorbs the metadata strategy work originally planned for Phase 5.

##### 2.6.1: Metadata Strategy Decision ✅
- [x] Decided on wrapping HTML comment pattern: `<!-- type: {json} -->content<!-- /type -->` for inline element-level annotations
- [x] Defined metadata format for each element type (see `comment_tags.py` `TagType` enum)
- [x] `RichLink` wrapped in `<!-- rich-link: {"mimeType": "..."} -->[title](uri)<!-- /rich-link -->` when `mimeType` is present
- [x] Embedded metadata block at bottom of markdown file (`<!-- google-docs-metadata ... -->`) for document-level properties — no sidecar files
- [x] Created `comment_tags.py` module (serialization, parsing, tag registry) and `metadata.py` module (embedded block serialize/parse/strip)

##### 2.6.2: Non-Markdown Element Handling ✅

**First-class ParagraphElements with full API read support:**
- [x] Handle `Person` mentions — `<!-- person: {"email": "..."} -->Name<!-- /person -->`. **Round-trippable** via `insertPerson` batchUpdate
- [x] Handle `DateElement` — `<!-- date: {"format": "...", "locale": "...", ...} -->displayText<!-- /date -->`. **Round-trippable** via `insertDate` batchUpdate
- [x] Handle `RichLink` metadata — wrapped in `<!-- rich-link: {"mimeType": "..."} -->` when mimeType present; falls back to plain `[title](uri)` when no mimeType
- [x] Handle `AutoText` — `<!-- auto-text: {"type": "PAGE_NUMBER"} -->`
- [x] Handle `Equation` — `<!-- equation -->`

**Other non-Markdown elements:**
- [x] Handle colored text (`foregroundColor`, `backgroundColor`) — `<!-- style: {"color": "#FF0000", "background-color": "#0000FF"} -->text<!-- /style -->` (only non-default properties emitted; default determined by NORMAL_TEXT named style)
- [x] Handle non-default font-size and font-family via same `<!-- style -->` wrapping (common Google Docs fonts like Arial excluded from font-family checks to reduce noise)
- [x] Handle column breaks — `<!-- column-break -->`
- [x] Handle page breaks — `<!-- page-break -->`
- [x] Handle section breaks — `<!-- section-break: {"type": "..."} -->` (leading section break at `body.content[0]` always skipped; only mid-document breaks serialized)
- [x] Handle table of contents — `<!-- table-of-contents -->` (body content omitted; auto-generated by Docs)
- [x] Handle `TITLE` and `SUBTITLE` — `<!-- title -->` / `<!-- subtitle -->` markers precede the paragraph
- [x] Handle U+E907 chip placeholders — `<!-- chip-placeholder -->` replaces `\ue907` in TextRun content for chips without API data (status, file, place chips)

##### 2.6.3: Suggestion Handling ✅
- [x] Suggested insertions wrapped in `<!-- suggestion: {"id": "...", "type": "insertion"} -->text<!-- /suggestion -->`
- [x] Suggested deletions wrapped in `<!-- suggestion: {"id": "...", "type": "deletion"} -->text<!-- /suggestion -->`

##### 2.6.4: Headers, Footers, and Footnotes ✅
- [x] Headers serialized as `<!-- header: {"id": "..."} -->content<!-- /header -->` blocks
- [x] Footers serialized as `<!-- footer: {"id": "..."} -->content<!-- /footer -->` blocks
- [x] Footnotes (already implemented in Phase 2.1)

##### 2.6.5: Testing ✅
- [x] 74 new Phase 2.6 tests: `test_comment_tags.py` (16 tests), `test_metadata.py` (10 tests), `test_phase26_serializer.py` (48 tests)
- [x] Comment tag serialize + parse round-trip tests
- [x] Embedded metadata block round-trip tests
- [x] Fixture-based tests verifying person, date, chips, title/subtitle, TOC, rich link, suggestions against Multi-Tab fixture
- [x] Style default detection tests, custom font tests, heading font-size inheritance tests

**Deliverable:** Can download complex Google Docs with tables, images, lists, code blocks, links, footnotes, headers/footers, section breaks, TOC, suggestions, smart chips, and all paragraph elements, with full support for multi-tab documents. Non-markdown elements preserved via consistent HTML comment annotation pattern. Each file is self-contained with embedded metadata.

**Phase 2 progress note:** Phases 2.1–2.6 are complete. Total test count at end of Phase 2: 355 unit tests (164 existing + 74 new Phase 2.6 + 117 others) + 12 integration tests. After Phase 3.1–3.3: 423 tests (55 new context/registry tests).

---

### Phase 3: Upload (Markdown → Docs), Change Detection & Diffing
**Goal:** Convert Markdown back to Google Docs (create and update), with surgical change detection. Includes per-element handler architecture, shared context, source map, diff engine, and full multi-tab support.

**Key Architecture Decisions:**
- **Per-element handler pattern:** Each document element (heading, bold, person chip, table, etc.) gets its own handler class that owns both serialization and deserialization logic. A central orchestrator dispatches to handlers. This replaces the monolithic serializer with a slim orchestrator + handler registry, and prevents ser/deser formats from drifting. See `TECH_SPEC.md` Section 5.11.
- **Three-layer context:** `DocumentContext` (frozen, immutable document defaults), `SerContext`/`DeserContext` (mutable, direction-specific traversal state). `DocumentContext` is populated from `DocumentTab` (serialization) or the embedded metadata block (deserialization).
- **Atomic, surgical edits for updates:** Fetch current doc → serialize with source map → diff against local Markdown → map diff ranges to API indices → surgical `batchUpdate` requests. See `TECH_SPEC.md` Sections 5.9-5.10.
- **Create-before-update ordering:** The create-new-document flow validates the deserializer end-to-end before the update flow layers diffing on top.

**Progress (2026-03-27):** `GoogleDocsClient` exposes `create_document` and `batch_update` with Pydantic models (unit tested). CLI `upload` command exists as a stub. `list-tabs` CLI command implemented. **Phases 3.1–3.6 complete:** context layer, handler infrastructure, full handler migration, element registry with shared constants, source map (`SourceSpan`/`SpanKind`/`SourceMapBuilder`/`SourceMap`), and full markdown deserializer (`MarkdownDeserializer` with `markdown-it-py`, `deserialize()` on all handlers, comment-tag dispatch). 490 tests pass. No diff engine or `uploader.py` yet.

#### 3.1: Context Layer ✅
- [x] Create `google_docs_markdown/handlers/context.py`
- [x] Define `DocumentContext` frozen dataclass with all document-level defaults (default font, font size, foreground color, link color, named style sizes/colors/fonts, date defaults)
- [x] Implement `DocumentContext.from_document_tab(tab)` factory — extracts from `DocumentTab.namedStyles` (same logic as current `_extract_default_styles()`)
- [x] Implement `DocumentContext.from_metadata(metadata)` factory — extracts from parsed `<!-- google-docs-metadata ... -->` block's `defaultStyles`
- [x] Implement lookup methods: `expected_font_size(style_name)`, `expected_color(style_name)`, `expected_font(style_name)`
- [x] Define `SerContext` mutable dataclass (holds `DocumentContext`, `current_para_style`, `footnote_refs`, `date_defaults`, `source_map`, `inline_objects`, `lists_context`, `body_content`, plus `collect_paragraph_text` and `visit_block` callbacks)
- [x] Define `DeserContext` mutable dataclass (holds `DocumentContext`, `index`, `tab_id`, `segment_id`, `requests` accumulator, `advance()` and `emit()` methods)
- [x] Unit tests: 32 tests in `test_context.py` — verify `from_document_tab()` and `from_metadata()` produce equivalent contexts, test lookup methods against named style hierarchies, round-trip through metadata, `optional_color_to_hex`, SerContext/DeserContext state

#### 3.2: Handler Infrastructure ✅
- [x] Create `google_docs_markdown/handlers/` package
- [x] Define `ElementHandler` ABC in `handlers/base.py` with `serialize_match()`, `serialize()`, `deserialize_match()`, `deserialize()` abstract methods
- [x] Define `TagElementHandler` subclass with `TAG_TYPE` class attribute (shared between ser and deser directions)
- [x] Define `BlockElementHandler` subclass for structural blocks (heading, list, table, code)
- [x] Define `InlineFormatHandler` subclass with `MARKER` and `STYLE_FIELD` class attributes
- [x] Create `HandlerRegistry` in `handlers/registry.py` with three-level dispatch (`match_paragraph_element`, `match_structural`, `match_block`) and `match_deserialize` lookup, plus `get_handler(type)` accessor and `default()` factory
- [x] Unit tests: 23 tests in `test_handler_registry.py` — dispatch for all 11 paragraph element types, 4 structural elements, 2 block types, custom registry, `get_handler`, empty registry

#### 3.3: Handler Migration (Serialization Side) ✅
Migrated all `_visit_*` methods from `markdown_serializer.py` into per-element handler classes. All 423 unit tests pass (55 new + 368 existing).

- [x] **Comment-tag elements**: `PersonHandler` (`handlers/person.py`), `DateHandler` (`handlers/date.py`), `AutoTextHandler`, `EquationHandler`, `PageBreakHandler`/`ColumnBreakHandler`/`SectionBreakHandler` (`handlers/breaks.py`), `TableOfContentsHandler` (`handlers/toc.py`)
- [x] **Structural blocks**: `HeadingHandler` (`handlers/heading.py`), `TableHandler` (`handlers/table.py`), `CodeBlockHandler` (`handlers/code_block.py`), `ListHandler` (`handlers/list_handler.py`)
- [x] **Inline formatting**: `BoldHandler`/`ItalicHandler`/`StrikethroughHandler`/`UnderlineHandler`/`InlineCodeHandler` (`handlers/inline_format.py`), `LinkHandler` (`handlers/link.py`)
- [x] **Complex handlers**: `StyleHandler` (`handlers/style.py`), `SuggestionHandler` (`handlers/suggestion.py`), `RichLinkHandler` (`handlers/rich_link.py`), `ImageHandler` (`handlers/image.py`), `FootnoteRefHandler` (`handlers/footnote.py`), `HeaderHandler`/`FooterHandler` (`handlers/header_footer.py`), `TextRunHandler` (`handlers/text_run.py`)
- [x] Refactored `markdown_serializer.py` from ~900 lines to ~230-line orchestrator that walks Pydantic tree and delegates to handler registry
- [x] All existing 368 tests continue to pass after migration; backward-compatible private function re-exports maintained (`_apply_inline_formatting`, `_apply_link`, `_join_paragraphs`)

#### 3.4: Element Registry and Shared Constants ✅
- [x] Create `google_docs_markdown/element_registry.py`
- [x] Move heading level mappings (`HEADING_PREFIX`) from `heading.py`
- [x] Move glyph type sets (`ORDERED_GLYPH_TYPES`) from `block_grouper.py`
- [x] Move monospace font/color constants (`MONOSPACE_FONT`, `INLINE_CODE_COLOR`)
- [x] Move inline format marker definitions (`InlineMarker` enum, `INLINE_MARKER_TO_STYLE_FIELD`)
- [x] Move comment tag type to batchUpdate request type mapping (`TAG_TO_REQUEST_FIELD`)
- [x] Add `MD_HEADING_LEVEL_TO_STYLE`, `HEADING_STYLES`, `DEFAULT_LINK_COLOR`, `CODE_BLOCK_MARKER`
- [x] Both handlers and orchestrators import from here — all existing 423 tests pass

#### 3.5: Source Map ✅
- [x] Create `google_docs_markdown/source_map.py`
- [x] Define `SourceSpan` dataclass (md_start, md_end, api_start, api_end, tab_id, segment_id, kind, handler_type, style, tag_data)
- [x] Define `SpanKind` enum (TEXT, HEADING, LIST_ITEM, TABLE_CELL, CODE_LINE, WIDGET, SYNTAX, IMAGE, FOOTNOTE_REF, LINK, METADATA)
- [x] Define `SourceMapBuilder` with `record()`, `record_syntax()`, `advance()`, `set_segment()`, `build()`
- [x] Define `SourceMap` read-only view with `lookup(md_pos)`, `span_at()`, `spans_in_range()`, `visible_spans()`, `syntax_spans()`
- [x] Add `source_map` field to `SerContext`
- [x] Add `serialize_with_source_map()` to `MarkdownSerializer` — records structural spans from API indices
- [x] Unit tests: 20 tests in `test_source_map.py` — builder, recording, syntax vs visible spans, lookup, range queries

#### 3.6: Markdown Deserializer (Handlers + Orchestrator) ✅
Implemented `deserialize()` on each handler, plus new `markdown_deserializer.py` orchestrator.

- [x] Add `markdown-it-py>=4.0.0` dependency
- [x] Implement `deserialize()` on handler classes:
  - `PersonHandler` → `InsertPersonRequest` with email from tag data
  - `DateHandler` → `InsertDateRequest` with format/locale/timezone from tag data, merged with `dateDefaults`
  - `StyleHandler` → `InsertText` + `UpdateTextStyleRequest` (color, background-color, font-size, font-family, baseline-offset, small-caps)
  - `RichLinkHandler` → `InsertText` + `UpdateTextStyleRequest` with link (no `insertRichLink` API)
  - `PageBreakHandler` → `InsertPageBreakRequest`
  - `ColumnBreakHandler` → `InsertTextRequest` (vertical tab)
  - `SectionBreakHandler` → `InsertSectionBreakRequest` with section type
  - `TableOfContentsHandler` → `InsertTextRequest` placeholder
  - `ImageHandler` → `InsertInlineImageRequest`
- [x] Create `google_docs_markdown/markdown_deserializer.py` orchestrator:
  - Parse markdown via `markdown-it-py` AST (with strikethrough + table plugins enabled)
  - Walk block-level tokens: headings, paragraphs, lists, code fences, tables, horizontal rules, HTML blocks
  - Inline formatting: bold, italic, strikethrough, underline (`<u>`), links, inline code, images
  - Title/subtitle detection via `<!-- title -->`/`<!-- subtitle -->` comment tags
  - Comment-tag dispatch: block-level `html_block` and inline `html_inline` tags parsed via `comment_tags.parse_tags()` and dispatched through `HandlerRegistry.match_deserialize()`
  - Metadata handling: `parse_metadata()` → `DocumentContext.from_metadata()` → `DeserContext`
  - `tabId` and `segmentId` propagated to all Location/Range objects
  - Convenience function `deserialize()` for one-call usage
  - Returns `list[Request]` for `batchUpdate`
- [x] Added `StyleHandler` and `SuggestionHandler` to `HandlerRegistry.default()` for deserialization dispatch
- [x] Unit tests: 33 tests in `test_markdown_deserializer.py` — headings (1-6), paragraphs, bold/italic/strikethrough/underline, inline code, links, lists (ordered + unordered), code blocks, tables, person/date/page-break/section-break tags, metadata stripping, tab/segment IDs, style tags, rich-link tags, edge cases, index progression

#### 3.7: Create New Documents (Uploader — Create Flow)
- [x] Handle document creation (`documents().create()`) — `GoogleDocsClient.create_document`
- [x] Handle document updates (`documents().batchUpdate()`) — `GoogleDocsClient.batch_update`
- [ ] Create `google_docs_markdown/uploader.py`
- [ ] `Uploader.create_from_markdown(title, markdown_text)` → create blank doc via `GoogleDocsClient.create_document()`, then apply deserialized requests via `batch_update()`
- [ ] `Uploader.create_from_directory(directory_path)` → create multi-tab doc from directory structure (directory name = title, `.md` files = tabs, subdirectories = nested tabs via `addDocumentTab`)
- [ ] This validates the full deserializer pipeline end-to-end without any diffing complexity
- [ ] Integration tests: create doc from markdown, download it back, compare output

#### 3.8: Diff Engine
- [ ] Create `google_docs_markdown/diff_engine.py`
- [ ] Text-level diffing using `difflib.SequenceMatcher` (upgrade to Myers diff if needed)
- [ ] Strip metadata blocks before diffing (use existing `metadata.strip_metadata()`)
- [ ] Produce `list[DiffOp]` with markdown position ranges (`kind`, `md_start`, `md_end`, `new_text`)
- [ ] Source map integration: `DiffOp` positions → API index positions via `SourceMap.lookup()`
- [ ] Handler-aware request generation: look up handler for changed spans via source map, call `handler.deserialize()` at the insertion point
- [ ] No-change detection: if diff produces zero ops, skip API call entirely
- [ ] Per-tab diffing for multi-tab documents (diff each tab independently)
- [ ] Request ordering: deletions end-to-start, insertions start-to-end, widget inserts, style updates (any order)
- [ ] Unit tests: insertions, deletions, replacements, no-change detection, widget boundary preservation

#### 3.9: Update Existing Documents (Uploader — Update Flow)
- [ ] Add `Uploader.update_document(document_id, local_markdown, tab_id=None)` method
- [ ] Pipeline: fetch doc → serialize with source map → diff against local → generate requests → batch_update
- [ ] Widget preservation: unchanged regions produce zero ops (U+E907 boundaries survive naturally)
- [ ] Widget recreation: when diff detects changed person/date regions, generate `InsertPerson`/`InsertDate` from comment tag metadata
- [ ] One-way element fallback: convert `RichLink` metadata to regular hyperlinks on upload (no `insertRichLink` API); preserve `AutoText` and `Equation` in-place only
- [ ] `Uploader.update_from_directory(document_id, directory_path)` → per-tab updates, skip unchanged tabs
- [ ] Handle `tabId` in Location/Range objects for multi-tab documents
- [ ] Handle `segmentId` in Location/Range objects for headers/footers/footnotes
- [ ] Handle directory structure (all documents treated as multi-tab)
- [ ] Integration tests: round-trip (download → edit → upload → download → compare)

#### 3.10: CLI, Python API, and Final Testing
- [x] Add `upload` command to CLI (options: `--create`, `--overwrite`, `--local-path`; **handler not implemented**)
- [x] Implement `list-tabs` CLI command (calls `Downloader.get_tabs()`, prints nested tab tree with IDs) ✅
- [x] Unit tests for `create_document` and `batch_update` on both transport and client (mocked Google API)
- [ ] Implement `upload` command body (call uploader; remove `NotImplementedError`)
- [ ] `--create` flag → create flow (3.7); default → update flow (3.9)
- [ ] `--overwrite` flag → force update even when no changes detected
- [ ] `--tab` flag → update specific tab only
- [ ] Handle directory path input, auto-detect tab structure from directory contents
- [ ] Diff preview CLI option (optional, can defer to Phase 7 polish)
- [ ] Per-tab diff summary for multi-tab documents
- [ ] Python API: `Uploader.upload(document_id, markdown_content, tab_name=None)`, `upload_from_directory(document_id, directory_path)`, `create(markdown_content, title=None)`, `create_from_directory(directory_path, document_title=None)` — return created/updated document ID
- [ ] Round-trip tests: download → upload → download (single-tab and multi-tab)
- [ ] Widget preservation tests: U+E907 boundaries survive update cycle
- [ ] Widget recreation tests: person/date round-trip through comment tags
- [ ] RichLink fallback tests: rich link → hyperlink on upload
- [ ] No-change detection tests: download → immediate upload → zero API calls
- [ ] Partial update tests: change one paragraph, verify only that region is patched
- [ ] Multi-tab partial tests: change one tab, verify other tabs untouched
- [ ] Create-from-markdown tests with all element types
- [ ] Source map accuracy tests against known fixture documents
- [ ] Batch update ordering tests (verify indices are preserved)
- [ ] Deterministic upload tests (same markdown → same doc structure)

**Deliverable:** Can upload Markdown to Google Docs (create and update), with widget-preserving atomic edits, handler-based ser/deser architecture, change detection, and full multi-tab support

---

### Phase 4: Advanced Feature Preservation (Residual)
**Goal:** Handle any remaining Google Docs features not covered by Phase 2.6

**Note:** The bulk of the metadata strategy and non-Markdown element handling has been folded into Phase 2.6. This phase covers only features discovered during Phase 2-3 implementation that require additional work.

#### 4.1: Additional Feature Discovery
- [ ] Identify any Google Docs features not covered by Phase 2.6 during real-world testing
- [ ] Handle edge cases in metadata serialization/deserialization discovered during Phase 3 (upload)
- [ ] Handle embedded objects (charts, drawings) if encountered

#### 4.2: Metadata Round-Trip Refinement
- [ ] Ensure HTML comment metadata survives download → edit → upload cycle
- [ ] Ensure companion JSON metadata stays in sync with Markdown content
- [ ] Handle metadata conflicts (e.g., user edits HTML comment, breaking JSON structure)

#### 4.3: Testing
- [ ] End-to-end round-trip tests with all advanced features
- [ ] Verify feature preservation across multiple download/upload cycles

**Deliverable:** Robust handling of all Google Docs features in Markdown round-trips

---

### Phase 5: Advanced Tab Features
**Goal:** Enhanced features for multi-tab document workflows

**API Support:** The Google Docs API provides full CRUD for tabs via batchUpdate: `addDocumentTab` (create with `title`, `index`, `parentTabId` for nested tabs), `deleteTab` (cascading delete of child tabs), and `updateDocumentTabProperties` (rename, set icon emoji). This makes all tab management features below fully achievable.

#### 5.1: Tab Management
- [ ] Add CLI command to list tabs in a document
- [ ] Add CLI command to create new tabs (via `addDocumentTab` — supports `parentTabId` for nested tab creation)
- [ ] Add CLI command to rename tabs (via `updateDocumentTabProperties`)
- [ ] Add CLI command to delete tabs with confirmation (via `deleteTab` — note: cascades to child tabs)

#### 5.2: Bulk Operations
- [ ] Support bulk download of multiple multi-tab documents
- [ ] Support bulk upload of multiple directories
- [ ] Add progress indicators for multi-tab operations

#### 5.3: Tab Synchronization
- [ ] Detect when tabs are added/removed in Google Docs
- [ ] Handle tab reordering (via `addDocumentTab` with `index`)
- [ ] Sync tab names between local files and Google Docs (via `updateDocumentTabProperties`)

#### 5.4: Testing
- [ ] Test tab management operations (CRUD via batchUpdate)
- [ ] Test bulk operations
- [ ] Test synchronization scenarios

**Deliverable:** Advanced tab management and bulk operations for multi-tab documents

**Note:** Basic multi-tab support (detection, download, upload) is implemented in Phases 1-3. This phase adds advanced management features. All tab CRUD operations have full API backing.

---

### Phase 6: Image Storage Integration
**Goal:** Upload images to public storage (S3, GCS)

#### 6.1: Storage Backends
- [ ] Create `google_docs_markdown/storage/` module
- [ ] Implement S3 backend
- [ ] Implement GCS backend
- [ ] Create abstract base class for storage backends

#### 6.2: Configuration
- [ ] Create `google_docs_markdown/config.py`
- [ ] Support global config (`~/.config/google-docs-markdown/config.yaml`)
- [ ] Support per-document config (`my_doc/config.yaml`)
- [ ] Support CLI flag overrides

#### 6.3: Image Upload Workflow
- [ ] Scan Markdown for local image references
- [ ] Upload local images to configured storage
- [ ] Replace local references with public URLs
- [ ] Update Markdown files with public URLs

#### 6.4: CLI Integration
- [ ] Add `--image-storage` flag
- [ ] Add `--image-bucket` flag
- [ ] Support configuration via config files

#### 6.5: Testing
- [ ] Test S3 upload
- [ ] Test GCS upload
- [ ] Test URL replacement
- [ ] Test configuration precedence

**Deliverable:** Images can be uploaded to S3/GCS with URL replacement

---

### Phase 7: Polish & Documentation
**Goal:** Production-ready tool with comprehensive docs

#### 7.1: Error Handling
- [ ] Improve error messages
- [ ] Add helpful troubleshooting hints
- [ ] Handle edge cases gracefully

#### 7.2: CLI Polish
- [ ] Add progress indicators for long operations
- [ ] Improve help text
- [ ] Add verbose/debug flags
- [ ] Add dry-run mode

#### 7.3: Documentation
- [ ] Update README with all features
- [ ] Add API documentation
- [ ] Add examples for common use cases
- [ ] Document configuration options
- [ ] Add troubleshooting guide

#### 7.4: Performance
- [ ] Profile and optimize slow operations
- [ ] Add caching where appropriate
- [ ] Optimize API call usage

#### 7.5: Testing
- [ ] Increase test coverage
- [ ] Add performance tests
- [ ] Add end-to-end tests

**Deliverable:** Production-ready tool

---

## Implementation Order Recommendation

**Start with Phase 1** - Get basic download working first, including multi-tab support from the start. This provides immediate value and validates the approach. Multi-tab handling is a core requirement, not an add-on.

**Important**: Before implementing the downloader (Phase 1.4), complete the Pydantic model generation work (Phase 1.3). This foundational work enables attribute-based access to API responses and provides the models needed for markdown serialization.

**Then Phase 2** - Enhance download to handle complex documents.

**Then Phase 3** - Add upload capability with per-element handler architecture, change detection, and diffing. Phase 3 is structured with careful dependency ordering: context layer and handler infrastructure first (3.1-3.2), then migrate existing serialization into handlers (3.3), then build shared constants (3.4) and source map (3.5), then implement deserialization (3.6), validate via create flow (3.7), build diff engine (3.8), compose into update flow (3.9), and wire up CLI/API (3.10). The create-before-update ordering validates the deserializer end-to-end before layering diffing on top.

**Phases 4-6** can be done in parallel or based on priority:
- **Phase 4** is residual — most content absorbed into Phase 2.6. Only needed if additional features are discovered during Phase 3.
- **Phase 5** if advanced tab management features are needed (basic tab support is already in Phases 1-3)
- **Phase 6** if image storage is needed

**Phase 7** should be ongoing throughout development, but final polish happens at the end.

## Technical Decisions

1. **Data Models**: Use Pydantic models instead of TypedDicts
   - **Decision**: Generate Pydantic models from `google-api-python-client-stubs` using automated script
   - **Benefits**: Attribute access (`doc.title`), runtime validation, better developer experience
   - **See**: `docs/TECH_SPEC.md` Section 5.4 for model details (historical strategy doc archived at `docs/archive/PYDANTIC_STRATEGY.md`)

2. **Transport/Client Separation**: Two-layer API architecture
   - **`GoogleDocsTransport`** (`transport.py`): Low-level layer that talks to the Google Docs API and returns raw dicts. Uses `googleapiclient._apis.docs.v1` type stubs for typing.
   - **`GoogleDocsClient`** (`client.py`): High-level layer that composes the transport and returns typed Pydantic models. Most consumers should use this.
   - **Rationale**: Keeps raw API access available for scripts like `download_test_doc.py` that need unmodified JSON, while providing typed models for application code.

3. **Per-Element Handler Architecture**: Bidirectional ser/deser via handler classes
   - **Decision**: Each document element concept (heading, bold, person chip, table, etc.) gets its own handler class with both `serialize()` and `deserialize()` methods. A central orchestrator dispatches to handlers in each direction.
   - **Categories**: `TagElementHandler` (comment-tag elements like Person, Date, Style), `BlockElementHandler` (structural blocks like Heading, Table, CodeBlock, List), `InlineFormatHandler` (bold, italic, strikethrough, etc.)
   - **Benefits**: Element format knowledge lives in one place (single source of truth for both ser and deser), adding new elements means adding one handler file, handlers compose with source map and diff engine.
   - **Context**: Three-layer context — `DocumentContext` (frozen, document defaults; populated from `DocumentTab` or metadata block), `SerContext`/`DeserContext` (mutable, direction-specific traversal state)
   - **See**: `docs/TECH_SPEC.md` Section 5.11

4. **Markdown Parser**: Choose library for parsing Markdown
   - **Decision**: `markdown-it-py` (modern, extensible)
   - **Note**: Used by the **deserializer orchestrator** to parse markdown into AST tokens for handler dispatch. The **create-new-document** flow uses full AST parsing. The **update-existing-document** flow uses text-level diffing (via diff engine) but routes changed fragments through handler deserialization for request generation.

5. **CLI Framework**: Choose CLI framework
   - **Decision**: `typer` (modern, type-safe, leverages Python type hints)
   - **Note**: Use `Annotated` from `typing` to type CLI arguments and options (recommended by typer)

6. **Diff Algorithm**: Choose diffing library
   - **Decision**: Start with `difflib.SequenceMatcher` (built-in), upgrade to Myers diff if needed
   - **Note**: Operates on text, not structure. Compares canonical (serialized) markdown against local markdown. Source map translates diff positions to API indices. Handler registry generates the appropriate `batchUpdate` requests for changed spans.

7. **Storage Libraries**: Choose libraries for S3/GCS
   - **Decision**: 
     - S3: `boto3`
     - GCS: `google-cloud-storage`
   - Both are standard choices

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test full workflows with real Google Docs
- **Determinism Tests**: Verify same input → same output
- **Round-Trip Tests**: Download → Upload → Download should match

## Example Document Testing

Use the example document from `example_markdown/google_doc_urls.txt`:
- Contains headings (H1-H6)
- Contains images
- Contains tables
- Contains code blocks
- Contains formatting (bold, italic, colors)
- Contains lists
- Contains item pickers/chips

This document should be used for testing throughout development.

**Multi-Tab Testing:**
- Test with multi-tab Google Docs (if available)
- Verify directory structure creation
- Verify tab name to filename mapping
- Test selective tab download
- Test uploading to specific tabs
- Test round-trip conversion for multi-tab documents

## Next Steps

**Completed:**
- ✅ Phase 1.1: Project Setup
- ✅ Phase 1.2: Google Docs API Transport & Client (transport for raw dicts, client for Pydantic models, with comprehensive unit tests for both)
- ✅ Phase 1.3: Pydantic model generation and transport/client integration (`get_document`, `create_document`, `batch_update`)
- ✅ Phase 1.4: Basic Downloader — `MarkdownSerializer` (visitor-style traversal of `DocumentTab` → `Body` → `Paragraph` → `TextRun`, handles headings/bold/italic/whitespace normalization) and `Downloader` (multi-tab orchestration, recursive nested tabs, directory/file I/O, filename sanitization). Location/Range `tabId`/`segmentId` deferred to Phase 3.
- ✅ Phase 1.5: CLI Download Command — `download` wired to `Downloader.download_to_files()`, supports `--output`/`-o`, `--tabs`/`-t`, `--force`/`-f`, file conflict handling, stale file cleanup, error handling, summary output
- ✅ Phase 1.6: Python API — `Downloader.download()`, `download_to_files(overwrite=)`, `get_document_title()`, `get_tabs()` (returns `TabSummary` tree), `get_nested_tabs()`, `extract_document_id()`, plus `find_stale_files()` and `remove_empty_dirs()` utility functions
- ✅ Phase 1.7: Testing — 355+ unit tests (serializer 102, block grouper 15, downloader 47, CLI 21, transport 15, client 6, models 7, setup 45, gcloud 21, comment_tags 16, metadata 10, phase26_serializer 48, plus others) + 12 integration tests with live API (`tests/test_integration.py`, `@pytest.mark.integration`)

- ✅ Phase 2.1: Simple inline/block elements — links (`TextStyle.link.url` → `[text](url)`), strikethrough (`~~text~~`), underline (`<u>text</u>`, suppressed for links), rich links (`[title](uri)`), horizontal rules (`---`), footnote references (`[^N]`) with footnote content from `DocumentTab.footnotes`
- ✅ Phase 2.2: Lists — introduced `block_grouper.py` pre-processing pass that groups consecutive bullet paragraphs into `ListBlock` objects. Supports ordered (DECIMAL, ALPHA, ROMAN variants), unordered (GLYPH_TYPE_UNSPECIFIED), and nested lists (4-space indent per nesting level). Different `listId`s produce separate list blocks.
- ✅ Phase 2.3: Tables — `_visit_table` in `markdown_serializer.py` renders `Table` → Markdown pipe tables. Handles `tableRowStyle.tableHeader` for header detection (falls back to first row), multi-paragraph cells (`<br>` join), formatted cell content (reuses `_collect_paragraph_text`), pipe escaping.
- ✅ Phase 2.4: Code blocks — `CodeBlock` dataclass in `block_grouper.py` groups paragraphs between U+E907 bookend markers. `_visit_code_block` in `markdown_serializer.py` renders as bare fenced code blocks (no language identifier — API doesn't expose it). U+E907 stripped from all `TextRun.content` (handles both code block markers and smart chip placeholders). Monospace font helper (`_paragraph_has_monospace_font`) supports Roboto Mono, Courier New, Consolas, Source Code Pro.
- ✅ Phase 2.5: Images — `_visit_inline_object` in `markdown_serializer.py` renders `InlineObjectElement` → `![alt](contentUri)`. Looks up `DocumentTab.inlineObjects[objectId]` for embedded object properties. Uses `description` or `title` for alt text. Currently references Google-hosted `contentUri` directly; local image download deferred to Phase 6 (image storage integration).
- ✅ Phase 2.6: Non-Markdown Elements — Full annotation system via wrapping HTML comments (`<!-- type: {json} -->content<!-- /type -->`). Handles: Person, DateElement, AutoText, Equation, SectionBreak, ColumnBreak, PageBreak, TableOfContents, RichLink metadata, TITLE/SUBTITLE markers, style comments (color, font, size), suggestion markers, chip placeholders (U+E907), headers/footers. Embedded metadata block at bottom of markdown file for document-level properties. New modules: `comment_tags.py`, `metadata.py`. 74 new tests.

- ✅ Phase 3.1: Context Layer — `DocumentContext` frozen dataclass with dual factories (`from_document_tab()`, `from_metadata()`), `SerContext` and `DeserContext` mutable contexts. `optional_color_to_hex` utility. 32 new tests.
- ✅ Phase 3.2: Handler Infrastructure — `ElementHandler` ABC, `TagElementHandler`/`BlockElementHandler`/`InlineFormatHandler` subclasses, `HandlerRegistry` with three-level dispatch. 23 new tests.
- ✅ Phase 3.3: Handler Migration — 17 handler files (`person.py`, `date.py`, `breaks.py`, `toc.py`, `heading.py`, `table.py`, `code_block.py`, `list_handler.py`, `inline_format.py`, `link.py`, `style.py`, `suggestion.py`, `rich_link.py`, `image.py`, `footnote.py`, `header_footer.py`, `text_run.py`). `markdown_serializer.py` refactored from ~900 lines to ~230-line orchestrator. All 423 tests pass.

**In Progress:**
- **Phase 3:** Upload, Change Detection & Diffing — Phases 3.1–3.3 complete. Remaining: element registry (3.4), source map (3.5), deserializer (3.6), create flow (3.7), diff engine (3.8), update flow (3.9), CLI/API wiring (3.10).

**Up Next:**
- **Phase 3.4:** Element Registry — shared constants (heading levels, glyph types, monospace fonts, format markers)
- 3.5: Source map — `SourceMapBuilder` integrated with handler serialization, `SourceMap.lookup()` for md-position-to-API-index translation
- 3.6: Markdown deserializer — implement `deserialize()` on each handler + new `markdown_deserializer.py` orchestrator with `markdown-it-py`
- 3.7: Create flow — `uploader.py` with `create_from_markdown()` and `create_from_directory()` (validates deserializer without diffing)
- 3.8: Diff engine — text-level diffing, source map integration, handler-aware request generation, no-change detection, per-tab diffing
- 3.9: Update flow — surgical update pipeline composing source map + diff engine + handlers; widget preservation; widget recreation via `insertPerson`/`insertDate`
- 3.10: CLI, Python API, final testing — wire up `upload` command, round-trip tests, widget tests, partial update tests
- Location/Range `tabId` and `segmentId` handling (deferred from Phase 1.4)
- U+E907 index preservation for round-trip fidelity (deferred from Phase 2.4)

