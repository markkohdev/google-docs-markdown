# Google Docs Markdown - Technical Specification

**Document Version:** 1.6.0  
**Date:** 2026-01-08  
**Last Updated:** 2026-03-26 (Phase 2.6 complete: non-markdown element annotations, style comments, embedded metadata, suggestions, headers/footers)  
**Authors:** Mark Koh  
**Status:** Active

## 1. Introduction

This project is a Python package and CLI tool for downloading and editing Google Docs as Markdown using the Google Docs API. The tool enables bidirectional conversion between Google Docs and Markdown format, allowing users to edit documents locally in Markdown while maintaining synchronization with Google Docs.

The tool leverages the [Google Docs API](https://googleapis.github.io/google-api-python-client/docs/dyn/docs_v1.documents.html) via the `google-api-python-client` library to interact with documents programmatically.  This documentation has been downloaded locally for reference at `resources/google_docs_api_reference.md`.

## 2. Goals

The primary goals of this project are:

1. **Bidirectional Conversion**: Enable seamless conversion between Google Docs and Markdown formats
2. **Deterministic Behavior**: Ensure consistent, reproducible conversions (same input always produces same output)
3. **Conflict Resolution**: Handle concurrent edits gracefully by detecting and merging changes intelligently
4. **Developer Experience**: Provide both CLI and Python API interfaces for different use cases
5. **Resource Efficiency**: Optimize for LLM contexts by managing images efficiently

## 3. Requirements

### 3.1 Functional Requirements

#### Core Functionality
- **FR-1**: Download Google Docs as Markdown
  - Convert Google Docs documents to Markdown format
  - Preserve document structure, formatting, and content
  - Treat every document as a multi-tab document (even single-tab ones)
  - Handle nested tab structures recursively (tabs can contain both content and child tabs)
  - Download each tab into a separate markdown file
  - Create a folder based on the document title (or user-provided output directory)
  - Save markdown files as `{Doc Title}/{Tab Name}.md` (e.g., `My Doc/Tab 1.md` for single-tab, `My Doc/Tab 1.md` and `My Doc/Tab 2.md` for multi-tab)
  - Support selective tab download via CLI flags

- **FR-2**: Upload Markdown to Google Docs
  - Convert Markdown content back to Google Docs format
  - Support both updating existing documents and creating new documents
  - Preserve Markdown structure and formatting in Google Docs

- **FR-4**: Image Management
  - Extract images from Google Docs during download — **implemented**: images are serialized as `![alt](contentUri)` referencing Google-hosted URLs
  - Store images locally in an `imgs` directory within the document's output folder (e.g., `My Doc/imgs/`) — **planned** (Phase 7)
  - Upload local images to a configurable public storage service (S3, GCS, etc.) — **planned** (Phase 7)
  - Inline image URLs in Markdown files with public URLs — **planned** (Phase 7)
  - Replace local image references with public URLs after upload — **planned** (Phase 7)

- **FR-5**: Change Detection and Diffing
  - Compare local Markdown content with online Google Docs content
  - Detect differences at granular levels (character, word, paragraph, structural element)
  - Only submit changes that differ from the online version
  - Prevent unnecessary updates when content is unchanged (unless `--overwrite` flag is used)

- **FR-6**: CLI Interface
  - Provide intuitive command-line interface for common operations
  - Support interactive prompts for document URLs/IDs
  - Enable configuration via command-line flags and config files

- **FR-7**: Python API
  - Provide programmatic Python API for integration into other tools
  - Support both high-level convenience methods and low-level API access

### 3.2 Non-Functional Requirements

- **NFR-1 Performance**: The system should download and upload documents efficiently, minimizing API calls and processing time
- **NFR-2 Security**: Protect user credentials and data, support secure authentication via Application Default Credentials (ADC)
- **NFR-3 Reliability**: Handle API errors gracefully, provide clear error messages, and support retry logic for transient failures
- **NFR-4 Usability**: CLI should be intuitive with clear help text and error messages
- **NFR-5 Maintainability**: Code should be modular, well-documented, and follow Python best practices
- **NFR-6 Determinism**: Same document input must always produce identical Markdown output; same Markdown input must produce identical Google Docs structure (within API constraints)

## 4. Architecture

### 4.1 System Overview

The tool is organized into several distinct components that work together to provide the core functionality:

```
┌─────────────────────────────────────────────┐
│   CLI (cli.py, typer)                       │  User-facing command-line interface
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│   Downloader / Uploader                     │  High-level orchestration
│   ┌──────────────────────────────────────┐  │
│   │  Downloader (downloader.py)          │  │  Fetches doc, serializes tabs, writes files
│   │  MarkdownSerializer (markdown_       │  │  Pydantic DocumentTab → Markdown string
│   │    serializer.py)                    │  │
│   │  Uploader (uploader.py) [planned]    │  │  Markdown → batchUpdate requests
│   └──────────────────────────────────────┘  │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│   API Client Layer                          │
│   ┌──────────────────────────────────────┐  │
│   │  GoogleDocsClient (client.py)        │  │  Typed client (Pydantic models)
│   │  GoogleDocsTransport (transport.py)  │  │  Raw API transport (dicts)
│   │  Data Models (models/)               │  │  Pydantic models for API objects
│   └──────────────────────────────────────┘  │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────┐
│ Google Docs │  External API
│    API      │
└─────────────┘
```

### 4.2 Component Responsibilities

- **CLI** (`cli.py`): Parses command-line arguments via `typer`, orchestrates operations, provides user feedback. Commands: `download` (with `--force`, file conflict handling, stale cleanup), `upload` (stub), `diff` (stub), `list-tabs`, `setup`.
- **Downloader** (`downloader.py`): Orchestrates fetching a `Document` via `GoogleDocsClient`, iterating tabs recursively, serializing each tab via `MarkdownSerializer`, and writing `.md` files to a directory structure. Supports selective tab download via `tab_names` filter, file conflict detection (`FileConflictError`), stale file cleanup (`find_stale_files`), and empty directory removal (`remove_empty_dirs`).
- **MarkdownSerializer** (`markdown_serializer.py`): Converts a single `DocumentTab` Pydantic model to a Markdown string. Uses a block-grouper pre-processing pass (`block_grouper.py`) to group list items and code blocks before visitor-style traversal. Handles all Google Docs element types: headings, paragraphs, bold/italic/strikethrough/underline formatting, links, rich links (with metadata), horizontal rules, footnotes, ordered/unordered/nested lists, tables (pipe format), code blocks (U+E907 boundary detection), images, Person mentions, DateElements, AutoText, Equations, SectionBreaks, PageBreaks, ColumnBreaks, TableOfContents, style annotations (color, font, size), suggestion markers, chip placeholders, and headers/footers.
- **CommentTags** (`comment_tags.py`): Serialization and parsing for wrapping HTML comment annotations (`<!-- type: {json} -->content<!-- /type -->`). Provides `TagType` enum, `opening_tag()`, `closing_tag()`, `wrap_tag()`, and `parse_tags()`.
- **Metadata** (`metadata.py`): Handles the embedded metadata block at the bottom of markdown files (`<!-- google-docs-metadata ... -->`). Provides `serialize_metadata()`, `parse_metadata()`, and `strip_metadata()`.
- **BlockGrouper** (`block_grouper.py`): Pre-processing pass that groups `StructuralElement` lists into typed blocks: `ListBlock` (consecutive bullet paragraphs), `CodeBlock` (paragraphs between U+E907 bookend markers). All other elements pass through unchanged.
- **Uploader** (`uploader.py`, planned): Will convert Markdown back to Google Docs via surgical `batchUpdate` requests. See Section 5.9 for the atomic-edit strategy.
- **GoogleDocsClient** (`client.py`): High-level typed client that returns Pydantic models. Composes `GoogleDocsTransport`. Most consumers (CLI, downloader, uploader) should use this.
- **GoogleDocsTransport** (`transport.py`): Low-level transport that handles authentication, API requests/responses, error handling, and retry logic. Returns raw dicts as received from the API. Used directly for scripts that need unmodified API responses (e.g., downloading test fixtures).
- **Data Models** (`models/`): Pydantic models representing Google Docs API response objects, enabling attribute-based access (`doc.title`) and runtime validation. Generated from `google-api-python-client-stubs` via `scripts/generate_models.py`. Organized into `document.py`, `elements.py`, `styles.py`, `common.py`, `requests.py`, `responses.py`.

## 5. Detailed Design

### 5.1 Deterministic Conversion

The tool must produce deterministic outputs to ensure consistency and enable reliable diffing:

- **Download Determinism**: The same Google Doc must always produce identical Markdown output
  - Normalize whitespace and formatting consistently
  - Preserve document structure in a canonical order
  - Handle edge cases (empty documents, special characters, etc.) consistently

- **Upload Determinism**: The same Markdown input must produce identical Google Docs structure
  - Parse Markdown in a consistent manner
  - Apply formatting rules deterministically
  - Handle ambiguous Markdown constructs consistently

- **No-Change Detection**: If a document is downloaded and immediately uploaded without modification, no API calls should be made (unless `--overwrite` flag is provided)
  - This requires accurate diffing to detect when content is truly unchanged

### 5.2 Change Detection and Diffing

The diff engine is critical for efficient updates and conflict resolution:

- **Granularity Levels**: The diff should operate at multiple levels:
  - **Character level**: For precise text changes
  - **Word level**: For word insertions/deletions
  - **Paragraph level**: For structural changes
  - **Element level**: For formatting, images, tables, etc.

- **Diff Algorithm**: 
  - Convert both Markdown and Google Docs content to a normalized intermediate representation
  - Use appropriate diffing algorithms (e.g., Myers diff algorithm) to identify changes
  - For Google Docs API objects, leverage Pydantic model comparison capabilities for efficient structural diffing
  - Generate minimal set of update operations needed to transform online content to match local content

- **Conflict Handling**:
  - Before uploading, always download the current online version
  - Compare local Markdown with online content
  - Generate only the changes needed (insertions, deletions, modifications)
  - After upload, prompt user to pull latest version (default: yes) to sync any concurrent online edits

### 5.3 Update Operations

- **Batch Updates**: Use the `batchUpdate` endpoint to submit multiple changes atomically
- **Granular Changes**: Submit changes at the smallest possible granularity to:
  - Minimize conflicts with concurrent online edits
  - Enable precise change tracking
  - Reduce risk of overwriting unrelated content

- **Update Ordering**: Process batch updates in a specific order to preserve indices:
  1. **Deletions**: Process from end to start (preserves indices for earlier operations)
  2. **Insertions**: Process from start to end (doesn't affect later insertions)
  3. **Updates**: Can be processed in any order (don't affect indices)
  
  This ordering is critical because deletions and insertions change document indices, and processing them in the wrong order can cause index errors.

- **Update Modes**:
  - **Update Mode**: Modify existing document (default)
  - **Create Mode**: Create new document from Markdown (via `create` endpoint)
  - **Overwrite Mode**: Force update even when no changes detected (via `--overwrite` flag)

### 5.4 Data Models

- **Purpose**: Use Pydantic models to represent Google Docs API response objects, enabling attribute-based access (`doc.title` instead of `doc.get("title")`) and runtime validation

- **Benefits**:
  - **Better Developer Experience**: Attribute access (`doc.title`) instead of dictionary access (`doc.get("title")`)
  - **Runtime Validation**: Pydantic validates API responses at runtime, catching schema mismatches early
  - **Type Safety**: Full type checking support with IDE autocomplete
  - **Flexibility**: Easy to add computed properties, validation logic, and helper methods
  - **Serialization**: Built-in JSON/dict conversion for API compatibility
  - **Model Comparison**: Pydantic models enable efficient structural diffing strategies

- **Implementation Strategy**:
  - **Model Generation**: Automatically generate all Pydantic models from `google-api-python-client-stubs` using a generation script (`scripts/generate_models.py`)
  - **Model Organization**: Organize models in `google_docs_markdown/models/` module (document.py, elements.py, styles.py, etc.)
  - **Transport/Client Separation**: `GoogleDocsTransport` returns raw API dicts; `GoogleDocsClient` wraps the transport and converts to/from Pydantic models using `model_validate()` and `model_dump(exclude_none=True)`
  - **Base Configuration**: All models inherit from `GoogleDocsBaseModel` with shared Pydantic configuration
  - **Field Names**: Preserve camelCase field names to match API exactly (e.g., `documentId`, `namedStyleType`)

- **Key Types**:
  - `Document` - Container for all tabs in a document
  - `DocumentTab` - Fundamental document object representing a single tab (can contain both content and child tabs)
  - `Body` - Document body containing structural elements
  - `Paragraph`, `Table`, `TextRun`, etc. - Element types used throughout the document structure

- **Markdown Conversion**:
  - **Serialization (Pydantic → Markdown)**: `MarkdownSerializer` uses a two-stage pipeline: (1) `block_grouper.py` groups `StructuralElement` lists into typed blocks (`ListBlock`, `CodeBlock`, or pass-through `StructuralElement`), then (2) visitor-style dispatch on optional fields (`if element.paragraph:`, `if element.textRun:`) traverses the Pydantic model tree and builds Markdown strings directly. No markdown library needed. Note: the models use optional-field composition (not class hierarchies), so dispatch is via field presence checks, not `isinstance()`. Block-level dispatch uses `isinstance()` on the block-grouper dataclasses.
  - **Currently serialized elements**: headings (H1–H6, Title with `<!-- title -->`, Subtitle with `<!-- subtitle -->`), paragraphs, bold, italic, strikethrough, underline, links, rich links (with `<!-- rich-link -->` metadata), horizontal rules, footnotes, ordered/unordered/nested lists, tables (pipe format), code blocks (U+E907 detection), images (`InlineObjectElement` → `![alt](contentUri)`), Person (`<!-- person -->` wrapping), DateElement (`<!-- date -->` wrapping), AutoText, Equation, SectionBreak, PageBreak, ColumnBreak, TableOfContents, style annotations (`<!-- style -->` for non-default colors/fonts/sizes), suggestion markers (`<!-- suggestion -->`), chip placeholders (`<!-- chip-placeholder -->`), headers/footers
  - **Deserialization (Markdown → API requests)**: For the **update** case, the approach is to diff two Markdown strings (serialized current doc vs. local file) and map changes back to API indices for surgical `batchUpdate` requests. For the **create** case, `markdown-it-py` may be used to parse Markdown into tokens and generate `batchUpdate` requests. See Section 5.9 for details.

- **Note**: Pydantic models provide both type checking and runtime validation. When using `GoogleDocsClient`, API responses are converted to Pydantic models automatically, enabling attribute access throughout the codebase. When using `GoogleDocsTransport` directly, raw dicts are returned for maximum fidelity (useful for test fixtures, debugging, etc.).

### 5.5 Image Management Workflow

The image management system handles images throughout the document lifecycle:

**Upload Flow**:
1. Scan Markdown for image references
2. Identify images that need to be uploaded (not already public URLs)
3. Upload local images to configured storage service (S3, GCS, etc.)
4. Replace local image references in Markdown with public URLs
5. Upload Markdown with public image URLs to Google Docs
6. After successful upload, replace local image files with references to public URLs (or update Markdown to use public URLs)

**Configuration**:
- Storage service configuration should be:
  - Configurable globally via config file (e.g., `~/.config/google-docs-markdown/config.yaml`)
  - Overridable per-document via document-folder-specific config (e.g: `My Doc/config.yaml`, alongside the markdown files within the document folder)
  - Overridable per-command execution via CLI flags
- Supported storage backends: S3, Google Cloud Storage, or other public URL providers

### 5.6 Tab Handling and Output Directory Structure

- **Fundamental Approach**: Treat every Google Doc as a multi-tab document, even if it only has a single tab
  - The API client always requests `includeTabsContent=True` to ensure consistent tab structure
  - Single-tab documents are handled the same way as multi-tab documents (just with one tab)

- **Tab Structure**: Google Doc tabs are nested - tabs can have both content AND child tabs simultaneously
  - Each `DocumentTab` contains:
    - `body` - The main content of the tab
    - `headers[]` - Header segments for the tab
    - `footers[]` - Footer segments for the tab
    - `footnotes[]` - Footnote segments for the tab
    - `tabs[]` (optional) - Child tabs nested within this tab
  - This nested structure must be handled recursively when processing documents

- **Data Model**: Use `DocumentTab` as the fundamental document object
  - `Document` serves as the container for all top-level tabs
  - Each `DocumentTab` represents a single tab and can be processed independently
  - When processing nested tabs, recursively handle child tabs within each parent tab

- **Download Strategy**: 
  - Create a directory named after the document title (or user-provided output directory)
  - Download each tab (including nested tabs) as a separate markdown file named after the tab within this directory
  - Example: Document "My Doc" with tabs "Tab 1", "Tab 2" → `My Doc/Tab 1.md`, `My Doc/Tab 2.md`
  - For nested tabs, use a naming convention that reflects the hierarchy (e.g., `Tab 1/Subtab A.md`)
- **Selective Download**: Support `--tabs` flag to download specific tabs
- **Upload Strategy**: When uploading, handle tab structure (including nested tabs) appropriately
- **Tab Context**: Maintain `tabId` in Location/Range objects when working with multi-tab documents

### 5.7 Headers, Footers, and Footnotes

Google Docs supports headers, footers, and footnotes as separate document segments:

- **Headers**: Reusable header content that can be linked to sections. Each tab in a multi-tab document can have its own headers.
- **Footers**: Reusable footer content that can be linked to sections. Each tab in a multi-tab document can have its own footers.
- **Footnotes**: Separate segment for footnote content. Footnotes are referenced inline via `FootnoteReference` elements and stored in a `footnotes[]` array.

**Handling Strategy**:
- **Download**: Extract headers, footers, and footnotes as separate content segments
  - Serialize headers/footers as separate files (e.g., `header.md`, `footer.md`) or include in metadata
  - Extract footnote references (`[^1]`) and footnote content separately
  - For multi-tab documents, handle headers/footers per-tab
- **Upload**: Upload header/footer content to appropriate segments using `segmentId` in Location/Range objects
  - Create footnote segments and link footnote references appropriately
  - Maintain segment context when uploading content

**Segment IDs**: The Google Docs API uses `segmentId` in Location/Range objects to specify which segment (header, footer, footnote, or body) an operation targets. Empty `segmentId` indicates the document body.

### 5.8 Handling Google Docs Features Not Supported in Markdown

Markdown has limited support for many advanced Google Docs features. The tool must serialize and deserialize these features in a way that preserves functionality while maintaining editability where appropriate.

#### 5.8.1 Serialization Strategy (Implemented — Phase 2.6)

**Status:** Implemented in `comment_tags.py` and `metadata.py`.

The tool uses a consistent **wrapping HTML comment pattern** for all non-markdown elements:

```
<!-- type: {json_data} -->visible content<!-- /type -->
```

Self-closing variant for elements with no visible content:

```
<!-- type: {json_data} -->
```

**Design Principles:**
- **Content editability:** Display text is visible in rendered markdown; metadata is in the comment tags
- **Self-contained files:** No sidecar files; document-level metadata is embedded as an HTML comment at the bottom of the markdown
- **Round-trip fidelity:** Enough metadata to reconstruct elements without destroying existing formatting
- **Non-default-only style annotations:** Style comments only emitted for properties that differ from the document's named style defaults

**Element Annotation Formats (Implemented):**

| Element | Format | Round-trip |
|---------|--------|------------|
| Person | `<!-- person: {"email": "x@y.com"} -->Name<!-- /person -->` | Yes (`insertPerson`) |
| Date | `<!-- date: {"format": "...", ...} -->displayText<!-- /date -->` | Yes (`insertDate`) |
| Style | `<!-- style: {"color": "#FF0000"} -->text<!-- /style -->` | Yes (`updateTextStyle`) |
| Suggestion (insert) | `<!-- suggestion: {"id": "...", "type": "insertion"} -->text<!-- /suggestion -->` | Preserve-in-place |
| Suggestion (delete) | `<!-- suggestion: {"id": "...", "type": "deletion"} -->text<!-- /suggestion -->` | Preserve-in-place |
| Rich Link | `<!-- rich-link: {"mimeType": "..."} -->[title](uri)<!-- /rich-link -->` | Fallback to hyperlink |
| Section break | `<!-- section-break: {"type": "..."} -->` (mid-doc only) | Preserve-in-place |
| Page break | `<!-- page-break -->` | Preserve-in-place |
| Column break | `<!-- column-break -->` | Preserve-in-place |
| TOC | `<!-- table-of-contents -->` | Auto-generated |
| AutoText | `<!-- auto-text: {"type": "PAGE_NUMBER"} -->` | Preserve-in-place |
| Equation | `<!-- equation -->` | Preserve-in-place |
| Chip placeholder | `<!-- chip-placeholder -->` (U+E907 with no API data) | Preserve-in-place |
| Title marker | `<!-- title -->` before `# text` | Yes (`updateParagraphStyle`) |
| Subtitle marker | `<!-- subtitle -->` before `*text*` | Yes (`updateParagraphStyle`) |
| Header | `<!-- header: {"id": "..."} -->content<!-- /header -->` | Via `segmentId` |
| Footer | `<!-- footer: {"id": "..."} -->content<!-- /footer -->` | Via `segmentId` |

**Style Comment Details:**
- Style defaults extracted from NORMAL_TEXT named style (font, size, color)
- Heading text uses the heading's named style font-size as the expected size (not NORMAL_TEXT)
- Common Google Docs fonts (Arial, Roboto, etc.) suppressed from font-family annotations to reduce noise
- Style wraps OUTSIDE markdown formatting: `<!-- style: {...} -->**bold**<!-- /style -->`

**Embedded Metadata Block:**

Document-level properties stored as an HTML comment at the bottom of the markdown file:

```markdown
<!-- google-docs-metadata
{
  "documentId": "...",
  "tabId": "t.0",
  "revisionId": "...",
  "defaultStyles": {"fontFamily": "Proxima Nova", "fontSize": 11}
}
-->
```

Safety: `>` escaped as `\u003e` in JSON string values to prevent premature `-->` closure.

#### 5.8.2 Deserialization Strategy

When uploading Markdown back to Google Docs:

- **Parse Comment Tags**: The `comment_tags.parse_tags()` function extracts all comment tags from markdown text, returning structured `ParsedTag` objects with type, data, content, and position spans
- **Parse Metadata Block**: The `metadata.parse_metadata()` function extracts the embedded metadata JSON
- **Strip Metadata**: The `metadata.strip_metadata()` function removes the metadata block for content-only diffing
- **Widget Recreation**: For `<!-- person -->` tags → `insertPerson` requests; for `<!-- date -->` tags → `insertDate` requests
- **One-Way Elements**: `RichLink` falls back to regular hyperlink; `AutoText`/`Equation` preserved in-place only
- **Source Map Strategy**: At upload time, the serializer produces both canonical markdown and a source map (mapping markdown positions to API indices) from the current document. The diff operates on canonical vs. local markdown, and the source map translates diff positions to surgical `batchUpdate` operations.

#### 5.8.3 Examples

**Person Mention in Markdown** (round-trippable via `insertPerson`):
```markdown
Assigned to <!-- person: {"email": "john@example.com"} -->John Doe<!-- /person --> for review.
```

**Date Element in Markdown** (round-trippable via `insertDate`):
```markdown
Meeting on <!-- date: {"format": "DATE_FORMAT_ISO8601", "locale": "en", "timestamp": "2026-01-08T12:00:00Z"} -->2026-01-08<!-- /date -->.
```

**Styled Text** (round-trippable via `updateTextStyle`):
```markdown
<!-- style: {"color": "#FF0000", "background-color": "#FFFF00"} -->highlighted red text<!-- /style -->
```

**Rich Link** (falls back to regular hyperlink on upload):
```markdown
<!-- rich-link: {"mimeType": "application/vnd.google-apps.spreadsheet"} -->[Project Roadmap](https://docs.google.com/spreadsheets/d/abc123)<!-- /rich-link -->
```

### 5.9 U+E907 Widget Markers and Non-Text Element Handling

The Google Docs API uses the Unicode Private Use Area character `U+E907` as a placeholder for non-text elements within `TextRun.content`. From the API documentation:

> "The text of this run. Any non-text elements in the run are replaced with the Unicode character U+E907."

#### 5.9.1 Where U+E907 Appears

In practice, `U+E907` appears in two contexts:

1. **Code block widget boundaries**: A `TextRun` with `content="\ue907"` (typically Arial font) appears immediately before the first line of a code block, and another with `content="\ue907\n"` appears immediately after the last line. These represent the code block container widget (which holds internal state like the language label shown in the Google Docs UI).

2. **Opaque smart chip placeholders**: When a smart chip type has no dedicated `ParagraphElement` field in the API schema, a `U+E907` character appears in the adjacent `TextRun.content` as a placeholder. This applies to chip types like **status chips**, **file chips**, and **place chips** — none of which have a corresponding `ParagraphElement` field.

**Important distinction:** Several "smart chip" types are **NOT** U+E907 placeholders — they are first-class `ParagraphElement` fields with full structured data:

| Element | ParagraphElement Field | Read | Write (batchUpdate) |
|---|---|---|---|
| **Person** | `person` | Full: `personId`, `personProperties.email`, `personProperties.name`, `textStyle` | `insertPerson` with `personProperties` |
| **DateElement** | `dateElement` | Full: `dateElementProperties` (format, locale, timezone, timestamp, displayText) | `insertDate` with `dateElementProperties` |
| **RichLink** | `richLink` | Full: `richLinkProperties.title`, `.uri`, `.mimeType` | **No write API** — no `insertRichLink` request exists |
| **AutoText** | `autoText` | `type` (PAGE_NUMBER, PAGE_COUNT), `textStyle` | **No write API** — no `insertAutoText` request exists |
| **Equation** | `equation` | Opaque — only `suggestedDeletionIds`/`suggestedInsertionIds`, no content | **No write API** |

This means the atomic-edit upload strategy (Section 5.10) can leverage `insertPerson` and `insertDate` to **recreate** these widgets when needed, rather than only preserving them in place.

#### 5.9.2 Code Block Detection Strategy

**Status:** Implemented in Phase 2.4 (`block_grouper.py` and `markdown_serializer.py`).

Google Docs has no formal "code block" structural element in the API. Code blocks are detected using a combination of:

1. **U+E907 boundary markers**: A paragraph starting with `\ue907` marks the start; a paragraph ending with `\ue907` marks the end. All paragraphs between (inclusive) are grouped into a `CodeBlock` dataclass by `block_grouper.py`.
2. **Monospace font heuristic**: A helper `_paragraph_has_monospace_font()` detects monospace fonts (`Roboto Mono`, `Courier New`, `Consolas`, `Source Code Pro`). Currently available for validation but detection relies primarily on U+E907 markers.
3. **Output**: `_visit_code_block()` in `markdown_serializer.py` renders bare fenced code blocks (` ``` `) with no language identifier (the API does not expose the language label from the widget's internal state). All U+E907 characters are stripped from the output.
4. **U+E907 in non-code contexts**: `_visit_text_run()` also strips U+E907 from regular `TextRun.content`, handling smart chip placeholder occurrences outside code blocks.

#### 5.9.3 Implications for Upload (Atomic Edits)

The `U+E907` characters represent widget containers whose internal state (code block language, chip metadata, etc.) is invisible to the API. This has a critical implication for the upload strategy:

**Principle: Edit inside widget boundaries, don't reconstruct widgets.**

When uploading changes to a document that contains code blocks or smart chips:

1. The diff engine identifies changed text regions
2. `batchUpdate` requests target ONLY the text content indices within widget boundaries
3. The `U+E907` boundary characters are left untouched
4. Result: widget containers survive with their internal state (language labels, chip metadata) intact

This eliminates the need to reconstruct widgets from scratch -- we only edit the text content around and within them. When a widget has NOT changed, the diff produces zero operations for that range.

#### 5.9.4 Serialization Behavior

- **Download** (implemented): `U+E907` characters are handled in two places: (1) `_visit_code_block()` strips markers when rendering `CodeBlock` content, (2) `_visit_text_run()` replaces remaining `U+E907` occurrences with `<!-- chip-placeholder -->` to mark the position of smart chips without API data (status chips, file chips, place chips).
- **Upload** (planned): The diff engine must be aware of `U+E907` positions so it can avoid targeting them with edit operations. Preserving U+E907 index positions in the internal representation is deferred to Phase 3 (upload implementation).

### 5.10 Upload Strategy -- Atomic Edits, Not Reconstruction

The upload strategy differs fundamentally between updating an existing document and creating a new one.

#### 5.10.1 Update Existing Document (Common Case)

The approach is to **diff two Markdown strings** and map the diff back to API indices:

1. Fetch the current document via `GoogleDocsClient.get_document()`
2. Serialize it to Markdown using `MarkdownSerializer` (same code path as download)
3. Text-diff the serialized version against the user's local Markdown
4. Map diff ranges back to document indices (using index information from the original `Document` model)
5. Generate surgical `DeleteContentRange` + `InsertText` requests targeting ONLY changed regions
6. Widget boundaries (`U+E907` markers) are naturally preserved because unchanged regions produce no operations
7. For modified widget regions: use dedicated insert requests where available (see 5.10.3)
8. Process batch updates in correct order: deletions (end-to-start), insertions (start-to-end), widget inserts, style updates (any order)

This approach does NOT require parsing Markdown back into a `Document` Pydantic model. We don't reconstruct the document -- we patch it.

#### 5.10.2 Create New Document

For creating a brand-new document from Markdown:

1. Create a blank document via `GoogleDocsClient.create_document()`
2. Parse the Markdown (potentially using `markdown-it-py`) into a sequence of `batchUpdate` `Request` objects
3. Submit the requests to populate the document

This is a simpler one-directional pipeline. `markdown-it-py` may only be needed for this create flow, not the update flow.

#### 5.10.3 Widget Recreation on Upload

Some non-text elements have dedicated `batchUpdate` insert requests, enabling round-trip fidelity beyond simple text patching:

- **`insertPerson`**: Recreate person mentions from serialized `<!-- person: {...} -->` comments. Requires `personProperties.email` (and optionally `name`) plus a `location` index.
- **`insertDate`**: Recreate date elements from serialized `<!-- date: {...} -->` comments. Accepts full `dateElementProperties` (format, locale, timezone, timestamp) plus a `location` index.

Elements **without** dedicated insert requests cannot be recreated and must be handled differently:

- **`RichLink`**: No `insertRichLink` exists. Fall back to a regular hyperlink (`InsertText` + `UpdateTextStyle` with `link.url`). The rich link widget (with preview card) will be lost on upload.
- **`AutoText`**: No `insertAutoText` exists. Must be preserved in-place via atomic edits (don't delete/recreate). If an AutoText element is removed from the local Markdown, it cannot be restored.
- **`Equation`**: No `insertEquation` exists and no content is exposed by the API. Must be preserved in-place.

#### 5.10.4 Why Not Markdown -> Document Model?

Earlier design documents (now archived in `docs/archive/PYDANTIC_STRATEGY.md`) proposed a `MarkdownDeserializer` that would parse Markdown into a `Document` Pydantic model. This was abandoned because:

- The API needs `batchUpdate` `Request` objects, not a `Document` model
- The update case benefits from surgical edits that preserve widget state (U+E907 containers)
- Diffing at the Markdown text level is simpler and more robust than structural model comparison

## 6. Resources

- Example Google Doc URLs for testing are provided in `resources/example_markdown/google_doc_urls.txt`
- Google Docs API Documentation: https://googleapis.github.io/google-api-python-client/docs/dyn/docs_v1.documents.html
