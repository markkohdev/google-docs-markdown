# Google Docs Markdown

A Python package and CLI tool for downloading and editing Google Docs as Markdown using the Google Docs API. The tool enables bidirectional conversion between Google Docs and Markdown format, allowing you to edit documents locally in Markdown while maintaining synchronization with Google Docs.

## Features

- **Bidirectional Conversion**: Seamlessly convert between Google Docs and Markdown formats
- **Download Google Docs as Markdown**: Convert Google Docs to Markdown format with preserved structure and formatting
- **Upload Markdown to Google Docs**: Update Google Docs with Markdown content, with intelligent change detection
- **Deterministic Behavior**: Consistent, reproducible conversions (same input always produces same output)
- **Change Detection**: Automatically detects differences and only submits changes that differ from the online version
- **Tab/Sheet Support**: Handles documents with multiple tabs by downloading each tab into a separate markdown file organized in a directory structure
- **Image Management**: Extracts images from Google Docs, stores them locally, and can upload to public storage (S3, GCS) with URL replacement
- **Advanced Feature Preservation**: Handles Google Docs features not natively supported in Markdown (date pickers, person references, custom formatting) via HTML comments and companion JSON files
- **Simple CLI**: Easy-to-use command-line interface with interactive prompts

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

### Google API Authentication

1. **Authenticate using `gcloud`:**
   ```bash
   gcloud auth application-default login 
   ```
   
   This will:
   - Open a browser for authentication
   - Grant permissions to access and edit your Google Docs
   - Store credentials locally for future use
   
   **Important:** Include the `--scopes` flag to ensure your credentials have permission to access the Google Docs API. If you've already authenticated without scopes, revoke and re-authenticate:
   ```bash
   gcloud auth application-default revoke
   gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents
   ```
   
   **Note:** You need the Google Cloud SDK installed. If you don't have it:
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

   **For Spotify engineers:** If you're using Spotify's internal Google Cloud setup, you may need to configure your project:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   gcloud services enable docs.googleapis.com
   ```

## Usage

### Command Line Interface

#### Download a Google Doc as Markdown

For documents with multiple tabs (e.g., Google Sheets), the tool creates a directory named after the document and downloads each tab as a separate markdown file named after the tab. For example, a document "My Spreadsheet" with tabs "Sheet1" and "Sheet2" will create:
- `My Spreadsheet/Sheet1.md`
- `My Spreadsheet/Sheet2.md`

```bash
# Download a Google Doc as Markdown (will prompt for document URL or ID)
google-docs-markdown download

# Download as Markdown (default output file path)
google-docs-markdown download "https://docs.google.com/document/d/DOC_ID/edit"

# Specify output directory
google-docs-markdown download "https://docs.google.com/document/d/DOC_ID/edit" --output my_doc

# Download specific tabs as single files
google-docs-markdown download "URI" --tabs Sheet1 Sheet2

# Short form
google-docs-markdown download "URI" -o output.md
```

#### Upload Markdown to a Google Doc

The upload process automatically detects changes by comparing your local Markdown with the online version. Only differences are submitted, minimizing API calls and reducing conflicts with concurrent edits.

```bash
# Upload markdown file to an existing Google Doc (update mode)
google-docs-markdown upload document.md "https://docs.google.com/document/d/DOC_ID/edit"

# Create a new Google Doc from Markdown (create mode)
google-docs-markdown upload document.md --create

# Force upload even when no changes detected (overwrite mode)
google-docs-markdown upload document.md "URI" --overwrite
```

**Note**: After uploading, the tool will prompt you to pull the latest version (default: yes) to sync any concurrent online edits.

### Python API

```python
from google_docs_markdown import GoogleDocMarkdown

# Initialize client
client = GoogleDocMarkdown()

# Download a document as markdown
document_id = "DOC_ID"
markdown_content = client.download(document_id)

# Download and save to file
output_path = client.download_to_file(document_id, output_path="my_doc")

# Upload markdown to a document
client.upload(document_id, markdown_content)

# Get document title
title = client.get_document_title(document_id)

# Extract document ID from URI
doc_id = GoogleDocMarkdown.extract_document_id(
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

## Configuration

### Image Storage

The tool can upload images to public storage services (S3, GCS, etc.) and replace local image references with public URLs. Configuration can be set at multiple levels:

1. **Global config**: `~/.config/google-docs-markdown/config.yaml`
2. **Per-document config**: `my_doc/config.yaml` (alongside markdown files)
3. **CLI flags**: Override config per command execution

Example config file:
```yaml
image_storage:
  backend: s3  # or gcs
  bucket: my-bucket
  region: us-east-1
  # ... other backend-specific settings
```

### Advanced Features

Google Docs features not natively supported in Markdown are preserved using two strategies:

**1. HTML Comments (User-Editable Features)**
- Date pickers: `<!-- date-picker: {"type": "date", "value": "2026-01-15", "format": "YYYY-MM-DD"} -->`
- Custom font colors: `<!-- font-color: {"hex": "#FF5733", "name": "custom-orange"} -->`
- Other editable metadata that users might want to modify directly in Markdown

**2. Companion JSON Files (Complex Features)**
- Person references, complex formatting, document-level metadata
- Stored in `document.metadata.json` alongside the markdown file
- Can also be embedded at the bottom of the markdown file as a JSON code block

These features are automatically serialized when downloading and deserialized when uploading.

## Notes

- The package requires read and write access to Google Docs (uses `documents` scope)
- Documents must be accessible by the authenticated Google account
- Uses Application Default Credentials (ADC) via `gcloud auth application-default login`
- Credentials are cached locally and automatically refreshed when needed
- **Deterministic conversions**: Same document input always produces identical Markdown output
- **No-change detection**: If a document is downloaded and immediately uploaded without modification, no API calls are made (unless `--overwrite` flag is used)
- The tool handles concurrent edits gracefully by detecting changes and only submitting differences

## License

See LICENSE file for details.
