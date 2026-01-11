# Google Docs Markdown - Development Plan

**Created:** 2026-01-08  
**Last Updated:** 2026-01-08 (Updated to reflect TypedDict approach and nested tab structure)  
**Status:** Phase 1 - In Progress (Tasks 1 & 2 Complete ✅)

## Overview

This document outlines the development plan for building the Google Docs Markdown tool. The plan is organized into phases, starting with a Minimum Viable Product (MVP) and progressively adding features.

**Important:** Multi-tab Google Docs support is integrated from Phase 1. All documents are treated as multi-tab documents (even single-tab ones), creating directory structures named after the document title, with each tab saved as a separate markdown file. Tabs can be nested (contain both content and child tabs), and this nested structure must be handled recursively.

Unit tests and documentation should be written for each component and function as they are implemented.

## Development Phases

### Phase 1: Foundation & MVP (Core Download with Multi-Tab Support)
**Goal:** Get basic Google Docs → Markdown conversion working, including multi-tab documents

**Tasks:**
1. **Project Setup** ✅
   - [x] Set up proper project structure
   - [x] Configure development dependencies (pytest, black, ruff, mypy)
   - [x] Set up basic CI/CD (GitHub Actions with tests, linting, formatting, type checking)
   - [x] Create `.gitignore` and development documentation

2. **Google Docs API Client** ✅
   - [x] Create `google_docs_markdown/api_client.py`
   - [x] Implement authentication using Application Default Credentials
   - [x] Create wrapper for Google Docs API (`documents().get()`)
   - [x] Handle authentication errors gracefully
   - [x] Include retry logic for transient failures
   - [x] Extract document ID from URLs
   - [x] Retrieve tab information (names, IDs) for multi-tab documents

3. **Basic Downloader (Docs → Markdown)**
   - [ ] Create `google_docs_markdown/downloader.py`
   - [ ] Treat every document as multi-tab (use `DocumentTab` as fundamental object)
   - [ ] Handle nested tab structures recursively (tabs can contain both content and child tabs)
   - [ ] Implement basic text extraction
   - [ ] Handle headings (up to arbitrary depth)
   - [ ] Handle paragraphs
   - [ ] Handle basic formatting (bold, italic)
   - [ ] Handle line breaks
   - [ ] Ensure deterministic output (normalize whitespace)
   - [ ] Create directory structure named after document title (or user-provided output directory)
   - [ ] Download each tab (including nested tabs) as a separate markdown file named after the tab (e.g., `My Doc/Tab 1.md`)
   - [ ] Name markdown files after tab names (sanitize filenames)
   - [ ] Handle nested tabs with appropriate naming convention (e.g., `Tab 1/Subtab A.md`)
   - [ ] Ensure Location/Range objects include `tabId` when working with multi-tab documents (API client ready; objects created in later tasks)
   - [ ] Handle `segmentId` in Location/Range objects for headers/footers/footnotes (API client ready; objects created in later tasks)

4. **CLI - Download Command**
   - [ ] Create `google_docs_markdown/cli.py` using `typer`
   - [ ] Implement `download` command
   - [ ] Support document URL/ID input
   - [ ] Support output directory path
   - [ ] Add `--tabs` flag for selective tab download (specify which tabs to download)
   - [ ] Add interactive prompts for missing arguments
   - [ ] Update `pyproject.toml` entry point

5. **Python API - Basic Interface**
   - [ ] Create `GoogleDocMarkdown` class in `downloader.py`
   - [ ] Implement `download(document_id)` → returns dict of tab_name → markdown (all docs treated as multi-tab)
   - [ ] Implement `download_to_file(document_id, output_path)` → saves to directory
   - [ ] Implement `get_document_title(document_id)` → returns title
   - [ ] Implement `get_tabs(document_id)` → returns list of tab names/IDs (always returns at least one tab)
   - [ ] Implement `get_nested_tabs(document_id, tab_id)` → returns nested tabs within a tab
   - [ ] Implement `extract_document_id(url)` → static method

6. **Testing**
   - [ ] Test with example Google Doc from `example_markdown/google_doc_urls.txt`
   - [ ] Test with multi-tab Google Doc (if available)
   - [x] Create unit tests for API client (including tab detection) ✅
   - [ ] Create unit tests for downloader (single-tab and multi-tab)
   - [ ] Create integration tests for end-to-end download (both scenarios)
   - [ ] Verify deterministic output (same doc → same markdown)
   - [ ] Test directory creation and file naming for multi-tab documents
   - [ ] Test selective tab download with `--tabs` flag

**Deliverable:** Can download Google Docs as Markdown (creates directory structure with markdown files inside, named after document title)

---

### Phase 2: Enhanced Markdown Features
**Goal:** Support more complex document structures (applies to all tabs in multi-tab documents)

**Tasks:**
1. **Advanced Text Formatting**
   - [ ] Handle strikethrough
   - [ ] Handle underline (convert to emphasis or preserve)
   - [ ] Handle code spans (inline code)
   - [ ] Handle links (TextRun with link property)
   - [ ] Handle rich links (RichLink element → `[title](uri)`)
   - [ ] Handle colored text (serialize as HTML comments per spec)
   - [ ] Handle column breaks (serialize as HTML comment)
   - [ ] Handle auto text (serialize as HTML comment with type info)
   - [ ] Ensure formatting works correctly across all tabs in multi-tab documents

2. **Structural Elements**
   - [ ] Handle lists (ordered and unordered)
   - [ ] Handle nested lists
   - [ ] Handle tables (convert to Markdown table format)
   - [ ] Handle horizontal rules
   - [ ] Handle block quotes
   - [ ] Handle section breaks (serialize as HTML comment with section style info)
   - [ ] Handle table of contents (mark as auto-generated, preserve or regenerate)
   - [ ] Handle equations (both block and inline versions)
   - [ ] Ensure structural elements work correctly in each tab independently

3. **Code Blocks**
   - [ ] Detect code blocks in Google Docs
   - [ ] Preserve language hints if available
   - [ ] Handle preformatted text
   - [ ] Support code blocks in any tab

4. **Images**
   - [ ] Create `google_docs_markdown/image_manager.py`
   - [ ] Extract images from Google Docs API
   - [ ] Download images to local `imgs/` directory within the document's output folder (e.g., `My Doc/imgs/`)
   - [ ] Generate Markdown image references
   - [ ] Handle image alt text and titles

5. **Headers, Footers, and Footnotes**
   - [ ] Extract headers from document (per-tab for multi-tab documents)
   - [ ] Extract footers from document (per-tab for multi-tab documents)
   - [ ] Extract footnotes from document (shared across tabs or per-tab)
   - [ ] Serialize headers/footers (as separate files or metadata)
   - [ ] Handle footnote references (`[^1]`) and footnote content
   - [ ] Ensure headers/footers/footnotes work correctly for all documents

6. **Multi-Tab Enhancements**
   - [ ] Ensure all enhanced features work correctly per-tab
   - [ ] Handle tab-specific formatting and structure
   - [ ] Maintain consistent image directory structure across tabs
   - [ ] Handle headers/footers per-tab in multi-tab documents

7. **Testing**
   - [ ] Test with example doc (has images, tables, code blocks)
   - [ ] Test with multi-tab doc containing complex features in multiple tabs
   - [ ] Verify all formatting is preserved across all tabs
   - [ ] Test edge cases (empty lists, nested structures) in multi-tab context
   - [ ] Verify image organization in multi-tab documents

**Deliverable:** Can download complex Google Docs with tables, images, lists, code blocks, headers/footers/footnotes, section breaks, TOC, and all paragraph elements, with full support for multi-tab documents

---

### Phase 3: Upload (Markdown → Docs)
**Goal:** Convert Markdown back to Google Docs, including multi-tab documents

**Tasks:**
1. **Markdown Parser**
   - [ ] Choose/implement Markdown parser (consider `markdown-it-py` or `mistune`)
   - [ ] Parse Markdown to intermediate representation
   - [ ] Handle all Markdown features from Phase 2
   - [ ] Detect directory structure indicating multi-tab document

2. **Uploader**
   - [ ] Create `google_docs_markdown/uploader.py`
   - [ ] Convert Markdown AST to Google Docs API `batchUpdate` requests
   - [ ] Handle document creation (`documents().create()`)
   - [ ] Handle document updates (`documents().batchUpdate()`)
   - [ ] Map Markdown elements to Google Docs elements:
     - Headings → paragraph with heading style
     - Lists → list elements
     - Tables → table elements
     - Images → inline images
     - Formatting → text runs with formatting
     - Rich links → RichLink elements
     - Section breaks → SectionBreak elements
     - Footnotes → FootnoteReference and footnote segments
   - [ ] Handle directory structure (all documents treated as multi-tab)
   - [ ] Handle uploading to specific tabs in multi-tab documents
   - [ ] Handle nested tab structures when uploading
   - [ ] Support creating documents from directory structure
   - [ ] Map directory structure to tab structure (directory name → document, files → tabs, subdirectories → nested tabs)
   - [ ] Handle `segmentId` in Location/Range objects for headers/footers/footnotes
   - [ ] Process batch updates in correct order:
     1. Deletions (from end to start to preserve indices)
     2. Insertions (from start to end)
     3. Updates (can be done in any order)
   - [ ] Upload headers/footers content to appropriate segments
   - [ ] Upload footnote content to footnote segments

3. **CLI - Upload Command**
   - [ ] Add `upload` command to CLI
   - [ ] Support `--create` flag for new documents
   - [ ] Support `--overwrite` flag
   - [ ] Handle directory path input
   - [ ] Auto-detect tab structure from directory contents (files → tabs, subdirectories → nested tabs)
   - [ ] Handle document URL/ID for updates
   - [ ] Add `--tab` flag to specify which tab to update (for multi-tab docs)
   - [ ] Support nested tab paths (e.g., `--tab "Tab 1/Subtab A"`)

4. **Python API - Upload Methods**
   - [ ] Add `upload(document_id, markdown_content, tab_name=None)` method
   - [ ] Add `upload_from_directory(document_id, directory_path)` method for multi-tab (handles nested tabs)
   - [ ] Add `create(markdown_content, title=None)` method (creates single-tab document)
   - [ ] Add `create_from_directory(directory_path, document_title=None)` method (handles multi-tab and nested tabs)
   - [ ] Return created/updated document ID

5. **Testing**
   - [ ] Test round-trip: download → upload → download (should match) for single-tab (treated as multi-tab with one tab)
   - [ ] Test round-trip: download → upload → download (should match) for multi-tab
   - [ ] Test round-trip with nested tabs
   - [ ] Test creating new single-tab documents
   - [ ] Test creating new multi-tab documents from directory
   - [ ] Test creating documents with nested tabs
   - [ ] Test updating existing single-tab documents
   - [ ] Test updating existing multi-tab documents (all tabs and specific tabs)
   - [ ] Test updating nested tabs
   - [ ] Verify deterministic upload (same markdown → same doc structure)
   - [ ] Test tab-specific updates
   - [ ] Test headers/footers/footnotes upload and round-trip
   - [ ] Test batch update ordering (verify indices are preserved)

**Deliverable:** Can upload Markdown to Google Docs (create and update), including full multi-tab support

---

### Phase 4: Change Detection & Diffing
**Goal:** Only upload changes, handle concurrent edits

**Tasks:**
1. **Diff Engine**
   - [ ] Create `google_docs_markdown/diff_engine.py`
   - [ ] Implement normalized representation for comparison
   - [ ] Use diff algorithm (Myers diff or similar) for text comparison
   - [ ] Detect changes at multiple granularities:
     - Character level
     - Word level
     - Paragraph level
     - Element level (formatting, structure)
   - [ ] Support per-tab diffing for multi-tab documents

2. **Change Detection**
   - [ ] Compare local Markdown with current online version
   - [ ] Generate minimal set of update operations
   - [ ] Handle insertions, deletions, modifications
   - [ ] Detect when no changes exist (skip API call)
   - [ ] For multi-tab documents: detect changes per-tab
   - [ ] Only update tabs that have changed

3. **Upload Integration**
   - [ ] Integrate diff engine into upload process
   - [ ] Always download current version before uploading
   - [ ] Generate only necessary `batchUpdate` requests
   - [ ] Handle conflicts gracefully (detect concurrent edits)
   - [ ] For multi-tab: only update changed tabs, preserve unchanged tabs

4. **CLI Enhancements**
   - [ ] Show diff preview before upload (optional flag)
   - [ ] Show per-tab diff summary for multi-tab documents
   - [ ] Prompt user after upload to pull latest version (default: yes)

5. **Testing**
   - [ ] Test no-change detection (download → upload without changes) for single-tab
   - [ ] Test no-change detection for multi-tab (all tabs unchanged)
   - [ ] Test partial updates (change one paragraph) for single-tab
   - [ ] Test partial updates (change one tab) for multi-tab
   - [ ] Test concurrent edit scenarios for both single and multi-tab
   - [ ] Test tab-specific change detection

**Deliverable:** Smart change detection, only uploads differences (works efficiently for multi-tab documents)

---

### Phase 5: Advanced Features
**Goal:** Handle Google Docs features not in Markdown

**Tasks:**
1. **Metadata Serialization**
   - [ ] Create `google_docs_markdown/metadata.py`
   - [ ] Implement HTML comment parsing for user-editable features
   - [ ] Implement JSON metadata parsing (from file or bottom of markdown)
   - [ ] Support both storage strategies (HTML comments + JSON)

2. **Feature Preservation**
   - [ ] Handle date pickers (serialize as HTML comments)
   - [ ] Handle person references (serialize as JSON)
   - [ ] Handle custom font colors (serialize as HTML comments)
   - [ ] Handle column breaks (serialize as HTML comments)
   - [ ] Handle auto text (serialize as HTML comments with type info)
   - [ ] Handle rich links (convert to Markdown links, preserve metadata)
   - [ ] Handle other advanced features as discovered

3. **Deserialization**
   - [ ] Parse HTML comments during upload
   - [ ] Parse JSON metadata during upload
   - [ ] Convert back to Google Docs API format
   - [ ] Preserve feature order

4. **Testing**
   - [ ] Test round-trip with advanced features
   - [ ] Verify features are preserved

**Deliverable:** Advanced Google Docs features preserved in Markdown

---

### Phase 6: Advanced Tab Features
**Goal:** Enhanced features for multi-tab document workflows

**Tasks:**
1. **Tab Management**
   - [ ] Add CLI command to list tabs in a document
   - [ ] Add CLI command to create new tabs
   - [ ] Add CLI command to rename tabs
   - [ ] Add CLI command to delete tabs (with confirmation)

2. **Bulk Operations**
   - [ ] Support bulk download of multiple multi-tab documents
   - [ ] Support bulk upload of multiple directories
   - [ ] Add progress indicators for multi-tab operations

3. **Tab Synchronization**
   - [ ] Detect when tabs are added/removed in Google Docs
   - [ ] Handle tab reordering
   - [ ] Sync tab names between local files and Google Docs

4. **Testing**
   - [ ] Test tab management operations
   - [ ] Test bulk operations
   - [ ] Test synchronization scenarios

**Deliverable:** Advanced tab management and bulk operations for multi-tab documents

**Note:** Basic multi-tab support (detection, download, upload) is implemented in Phases 1-3. This phase adds advanced management features.

---

### Phase 7: Image Storage Integration
**Goal:** Upload images to public storage (S3, GCS)

**Tasks:**
1. **Storage Backends**
   - [ ] Create `google_docs_markdown/storage/` module
   - [ ] Implement S3 backend
   - [ ] Implement GCS backend
   - [ ] Create abstract base class for storage backends

2. **Configuration**
   - [ ] Create `google_docs_markdown/config.py`
   - [ ] Support global config (`~/.config/google-docs-markdown/config.yaml`)
   - [ ] Support per-document config (`my_doc/config.yaml`)
   - [ ] Support CLI flag overrides

3. **Image Upload Workflow**
   - [ ] Scan Markdown for local image references
   - [ ] Upload local images to configured storage
   - [ ] Replace local references with public URLs
   - [ ] Update Markdown files with public URLs

4. **CLI Integration**
   - [ ] Add `--image-storage` flag
   - [ ] Add `--image-bucket` flag
   - [ ] Support configuration via config files

5. **Testing**
   - [ ] Test S3 upload
   - [ ] Test GCS upload
   - [ ] Test URL replacement
   - [ ] Test configuration precedence

**Deliverable:** Images can be uploaded to S3/GCS with URL replacement

---

### Phase 8: Polish & Documentation
**Goal:** Production-ready tool with comprehensive docs

**Tasks:**
1. **Error Handling**
   - [ ] Improve error messages
   - [ ] Add helpful troubleshooting hints
   - [ ] Handle edge cases gracefully

2. **CLI Polish**
   - [ ] Add progress indicators for long operations
   - [ ] Improve help text
   - [ ] Add verbose/debug flags
   - [ ] Add dry-run mode

3. **Documentation**
   - [ ] Update README with all features
   - [ ] Add API documentation
   - [ ] Add examples for common use cases
   - [ ] Document configuration options
   - [ ] Add troubleshooting guide

4. **Performance**
   - [ ] Profile and optimize slow operations
   - [ ] Add caching where appropriate
   - [ ] Optimize API call usage

5. **Testing**
   - [ ] Increase test coverage
   - [ ] Add performance tests
   - [ ] Add end-to-end tests

**Deliverable:** Production-ready tool

---

## Implementation Order Recommendation

**Start with Phase 1** - Get basic download working first, including multi-tab support from the start. This provides immediate value and validates the approach. Multi-tab handling is a core requirement, not an add-on.

**Then Phase 2** - Enhance download to handle complex documents.

**Then Phase 3** - Add upload capability, including multi-tab support. This completes the bidirectional conversion for both single and multi-tab documents.

**Then Phase 4** - Add change detection. This is critical for the tool's efficiency and conflict handling. Change detection should work per-tab for multi-tab documents.

**Phases 5-7** can be done in parallel or based on priority:
- **Phase 5** if advanced features are needed early
- **Phase 6** if advanced tab management features are needed (basic tab support is already in Phases 1-3)
- **Phase 7** if image storage is needed

**Phase 8** should be ongoing throughout development, but final polish happens at the end.

## Technical Decisions Needed

1. **Markdown Parser**: Choose library for parsing Markdown
   - Options: `markdown-it-py`, `mistune`, `markdown`
   - Recommendation: `markdown-it-py` (modern, extensible)

2. **CLI Framework**: Choose CLI framework
   - Options: `click`, `argparse`, `typer`
   - Decision: `typer` (modern, type-safe, leverages Python type hints)
     - We should use `Annotated` from `typing` to type the CLI arguments and options since it's the recommended way to do so by the library.

3. **Diff Algorithm**: Choose diffing library
   - Options: `difflib` (built-in), `diff-match-patch`, custom implementation
   - Recommendation: Start with `difflib`, upgrade if needed

4. **Storage Libraries**: Choose libraries for S3/GCS
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
- ✅ Phase 1, Task 1: Project Setup
- ✅ Phase 1, Task 2: Google Docs API Client (with comprehensive unit tests)

**In Progress:**
- Phase 1, Task 3: Basic Downloader (Docs → Markdown) (next up)

**Remaining Phase 1 Tasks:**
- Task 3: Basic Downloader (Docs → Markdown)
- Task 4: CLI - Download Command
- Task 5: Python API - Basic Interface
- Task 6: Testing (API client tests complete; remaining tests depend on downloader)

