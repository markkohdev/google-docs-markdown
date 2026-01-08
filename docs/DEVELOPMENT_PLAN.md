# Google Docs Markdown - Development Plan

**Created:** 2026-01-08  
**Status:** Planning Phase

## Overview

This document outlines the development plan for building the Google Docs Markdown tool. The plan is organized into phases, starting with a Minimum Viable Product (MVP) and progressively adding features.

Unit tests and documentation should be written for each component and function as they are implemented.

## Development Phases

### Phase 1: Foundation & MVP (Core Download)
**Goal:** Get basic Google Docs → Markdown conversion working

**Tasks:**
1. **Project Setup**
   - [ ] Set up proper project structure
   - [ ] Configure development dependencies (pytest, black, ruff, mypy)
   - [ ] Set up basic CI/CD (if applicable)
   - [ ] Create `.gitignore` and development documentation

2. **Google Docs API Client**
   - [ ] Create `google_docs_markdown/api_client.py`
   - [ ] Implement authentication using Application Default Credentials
   - [ ] Create wrapper for Google Docs API (`documents().get()`)
   - [ ] Handle authentication errors gracefully
   - [ ] Add retry logic for transient failures
   - [ ] Extract document ID from URLs

3. **Data Models**
   - [ ] Create `google_docs_markdown/models.py`
   - [ ] Define dataclasses for Google Docs API structures:
     - Document
     - Body
     - Paragraph
     - TextRun
     - Structural elements (headings, lists, etc.)
   - [ ] Implement conversion from API dict → dataclass
   - [ ] Add type hints throughout

4. **Basic Downloader (Docs → Markdown)**
   - [ ] Create `google_docs_markdown/downloader.py`
   - [ ] Implement basic text extraction
   - [ ] Handle headings (H1-H6)
   - [ ] Handle paragraphs
   - [ ] Handle basic formatting (bold, italic)
   - [ ] Handle line breaks
   - [ ] Ensure deterministic output (normalize whitespace)

5. **CLI - Download Command**
   - [ ] Create `google_docs_markdown/cli.py` using `click` or `argparse`
   - [ ] Implement `download` command
   - [ ] Support document URL/ID input
   - [ ] Support output file path
   - [ ] Add interactive prompts for missing arguments
   - [ ] Update `pyproject.toml` entry point

6. **Python API - Basic Interface**
   - [ ] Create `GoogleDocMarkdown` class in `downloader.py`
   - [ ] Implement `download(document_id)` → returns markdown string
   - [ ] Implement `download_to_file(document_id, output_path)` → saves to file
   - [ ] Implement `get_document_title(document_id)` → returns title
   - [ ] Implement `extract_document_id(url)` → static method

7. **Testing**
   - [ ] Test with example Google Doc from `example_markdown/google_doc_urls.txt`
   - [ ] Create unit tests for API client
   - [ ] Create unit tests for downloader
   - [ ] Create integration tests for end-to-end download
   - [ ] Verify deterministic output (same doc → same markdown)

**Deliverable:** Can download a simple Google Doc as Markdown

---

### Phase 2: Enhanced Markdown Features
**Goal:** Support more complex document structures

**Tasks:**
1. **Advanced Text Formatting**
   - [ ] Handle strikethrough
   - [ ] Handle underline (convert to emphasis or preserve)
   - [ ] Handle code spans (inline code)
   - [ ] Handle links
   - [ ] Handle colored text (serialize as HTML comments per spec)

2. **Structural Elements**
   - [ ] Handle lists (ordered and unordered)
   - [ ] Handle nested lists
   - [ ] Handle tables (convert to Markdown table format)
   - [ ] Handle horizontal rules
   - [ ] Handle block quotes

3. **Code Blocks**
   - [ ] Detect code blocks in Google Docs
   - [ ] Preserve language hints if available
   - [ ] Handle preformatted text

4. **Images**
   - [ ] Create `google_docs_markdown/image_manager.py`
   - [ ] Extract images from Google Docs API
   - [ ] Download images to local `imgs/` directory
   - [ ] Generate Markdown image references
   - [ ] Handle image alt text and titles

5. **Testing**
   - [ ] Test with example doc (has images, tables, code blocks)
   - [ ] Verify all formatting is preserved
   - [ ] Test edge cases (empty lists, nested structures)

**Deliverable:** Can download complex Google Docs with tables, images, lists, code blocks

---

### Phase 3: Upload (Markdown → Docs)
**Goal:** Convert Markdown back to Google Docs

**Tasks:**
1. **Markdown Parser**
   - [ ] Choose/implement Markdown parser (consider `markdown-it-py` or `mistune`)
   - [ ] Parse Markdown to intermediate representation
   - [ ] Handle all Markdown features from Phase 2

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

3. **CLI - Upload Command**
   - [ ] Add `upload` command to CLI
   - [ ] Support `--create` flag for new documents
   - [ ] Support `--overwrite` flag
   - [ ] Handle file path input
   - [ ] Handle document URL/ID for updates

4. **Python API - Upload Methods**
   - [ ] Add `upload(document_id, markdown_content)` method
   - [ ] Add `create(markdown_content, title=None)` method
   - [ ] Return created/updated document ID

5. **Testing**
   - [ ] Test round-trip: download → upload → download (should match)
   - [ ] Test creating new documents
   - [ ] Test updating existing documents
   - [ ] Verify deterministic upload (same markdown → same doc structure)

**Deliverable:** Can upload Markdown to Google Docs (create and update)

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

2. **Change Detection**
   - [ ] Compare local Markdown with current online version
   - [ ] Generate minimal set of update operations
   - [ ] Handle insertions, deletions, modifications
   - [ ] Detect when no changes exist (skip API call)

3. **Upload Integration**
   - [ ] Integrate diff engine into upload process
   - [ ] Always download current version before uploading
   - [ ] Generate only necessary `batchUpdate` requests
   - [ ] Handle conflicts gracefully (detect concurrent edits)

4. **CLI Enhancements**
   - [ ] Show diff preview before upload (optional flag)
   - [ ] Prompt user after upload to pull latest version (default: yes)

5. **Testing**
   - [ ] Test no-change detection (download → upload without changes)
   - [ ] Test partial updates (change one paragraph)
   - [ ] Test concurrent edit scenarios

**Deliverable:** Smart change detection, only uploads differences

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

### Phase 6: Tab/Sheet Support
**Goal:** Handle multi-tab documents (Google Sheets)

**Tasks:**
1. **Tab Detection**
   - [ ] Detect documents with multiple tabs
   - [ ] Identify tab names
   - [ ] Handle Google Sheets vs Google Docs

2. **Multi-Tab Download**
   - [ ] Create directory named after document
   - [ ] Download each tab as separate markdown file
   - [ ] Name files after tab names
   - [ ] Support `--tabs` flag for selective download

3. **Multi-Tab Upload**
   - [ ] Detect if target is multi-tab document
   - [ ] Handle uploading to specific tabs
   - [ ] Create directory structure if needed

4. **Testing**
   - [ ] Test with Google Sheets document
   - [ ] Test selective tab download
   - [ ] Test uploading to specific tabs

**Deliverable:** Full support for multi-tab documents

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

**Start with Phase 1** - Get basic download working first. This provides immediate value and validates the approach.

**Then Phase 2** - Enhance download to handle complex documents. This makes the tool more useful.

**Then Phase 3** - Add upload capability. This completes the bidirectional conversion.

**Then Phase 4** - Add change detection. This is critical for the tool's efficiency and conflict handling.

**Phases 5-7** can be done in parallel or based on priority:
- **Phase 5** if advanced features are needed early
- **Phase 6** if multi-tab support is important
- **Phase 7** if image storage is needed

**Phase 8** should be ongoing throughout development, but final polish happens at the end.

## Technical Decisions Needed

1. **Markdown Parser**: Choose library for parsing Markdown
   - Options: `markdown-it-py`, `mistune`, `markdown`
   - Recommendation: `markdown-it-py` (modern, extensible)

2. **CLI Framework**: Choose CLI framework
   - Options: `click`, `argparse`, `typer`
   - Recommendation: `click` (mature, well-documented)

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

## Next Steps

1. Review and refine this plan
2. Set up project structure (Phase 1, Task 1)
3. Begin implementation with Phase 1
4. Iterate based on testing and feedback

