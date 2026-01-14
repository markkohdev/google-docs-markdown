# Google Docs Markdown - Technical Specification

**Document Version:** 1.2.0  
**Date:** 2026-01-08  
**Last Updated:** 2026-01-08 (Updated to reflect Pydantic models approach)  
**Authors:** Mark Koh  
**Status:** Draft

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
  - Extract images from Google Docs during download
  - Store images locally in an `imgs` directory within the document's output folder (e.g., `My Doc/imgs/`)
  - Upload local images to a configurable public storage service (S3, GCS, etc.)
  - Inline image URLs in Markdown files with public URLs
  - Replace local image references with public URLs after upload

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
┌─────────────┐
│   CLI       │  User-facing command-line interface
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│   Python API (GoogleDocMarkdown)           │  High-level API for programmatic access
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│   Core Libraries                            │
│   ┌──────────────────────────────────────┐ │
│   │  Google Docs API Client              │ │  Low-level API wrapper
│   │  Downloader                          │ │  Converts Docs → Markdown
│   │  Uploader                            │ │  Converts Markdown → Docs
│   │  Diff Engine                         │ │  Compares content and generates updates
│   │  Image Manager                       │ │  Handles image extraction/upload
│   │  Data Models                         │ │  Python dataclasses for API objects
│   └──────────────────────────────────────┘ │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────┐
│ Google Docs │  External API
│    API      │
└─────────────┘
```

### 4.2 Component Responsibilities

- **CLI**: Parses command-line arguments, orchestrates operations, provides user feedback
- **Python API**: Provides high-level methods for common operations (download, upload, etc.)
- **Google Docs API Client**: Handles authentication, API requests/responses, error handling
- **Downloader**: Converts Google Docs API responses to Markdown format
- **Uploader**: Converts Markdown to Google Docs API batch update requests
- **Diff Engine**: Compares Markdown content with Google Docs content and generates minimal update operations
- **Image Manager**: Extracts images from documents, uploads to storage, manages local/public URL mapping
- **Data Models**: Pydantic models representing Google Docs API response objects, enabling attribute-based access (`doc.title`) and runtime validation

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
  - **API Integration**: Convert API dict responses to Pydantic models using `model_validate()`, convert back to dicts using `model_dump(exclude_none=True)`
  - **Base Configuration**: All models inherit from `GoogleDocsBaseModel` with shared Pydantic configuration
  - **Field Names**: Preserve camelCase field names to match API exactly (e.g., `documentId`, `namedStyleType`)

- **Key Types**:
  - `Document` - Container for all tabs in a document
  - `DocumentTab` - Fundamental document object representing a single tab (can contain both content and child tabs)
  - `Body` - Document body containing structural elements
  - `Paragraph`, `Table`, `TextRun`, etc. - Element types used throughout the document structure

- **Markdown Conversion**:
  - **Serialization (Pydantic → Markdown)**: Use Visitor Pattern to traverse Pydantic models and build Markdown strings directly (no markdown library needed)
  - **Deserialization (Markdown → Pydantic)**: Use `markdown-it-py` to parse Markdown into tokens, then convert tokens to Pydantic models
  - See `docs/PYDANTIC_STRATEGY.md` for detailed implementation patterns

- **Note**: Pydantic models provide both type checking and runtime validation. API responses are converted to Pydantic models immediately upon receipt, enabling attribute access throughout the codebase.

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

#### 5.8.1 Serialization Strategy

The tool uses two serialization approaches based on whether users might want to edit the feature directly in Markdown:

**1. Inline Comments (User-Editable Features)**

For features that users might want to edit directly in Markdown, serialize as HTML comments within the Markdown file:

- **Date Pickers**: Serialize as HTML comments with structured data
  - Example: `<!-- date-picker: {"type": "date", "value": "2026-01-08", "format": "YYYY-MM-DD"} -->`
  - Users can edit the date value directly in the comment
- **Specific Font Colors**: Serialize as HTML comments when color is non-standard or important
  - Example: `<!-- font-color: {"hex": "#FF5733", "name": "custom-orange"} -->`
  - Allows users to modify colors directly in Markdown
- **Other User-Editable Metadata**: Any feature where direct editing in Markdown is valuable

**2. JSON Metadata (Non-Editable or Complex Features)**

For features that are complex, rarely edited, or require structured data, serialize as JSON:

- **Person References**: Store as JSON with person IDs, names, and metadata
- **Complex Formatting**: Advanced formatting features that don't map to Markdown
- **Document-Level Metadata**: Features that apply to the entire document
- **Embedded Objects**: Complex embedded content (charts, drawings, etc.)

**JSON Storage Options**:

- **Option A: Bottom of Markdown File**: Append JSON as a code block at the end of the Markdown file
  - Format: `<!-- google-docs-metadata -->` followed by a JSON code block
  - Pros: Single file, easy to track
  - Cons: Can clutter the Markdown file
- **Option B: Companion JSON File**: Store in a separate `.json` file alongside the Markdown file
  - Format: `document.md` → `document.metadata.json`
  - Include comments in JSON (using JSON5 or JSONC format if supported)
  - Pros: Keeps Markdown clean, better for complex metadata
  - Cons: Two files to manage

**Recommendation**: Support both options, with companion JSON file as the default for complex documents. Allow users to configure preference via CLI flag or config file.

#### 5.8.2 Deserialization Strategy

When uploading Markdown back to Google Docs:

- **Parse Comments**: Extract HTML comments and convert back to Google Docs API format
- **Parse JSON**: Read JSON metadata (from file or bottom of Markdown) and apply to document
- **Preserve Order**: Maintain the order of features as they appear in the original document
- **Validation**: Validate that serialized data can be properly deserialized before upload

#### 5.8.3 Examples (Illustrative, actual implementations will depend on the API and the specific features being serialized/deserialized)

**Date Picker in Markdown**:
```markdown
The meeting is scheduled for <!-- date-picker: {"type": "date", "value": "2026-01-15", "format": "YYYY-MM-DD"} -->.
```

**Person Reference in Companion JSON** (`document.metadata.json`):
```json
{
  "personReferences": [
    {
      "id": "person123",
      "name": "John Doe",
      "email": "john@example.com",
      "position": {"startIndex": 45, "endIndex": 54}
    }
  ]
}
```

**Complex Metadata at Bottom of Markdown**:
```markdown
<!-- google-docs-metadata -->
```json
{
  "fontColors": {
    "custom-orange": "#FF5733"
  },
  "personReferences": [...]
}
```
```

## 6. Resources

- Example Google Doc URLs for testing are provided in `resources/example_markdown/google_doc_urls.txt`
- Google Docs API Documentation: https://googleapis.github.io/google-api-python-client/docs/dyn/docs_v1.documents.html
