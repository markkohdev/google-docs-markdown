# Google Docs Markdown

A Python package and CLI tool for downloading and editing Google Docs as Markdown using the Google Docs API.

## Features

- **Download Google Docs as Markdown**: Convert Google Docs to Markdown format
- **Upload Markdown to Google Docs**: Update Google Docs with Markdown content
- **Image Management**: Extract and inline images in Markdown files
- **Simple CLI**: Easy-to-use command-line interface

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
   gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents
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

```bash
# Download as Markdown (default output filename)
google-docs-markdown download "https://docs.google.com/document/d/DOC_ID/edit"

# Specify output file
google-docs-markdown download "https://docs.google.com/document/d/DOC_ID/edit" --output my_doc.md

# Short form
google-docs-markdown download "URI" -o output.md
```

#### Upload Markdown to a Google Doc

```bash
# Upload markdown file to a Google Doc
google-docs-markdown upload "https://docs.google.com/document/d/DOC_ID/edit" document.md
```

#### Image Management

```bash
# Extract embedded images from markdown to ./imgs/
extract-images extract document.md

# Inline image files as data URIs in markdown
extract-images inline document.md
```

### Python API

```python
from google_docs_markdown import GoogleDocMarkdown

# Initialize client
client = GoogleDocMarkdown()

# Download a document as markdown
document_id = "DOC_ID"
markdown_content = client.download(document_id)

# Download and save to file
output_path = client.download_to_file(document_id, output_path="my_doc.md")

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

## Notes

- The package requires read and write access to Google Docs (uses `documents` scope)
- Documents must be accessible by the authenticated Google account
- Uses Application Default Credentials (ADC) via `gcloud auth application-default login`
- Credentials are cached locally and automatically refreshed when needed
- The upload functionality provides basic markdown support; complex features may require additional parsing

## License

See LICENSE file for details.
