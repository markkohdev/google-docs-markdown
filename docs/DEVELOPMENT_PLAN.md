# Google Docs Markdown - Development Plan

**Created:** 2026-01-08  
**Last Updated:** 2026-03-26 (Phase 2.1–2.3 completed — inline elements, lists with block grouper, tables)  
**Status:** Phase 1 — **complete** (1.1–1.7 done; remaining 1.4 items deferred to Phase 3 by design); **Phase 2.1–2.3 — complete**; **Phase 3 — in progress** (client + CLI skeleton; no `uploader` / deserializer yet)

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
- [x] Add interactive prompts for missing arguments (document URL prompted by typer)
- [x] Update `pyproject.toml` entry point (`google-docs-markdown` and `gdm` aliases)

#### 1.6: Python API - Basic Interface ✅
- [x] Create `Downloader` class in `downloader.py` (named `Downloader`, not `GoogleDocMarkdown`)
- [x] Implement `download(document_id)` → returns dict of tab_path → markdown (all docs treated as multi-tab)
- [x] Implement `download_to_files(document_id, output_path)` → saves to directory, returns dict of tab_path → file Path
- [x] Implement `get_document_title(document_id)` → returns title (available via `GoogleDocsClient.get_document().title`)
- [x] Implement `get_tabs(document_id)` → returns list of `TabSummary` objects with tab names/IDs/nesting (available via `Document.tabs`)
- [x] Implement `get_nested_tabs(document_id, tab_id)` → returns nested `TabSummary` children within a tab
- [x] `extract_document_id(url)` → available as `GoogleDocsClient.extract_document_id()` (static method)

#### 1.7: Testing ✅
- [x] Test with example Google Doc from `example_markdown/google_doc_urls.txt` (integration — requires live API) ✅
- [x] Test with multi-tab Google Doc (integration — requires live API; skips nested-tab assertions when live doc lacks nested tabs) ✅
- [x] Create unit tests for transport and client (including tab detection) ✅
- [x] Create unit tests for `MarkdownSerializer` (36 tests: headings, formatting, fixtures, determinism) ✅
- [x] Create unit tests for `Downloader` (32 tests: single-tab, multi-tab, nested, filtering, disk I/O, `get_document_title`, `get_tabs`, `get_nested_tabs`) ✅
- [x] Create unit tests for CLI `download` command (4 tests: wiring, flags, error handling) ✅
- [x] Create unit tests for CLI `list-tabs` command (3 tests: wiring, nested, error handling) ✅
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

#### Phase 2.4: Code Blocks (U+E907 boundary markers + monospace font heuristic)

Google Docs code blocks are NOT a formal API element. They are detected via a combination of `U+E907` boundary markers and monospace font. See `TECH_SPEC.md` Section 5.9 for full details.

##### 2.4.1: Code Block Detection and Serialization
- [ ] Detect code block boundaries via `U+E907` (`\ue907`) bookend characters in `TextRun.content`
- [ ] Confirm with monospace font (`Roboto Mono`) on interior paragraph `TextRun`s
- [ ] Group consecutive monospace paragraphs into a single fenced code block
- [ ] Emit bare fenced code blocks with no language identifier (API does not expose language)
- [ ] Preserve `U+E907` positions in internal representation for round-trip fidelity
- [ ] Strip `U+E907` characters from Markdown output (not meaningful to users)

##### 2.4.2: Testing
- [ ] Unit tests with fixture code block data
- [ ] Test detection of code block boundaries
- [ ] Test that non-code-block `U+E907` (smart chips) is handled separately

#### Phase 2.5: Images

##### 2.5.1: Image Support
- [ ] Handle `InlineObjectElement` → `![alt](url)`
- [ ] Look up image data in `DocumentTab.inlineObjects[objectId].inlineObjectProperties.embeddedObject`
- [ ] Download images from `contentUri` to local `imgs/` directory within the document's output folder
- [ ] Generate Markdown image references with local paths
- [ ] Handle image alt text (from `description` if available)

##### 2.5.2: Testing
- [ ] Unit tests for image reference generation
- [ ] Test image download and local path generation

#### Phase 2.6: Non-Markdown Elements, Metadata Strategy, and Suggestions

This sub-phase handles Google Docs features that have no direct Markdown equivalent. It absorbs the metadata strategy work originally planned for Phase 5.

##### 2.6.1: Metadata Strategy Decision
- [ ] Decide and implement the full representation strategy for non-Markdown elements (HTML comments, companion JSON, or both)
- [ ] Define metadata format for each element type
- [ ] Decide on `RichLink` metadata — currently serialized as plain `[title](uri)` (Phase 2.1), indistinguishable from a regular link. Decide whether to add inline metadata (e.g., `[title](uri)<!-- richLink: {"mimeType": "...", "richLinkId": "..."} -->`) for user visibility, upload warnings, and future-proofing if `insertRichLink` is ever added to the API. Note: no `insertRichLink` batchUpdate exists today, so rich links fall back to regular hyperlinks on upload regardless.

##### 2.6.2: Non-Markdown Element Handling

**First-class ParagraphElements with full API read support** (see `TECH_SPEC.md` Section 5.9.1 for the full API capability matrix):
- [ ] Handle `Person` mentions — first-class `ParagraphElement` with `personProperties.email` + `.name`; serialize as `<!-- person: {...} -->` inline comment. **Round-trippable** via `insertPerson` batchUpdate (see Phase 3.1)
- [ ] Handle `DateElement` — first-class `ParagraphElement` with full `dateElementProperties` (format, locale, timezone, timestamp, displayText); serialize as `<!-- date: {...} -->` inline comment. **Round-trippable** via `insertDate` batchUpdate (see Phase 3.1)
- [ ] Handle `RichLink` metadata per 2.6.1 decision — update `_visit_rich_link` in `markdown_serializer.py` if metadata is added
- [ ] Handle `AutoText` (`type`: PAGE_NUMBER, PAGE_COUNT) — readable but **no write API** (`insertAutoText` does not exist); must be preserved in-place during upload
- [ ] Handle equations (`Equation`) — opaque element (no content exposed by API, no `insertEquation`); serialize as placeholder comment

**Other non-Markdown elements:**
- [ ] Handle colored text (`foregroundColor`, `backgroundColor`)
- [ ] Handle column breaks (`ColumnBreak`)
- [ ] Handle section breaks (`SectionBreak` → HTML comment with section style info)
- [ ] Handle table of contents (`TableOfContents` → mark as auto-generated)
- [ ] Handle `TITLE` and `SUBTITLE` named styles — currently serialized as lossy Markdown equivalents (`TITLE` → `#` same as `HEADING_1`, `SUBTITLE` → italic `*text*`). Add metadata (per 2.6.1 strategy) so they can be distinguished from `HEADING_1` / italic text and round-tripped on upload via `updateParagraphStyle` with the correct `namedStyleType`

##### 2.6.3: Suggestion Handling
- [ ] Serialize Google Docs suggestions (`suggestedInsertionIds` / `suggestedDeletionIds`) with visible markers (e.g., HTML comments around suggested text) so users can distinguish suggested vs. accepted content

##### 2.6.4: Headers, Footers, and Footnotes
- [ ] Extract headers from document (per-tab for multi-tab documents)
- [ ] Extract footers from document (per-tab for multi-tab documents)
- [ ] Serialize headers/footers (as separate files or metadata)

##### 2.6.5: Testing
- [ ] Test with example doc containing all element types
- [ ] Test metadata round-trip (serialize then parse)
- [ ] Test suggestion markers
- [ ] Verify all features work across tabs in multi-tab documents

**Deliverable:** Can download complex Google Docs with tables, images, lists, code blocks, links, footnotes, headers/footers, section breaks, TOC, suggestions, smart chips, and all paragraph elements, with full support for multi-tab documents

---

### Phase 3: Upload (Markdown → Docs)
**Goal:** Convert Markdown back to Google Docs, including multi-tab documents

**Key Architecture Decision:** The upload strategy uses **atomic, surgical edits** rather than full document reconstruction. See `TECH_SPEC.md` Sections 5.9-5.10 for the rationale (preserving U+E907 widget state via edit-in-place).

**Progress (2026-03-25):** `GoogleDocsClient` exposes `create_document` and `batch_update` with Pydantic models (unit tested). CLI `upload` command exists as a stub. No `uploader.py` or working pipeline yet.

#### 3.1: Uploader -- Update Existing Documents (Atomic Edit Approach)
- [x] Handle document creation (`documents().create()`) — `GoogleDocsClient.create_document`
- [x] Handle document updates (`documents().batchUpdate()`) — `GoogleDocsClient.batch_update`
- [ ] Create `google_docs_markdown/uploader.py`
- [ ] **Update flow:** Fetch current document → serialize to Markdown via `MarkdownSerializer` → text-diff against local Markdown → map diff ranges to document indices → generate surgical `batchUpdate` requests
- [ ] Map diff operations to API requests: `DeleteContentRange` for deletions, `InsertText` for insertions, `UpdateParagraphStyle`/`UpdateTextStyle` for formatting changes
- [ ] Preserve U+E907 widget boundaries (code blocks, opaque smart chips) by targeting only text content indices
- [ ] **Widget recreation:** Parse `<!-- person: {...} -->` comments and generate `insertPerson` requests with `personProperties`; parse `<!-- date: {...} -->` comments and generate `insertDate` requests with `dateElementProperties` (see `TECH_SPEC.md` Section 5.10.3)
- [ ] **One-way element fallback:** Convert `RichLink` metadata to regular hyperlinks on upload (no `insertRichLink` API); preserve `AutoText` and `Equation` in-place only
- [ ] Process batch updates in correct order: deletions (end-to-start), insertions (start-to-end), widget inserts, style updates (any order)
- [ ] Handle `tabId` in Location/Range objects for multi-tab documents
- [ ] Handle `segmentId` in Location/Range objects for headers/footers/footnotes
- [ ] Handle directory structure (all documents treated as multi-tab)
- [ ] Handle uploading to specific tabs in multi-tab documents
- [ ] Handle nested tab structures when uploading

#### 3.2: Uploader -- Create New Documents
- [ ] Parse Markdown into a sequence of `batchUpdate` `Request` objects (may use `markdown-it-py` for tokenization)
- [ ] Map Markdown elements to API requests: headings, lists, tables, images, formatting, links
- [ ] Map inline `<!-- person: {...} -->` comments to `insertPerson` requests and `<!-- date: {...} -->` comments to `insertDate` requests
- [ ] Support creating documents from directory structure (directory name → document, files → tabs, subdirectories → nested tabs)

#### 3.3: CLI - Upload & List-Tabs Commands
- [x] Add `upload` command to CLI (options: `--create`, `--overwrite`, `--local-path`; **handler not implemented**)
- [x] Implement `list-tabs` CLI command (calls `Downloader.get_tabs()`, prints nested tab tree with IDs) ✅
- [ ] Implement `upload` command body (call uploader; remove `NotImplementedError`)
- [ ] Support `--create` flag for new documents (wired to create flow)
- [ ] Support `--overwrite` flag (force update even when no changes detected)
- [ ] Handle directory path input, auto-detect tab structure from directory contents
- [ ] Add `--tab` flag to specify which tab to update (for multi-tab docs)

#### 3.4: Python API - Upload Methods
- [ ] Add `upload(document_id, markdown_content, tab_name=None)` method
- [ ] Add `upload_from_directory(document_id, directory_path)` method for multi-tab
- [ ] Add `create(markdown_content, title=None)` method (creates new document)
- [ ] Add `create_from_directory(directory_path, document_title=None)` method
- [ ] Return created/updated document ID

#### 3.5: Testing
- [x] Unit tests for `create_document` and `batch_update` on both transport and client (mocked Google API)
- [ ] Test round-trip: download → upload → download (should match) for single-tab and multi-tab
- [ ] Test that U+E907 widget boundaries are preserved during update
- [ ] Test `insertPerson` round-trip: download Person → serialize to comment → upload recreates Person widget
- [ ] Test `insertDate` round-trip: download DateElement → serialize to comment → upload recreates date widget
- [ ] Test RichLink fallback: download RichLink → serialize to `[title](uri)` → upload creates regular hyperlink
- [ ] Test creating new documents from Markdown
- [ ] Test creating multi-tab documents from directory structure
- [ ] Test updating existing documents (verify surgical edits)
- [ ] Test batch update ordering (verify indices are preserved)
- [ ] Verify deterministic upload (same markdown → same doc structure)

**Deliverable:** Can upload Markdown to Google Docs (create and update), with widget-preserving atomic edits and full multi-tab support

---

### Phase 4: Change Detection & Diffing
**Goal:** Only upload changes, handle concurrent edits

#### 4.1: Diff Engine
- [ ] Create `google_docs_markdown/diff_engine.py`
- [ ] Implement normalized representation for comparison
- [ ] Use diff algorithm (Myers diff or similar) for text comparison
- [ ] Detect changes at multiple granularities:
  - Character level
  - Word level
  - Paragraph level
  - Element level (formatting, structure)
- [ ] Support per-tab diffing for multi-tab documents

#### 4.2: Change Detection
- [ ] Compare local Markdown with current online version
- [ ] Generate minimal set of update operations
- [ ] Handle insertions, deletions, modifications
- [ ] Detect when no changes exist (skip API call)
- [ ] For multi-tab documents: detect changes per-tab
- [ ] Only update tabs that have changed

#### 4.3: Upload Integration
- [ ] Integrate diff engine into upload process
- [ ] Always download current version before uploading
- [ ] Generate only necessary `batchUpdate` requests
- [ ] Handle conflicts gracefully (detect concurrent edits)
- [ ] For multi-tab: only update changed tabs, preserve unchanged tabs

#### 4.4: CLI Enhancements
- [ ] Show diff preview before upload (optional flag)
- [ ] Show per-tab diff summary for multi-tab documents
- [ ] Prompt user after upload to pull latest version (default: yes)

#### 4.5: Testing
- [ ] Test no-change detection (download → upload without changes) for single-tab
- [ ] Test no-change detection for multi-tab (all tabs unchanged)
- [ ] Test partial updates (change one paragraph) for single-tab
- [ ] Test partial updates (change one tab) for multi-tab
- [ ] Test concurrent edit scenarios for both single and multi-tab
- [ ] Test tab-specific change detection

**Deliverable:** Smart change detection, only uploads differences (works efficiently for multi-tab documents)

---

### Phase 5: Advanced Feature Preservation (Residual)
**Goal:** Handle any remaining Google Docs features not covered by Phase 2.6

**Note:** The bulk of the metadata strategy and non-Markdown element handling has been folded into Phase 2.6. This phase covers only features discovered during Phase 2-3 implementation that require additional work.

#### 5.1: Additional Feature Discovery
- [ ] Identify any Google Docs features not covered by Phase 2.6 during real-world testing
- [ ] Handle edge cases in metadata serialization/deserialization discovered during Phase 3 (upload)
- [ ] Handle embedded objects (charts, drawings) if encountered

#### 5.2: Metadata Round-Trip Refinement
- [ ] Ensure HTML comment metadata survives download → edit → upload cycle
- [ ] Ensure companion JSON metadata stays in sync with Markdown content
- [ ] Handle metadata conflicts (e.g., user edits HTML comment, breaking JSON structure)

#### 5.3: Testing
- [ ] End-to-end round-trip tests with all advanced features
- [ ] Verify feature preservation across multiple download/upload cycles

**Deliverable:** Robust handling of all Google Docs features in Markdown round-trips

---

### Phase 6: Advanced Tab Features
**Goal:** Enhanced features for multi-tab document workflows

**API Support:** The Google Docs API provides full CRUD for tabs via batchUpdate: `addDocumentTab` (create with `title`, `index`, `parentTabId` for nested tabs), `deleteTab` (cascading delete of child tabs), and `updateDocumentTabProperties` (rename, set icon emoji). This makes all tab management features below fully achievable.

#### 6.1: Tab Management
- [ ] Add CLI command to list tabs in a document
- [ ] Add CLI command to create new tabs (via `addDocumentTab` — supports `parentTabId` for nested tab creation)
- [ ] Add CLI command to rename tabs (via `updateDocumentTabProperties`)
- [ ] Add CLI command to delete tabs with confirmation (via `deleteTab` — note: cascades to child tabs)

#### 6.2: Bulk Operations
- [ ] Support bulk download of multiple multi-tab documents
- [ ] Support bulk upload of multiple directories
- [ ] Add progress indicators for multi-tab operations

#### 6.3: Tab Synchronization
- [ ] Detect when tabs are added/removed in Google Docs
- [ ] Handle tab reordering (via `addDocumentTab` with `index`)
- [ ] Sync tab names between local files and Google Docs (via `updateDocumentTabProperties`)

#### 6.4: Testing
- [ ] Test tab management operations (CRUD via batchUpdate)
- [ ] Test bulk operations
- [ ] Test synchronization scenarios

**Deliverable:** Advanced tab management and bulk operations for multi-tab documents

**Note:** Basic multi-tab support (detection, download, upload) is implemented in Phases 1-3. This phase adds advanced management features. All tab CRUD operations have full API backing.

---

### Phase 7: Image Storage Integration
**Goal:** Upload images to public storage (S3, GCS)

#### 7.1: Storage Backends
- [ ] Create `google_docs_markdown/storage/` module
- [ ] Implement S3 backend
- [ ] Implement GCS backend
- [ ] Create abstract base class for storage backends

#### 7.2: Configuration
- [ ] Create `google_docs_markdown/config.py`
- [ ] Support global config (`~/.config/google-docs-markdown/config.yaml`)
- [ ] Support per-document config (`my_doc/config.yaml`)
- [ ] Support CLI flag overrides

#### 7.3: Image Upload Workflow
- [ ] Scan Markdown for local image references
- [ ] Upload local images to configured storage
- [ ] Replace local references with public URLs
- [ ] Update Markdown files with public URLs

#### 7.4: CLI Integration
- [ ] Add `--image-storage` flag
- [ ] Add `--image-bucket` flag
- [ ] Support configuration via config files

#### 7.5: Testing
- [ ] Test S3 upload
- [ ] Test GCS upload
- [ ] Test URL replacement
- [ ] Test configuration precedence

**Deliverable:** Images can be uploaded to S3/GCS with URL replacement

---

### Phase 8: Polish & Documentation
**Goal:** Production-ready tool with comprehensive docs

#### 8.1: Error Handling
- [ ] Improve error messages
- [ ] Add helpful troubleshooting hints
- [ ] Handle edge cases gracefully

#### 8.2: CLI Polish
- [ ] Add progress indicators for long operations
- [ ] Improve help text
- [ ] Add verbose/debug flags
- [ ] Add dry-run mode

#### 8.3: Documentation
- [ ] Update README with all features
- [ ] Add API documentation
- [ ] Add examples for common use cases
- [ ] Document configuration options
- [ ] Add troubleshooting guide

#### 8.4: Performance
- [ ] Profile and optimize slow operations
- [ ] Add caching where appropriate
- [ ] Optimize API call usage

#### 8.5: Testing
- [ ] Increase test coverage
- [ ] Add performance tests
- [ ] Add end-to-end tests

**Deliverable:** Production-ready tool

---

## Implementation Order Recommendation

**Start with Phase 1** - Get basic download working first, including multi-tab support from the start. This provides immediate value and validates the approach. Multi-tab handling is a core requirement, not an add-on.

**Important**: Before implementing the downloader (Phase 1.4), complete the Pydantic model generation work (Phase 1.3). This foundational work enables attribute-based access to API responses and provides the models needed for markdown serialization.

**Then Phase 2** - Enhance download to handle complex documents.

**Then Phase 3** - Add upload capability, including multi-tab support. This completes the bidirectional conversion for both single and multi-tab documents.

**Then Phase 4** - Add change detection. This is critical for the tool's efficiency and conflict handling. Change detection should work per-tab for multi-tab documents.

**Phases 5-7** can be done in parallel or based on priority:
- **Phase 5** is now residual -- most content absorbed into Phase 2.6. Only needed if additional features are discovered.
- **Phase 6** if advanced tab management features are needed (basic tab support is already in Phases 1-3)
- **Phase 7** if image storage is needed

**Phase 8** should be ongoing throughout development, but final polish happens at the end.

## Technical Decisions

1. **Data Models**: Use Pydantic models instead of TypedDicts
   - **Decision**: Generate Pydantic models from `google-api-python-client-stubs` using automated script
   - **Benefits**: Attribute access (`doc.title`), runtime validation, better developer experience
   - **See**: `docs/TECH_SPEC.md` Section 5.4 for model details (historical strategy doc archived at `docs/archive/PYDANTIC_STRATEGY.md`)

2. **Transport/Client Separation**: Two-layer API architecture
   - **`GoogleDocsTransport`** (`transport.py`): Low-level layer that talks to the Google Docs API and returns raw dicts. Uses `googleapiclient._apis.docs.v1` type stubs for typing.
   - **`GoogleDocsClient`** (`client.py`): High-level layer that composes the transport and returns typed Pydantic models. Most consumers should use this.
   - **Rationale**: Keeps raw API access available for scripts like `download_test_doc.py` that need unmodified JSON, while providing typed models for application code.

3. **Markdown Parser**: Choose library for parsing Markdown
   - **Decision**: `markdown-it-py` (modern, extensible)
   - **Note**: May only be needed for the **create-new-document** flow. The **update-existing-document** flow uses Markdown text diffing (not parsing) to generate surgical `batchUpdate` requests. Serialization (Pydantic → Markdown) builds strings directly using visitor-style dispatch.

4. **CLI Framework**: Choose CLI framework
   - **Decision**: `typer` (modern, type-safe, leverages Python type hints)
   - **Note**: Use `Annotated` from `typing` to type CLI arguments and options (recommended by typer)

5. **Diff Algorithm**: Choose diffing library
   - **Decision**: Start with `difflib` (built-in), upgrade if needed
   - **Note**: Can leverage Pydantic model comparison for structural diffing of Google Docs API objects

6. **Storage Libraries**: Choose libraries for S3/GCS
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
- ✅ Phase 1.4: Basic Downloader — `MarkdownSerializer` (visitor-style traversal of `DocumentTab` → `Body` → `Paragraph` → `TextRun`, handles headings/bold/italic/whitespace normalization) and `Downloader` (multi-tab orchestration, recursive nested tabs, directory/file I/O, filename sanitization). Unsupported elements (tables, images, lists, etc.) are silently skipped — those are Phase 2. Location/Range `tabId`/`segmentId` deferred to Phase 3.
- ✅ Phase 1.5: CLI Download Command — `download` wired to `Downloader.download_to_files()`, supports `--output`/`-o`, `--tabs`/`-t`, error handling, summary output
- ✅ Phase 1.6: Python API — `Downloader.download()`, `download_to_files()`, `get_document_title()`, `get_tabs()` (returns `TabSummary` tree), `get_nested_tabs()`, `extract_document_id()`
- ✅ Phase 1.7: Testing — 241 unit tests (serializer 90, block grouper 10, downloader 32, CLI 13, transport 10, client 6, models 7, setup 27, gcloud 19, plus 27 more across other modules) + 12 integration tests with live API (`tests/test_integration.py`, `@pytest.mark.integration`)

- ✅ Phase 2.1: Simple inline/block elements — links (`TextStyle.link.url` → `[text](url)`), strikethrough (`~~text~~`), underline (`<u>text</u>`, suppressed for links), rich links (`[title](uri)`), horizontal rules (`---`), footnote references (`[^N]`) with footnote content from `DocumentTab.footnotes`
- ✅ Phase 2.2: Lists — introduced `block_grouper.py` pre-processing pass that groups consecutive bullet paragraphs into `ListBlock` objects. Supports ordered (DECIMAL, ALPHA, ROMAN variants), unordered (GLYPH_TYPE_UNSPECIFIED), and nested lists (4-space indent per nesting level). Different `listId`s produce separate list blocks.
- ✅ Phase 2.3: Tables — `_visit_table` in `markdown_serializer.py` renders `Table` → Markdown pipe tables. Handles `tableRowStyle.tableHeader` for header detection (falls back to first row), multi-paragraph cells (`<br>` join), formatted cell content (reuses `_collect_paragraph_text`), pipe escaping. 10 unit tests + 2 fixture tests.

**In Progress:**
- **Phase 3:** Upload — client primitives and CLI `upload`/`list-tabs` scaffold done; **Markdown deserializer**, **`uploader.py`**, directory/tab mapping, and working upload CLI still to do

**Up Next:**
- **Phase 2.4-2.6:** Code blocks (U+E907 detection), images, non-Markdown elements + metadata strategy

**Remaining Phase 3 Tasks:**
- `uploader.py` with atomic-edit strategy (diff Markdown strings → map to API indices → surgical batchUpdate), widget recreation via `insertPerson`/`insertDate` for round-trippable elements, RichLink-to-hyperlink fallback, create-new-document flow (may use `markdown-it-py`), multi-tab directory support, Python upload API, round-trip and integration tests
- Location/Range `tabId` and `segmentId` handling (deferred from Phase 1.4)

