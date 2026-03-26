# Google Docs Markdown

A Python package and CLI tool for downloading and editing Google Docs as Markdown using the Google Docs API. The tool enables bidirectional conversion between Google Docs and Markdown format, allowing you to edit documents locally in Markdown while maintaining synchronization with Google Docs.

## Features

**Implemented:**
- **Download Google Docs as Markdown**: Convert Google Docs to Markdown format with comprehensive element support:
  - Headings (H1–H6, Title, Subtitle)
  - Inline formatting (bold, italic, strikethrough, underline)
  - Links and rich links (Google Drive files, etc.)
  - Ordered, unordered, and nested lists
  - Tables (Markdown pipe format with header detection)
  - Code blocks (detected via Google Docs' internal U+E907 markers)
  - Images (referenced via Google-hosted URLs with alt text)
  - Horizontal rules
  - Footnotes (references and definitions)
- **Multi-Tab Support**: Handles documents with multiple tabs (including nested tabs) by downloading each tab into a separate markdown file organized in a directory structure
- **Deterministic Behavior**: Consistent, reproducible conversions (same input always produces same output)
- **Smart CLI**: Command-line interface with interactive prompts, selective tab download, file conflict handling, and stale file cleanup
- **Python API**: Programmatic access via `Downloader` and `MarkdownSerializer` classes

**Planned (not yet implemented):**
- Non-Markdown element handling: Person mentions, date chips, equations, etc. (Phase 2.6)
- Upload Markdown to Google Docs (Phase 3)
- Change detection and smart diffing (Phase 4)
- Local image download and storage integration with S3/GCS (Phase 7)
- Advanced feature preservation via HTML comments and JSON metadata (Phase 2.6 / Phase 5)

## Installation

### Using `uv` (Recommended)

```bash
# Create venv and install dependencies
uv venv
source .venv/bin/activate
uv sync
```

### Using `pip`

```bash
pip install -e .
```

## Setup

### Quick Setup (Recommended)

Run the interactive setup command to configure authentication and enable required APIs:

```bash
google-docs-markdown setup
```

This command will:
- ✅ Check if `gcloud` CLI is installed
- ✅ Set up Application Default Credentials with required scopes
- ✅ Configure your default GCP project
- ✅ Enable the Google Docs API

The setup command is interactive and will guide you through each step, skipping any that are already configured.

### Manual Setup (Appendix)

If you prefer to set up manually or need to troubleshoot, see [Manual Setup Steps](#manual-setup-steps) in the appendix below.

## Usage

### Command Line Interface

#### Download a Google Doc as Markdown

The tool creates a directory named after the document and downloads each tab as a separate markdown file named after the tab. For example, a document "My Project" with tabs "Overview" and "Notes" will create:
- `My Project/Overview.md`
- `My Project/Notes.md`

Nested tabs produce nested directories (e.g., `My Project/Parent Tab/Child Tab.md`).

```bash
# Download a Google Doc as Markdown (will prompt for document URL or ID)
google-docs-markdown download

# Download with document URL
google-docs-markdown download "https://docs.google.com/document/d/DOC_ID/edit"

# Specify output directory
google-docs-markdown download "DOC_ID" --output my_doc

# Download specific tabs only
google-docs-markdown download "DOC_ID" --tabs "Tab 1" --tabs "Tab 2"

# Force overwrite existing files and auto-delete stale files
google-docs-markdown download "DOC_ID" --force

# Short forms
google-docs-markdown download "DOC_ID" -o my_doc -t "Tab 1" -f
```

#### Upload Markdown to a Google Doc (Not Yet Implemented)

Upload support is planned for Phase 3. The CLI command exists but is currently a stub.

```bash
# These commands exist but raise NotImplementedError:
google-docs-markdown upload --document-url "DOC_ID"
google-docs-markdown diff --document-url "DOC_ID"
```

### Python API

```python
from google_docs_markdown import Downloader, MarkdownSerializer, GoogleDocsClient

# --- Downloading ---

dl = Downloader()

# Download all tabs as a dict of tab_path -> markdown string
tabs = dl.download("DOC_ID")
for tab_path, markdown in tabs.items():
    print(f"{tab_path}: {len(markdown)} chars")

# Download and write to disk (creates directory structure)
written = dl.download_to_files("DOC_ID", output_dir="my_doc")
for tab_path, file_path in written.items():
    print(f"  {tab_path} -> {file_path}")

# Download only specific tabs
tabs = dl.download("DOC_ID", tab_names=["Overview", "Notes"])

# --- Low-level serialization ---

serializer = MarkdownSerializer()
client = GoogleDocsClient()
doc = client.get_document("DOC_ID")

# Serialize a single tab to markdown
for tab in doc.tabs or []:
    markdown = serializer.serialize(tab.documentTab)

# --- Utilities ---

# Extract document ID from a URL
doc_id = GoogleDocsClient.extract_document_id(
    "https://docs.google.com/document/d/DOC_ID/edit"
)
```

## Troubleshooting

### "Insufficient authentication scopes" error

If you see an error about insufficient authentication scopes, your credentials don't have permission to access the Google Docs API. Fix it by:

1. Revoking existing credentials:
   ```bash
   gcloud auth application-default revoke
   ```

2. Re-authenticating with the correct scope:
   ```bash
   gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents
   ```

3. Ensuring the Google Docs API is enabled:
   ```bash
   gcloud services enable docs.googleapis.com
   ```

### "Access denied" or "Document not found" errors

- Verify the document is shared with your Google account
- Check that you have view/edit permissions on the document
- Ensure your Google Cloud project has the Google Docs API enabled

## Current Limitations

The downloader handles most common document elements (see Features above). The following are **not yet supported** and are silently skipped:

**Planned for Phase 2.6:**
- Person mentions (smart chips)
- Date elements (smart chips)
- AutoText (page numbers, page counts)
- Equations
- Section breaks, column breaks
- Table of contents
- Suggestions (tracked changes)
- Headers and footers
- Colored text (foreground/background)
- Title/Subtitle round-trip metadata (currently serialized as `#` / `*text*`)

**Planned for Phase 3:**
- Upload Markdown back to Google Docs

**Other limitations:**
- Images reference Google-hosted `contentUri` URLs directly (local download planned for Phase 7)
- Code blocks have no language identifier (Google Docs API does not expose it)
- Rich links are serialized as plain links (no visual distinction from regular hyperlinks)

## Notes

- The package requires read access to Google Docs (uses `documents` scope)
- Documents must be accessible by the authenticated Google account
- Uses Application Default Credentials (ADC) via `gcloud auth application-default login`
- Credentials are cached locally and automatically refreshed when needed
- **Deterministic conversions**: Same document input always produces identical Markdown output

## Appendix

### Manual Setup Steps

If you prefer to set up manually or need to troubleshoot, follow these steps:

#### 1. Install Google Cloud SDK

If you don't have `gcloud` CLI installed:

```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

#### 2. Authenticate with Application Default Credentials

Set up authentication with the required scopes:

```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/sqlservice.login,openid
```

This will:
- Open a browser for authentication
- Grant permissions to access and edit your Google Docs
- Store credentials locally for future use

**Note:** If you've already authenticated without the required scopes, revoke and re-authenticate:

```bash
gcloud auth application-default revoke
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/sqlservice.login,openid
```

#### 3. Set Default GCP Project

Set your default Google Cloud project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

**For Spotify engineers:** Use your Spotify GCP project ID.

#### 4. Enable Google Docs API

Enable the Google Docs API for your project:

```bash
gcloud services enable docs.googleapis.com --project=YOUR_PROJECT_ID
```

Or if you've already set a default project:

```bash
gcloud services enable docs.googleapis.com
```

#### Verification

To verify your setup is correct:

```bash
# Check credentials
gcloud auth application-default print-access-token

# Check project
gcloud config get-value project

# Check if API is enabled
gcloud services list --enabled --filter="name:docs.googleapis.com"
```

## License

See LICENSE file for details.
