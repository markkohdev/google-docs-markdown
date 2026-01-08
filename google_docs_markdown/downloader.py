"""
Download and edit Google Docs as Markdown using the Google Docs API.

Usage:
    from google_docs_markdown import GoogleDocMarkdown
    
    client = GoogleDocMarkdown()
    
    # Download a document as markdown
    markdown_content = client.download(document_id)
    
    # Upload markdown to a document
    client.upload(document_id, markdown_content)
"""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Any, Dict, List, Optional, Pattern

try:
    import google.auth
    from google.auth.credentials import Credentials
    from google.auth.exceptions import DefaultCredentialsError
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import Resource
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(
        "Error: Missing required dependencies. Install with:",
        "pip install google-api-python-client google-auth",
        file=sys.stderr,
    )
    raise SystemExit(1) from e


# Required scopes for Google Docs API (read and write)
SCOPES: List[str] = ["https://www.googleapis.com/auth/documents"]

# Document ID regex pattern
DOC_ID_PATTERN: Pattern[str] = re.compile(
    r"/document/d/([a-zA-Z0-9-_]+)"
)


class GoogleDocMarkdown:
    """
    A class-based tool for downloading and editing Google Docs as Markdown.
    
    This class encapsulates Google Docs API interactions and provides
    methods to download documents as markdown and upload markdown back to documents.
    """

    def __init__(self, credentials: Optional[Credentials] = None) -> None:
        """
        Initialize the GoogleDocMarkdown client.
        
        Args:
            credentials: Optional Google credentials. If None, will authenticate
                        using Application Default Credentials.
        """
        self._credentials: Optional[Credentials] = credentials
        self._service: Optional[Resource] = None

    @staticmethod
    def extract_document_id(uri: str) -> str:
        """
        Extract the document ID from a Google Docs URI.

        Args:
            uri: Google Docs URI

        Returns:
            The extracted document ID

        Examples:
            https://docs.google.com/document/d/DOC_ID/edit
            https://docs.google.com/document/d/DOC_ID/edit?usp=sharing
        """
        match = DOC_ID_PATTERN.search(uri)
        if not match:
            raise ValueError(
                f"Could not extract document ID from URI: {uri}\n"
                "Expected format: https://docs.google.com/document/d/DOC_ID/..."
            )
        return match.group(1)

    @staticmethod
    def _authenticate() -> Credentials:
        """
        Authenticate using Application Default Credentials (ADC).

        Uses credentials from `gcloud auth application-default login`.
        Falls back to service account credentials if available.
        Ensures credentials have the required scopes by refreshing if needed.

        Returns:
            Authenticated credentials

        Raises:
            RuntimeError: If no credentials are found
        """
        try:
            credentials, _project = google.auth.default(scopes=SCOPES)
            
            # Refresh credentials if they're expired or don't have the right scopes
            if credentials.expired or not credentials.valid:
                request = Request()
                credentials.refresh(request)
            
            return credentials
        except DefaultCredentialsError as e:
            raise RuntimeError(
                "No credentials found. Please authenticate using:\n"
                "  gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents\n\n"
                "This will use your Google Cloud credentials to access Google Docs."
            ) from e

    def _get_service(self) -> Resource:
        """
        Get or create the Google Docs API service instance.

        Returns:
            Google Docs API service resource
        """
        if self._service is None:
            if self._credentials is None:
                self._credentials = self._authenticate()
            self._service = build("docs", "v1", credentials=self._credentials)
        return self._service

    @staticmethod
    def _handle_http_error(e: HttpError, document_id: str) -> None:
        """
        Handle HTTP errors with helpful error messages and troubleshooting steps.

        Args:
            e: The HTTP error that occurred
            document_id: The document ID that caused the error

        Raises:
            RuntimeError: With a helpful error message based on the HTTP status code
        """
        status: Optional[int] = e.resp.status if hasattr(e, 'resp') else None
        error_details: List[Any] = getattr(e, 'error_details', [])
        
        # Check for scope-related errors
        scope_error: bool = False
        for detail in error_details:
            if isinstance(detail, dict):
                reason: str = detail.get('reason', '')
                if reason == 'ACCESS_TOKEN_SCOPE_INSUFFICIENT':
                    scope_error = True
                    break
        
        if scope_error or (status == 403 and 'insufficient authentication scopes' in str(e).lower()):
            raise RuntimeError(
                "Authentication scopes are insufficient. Your credentials don't have "
                "permission to access the Google Docs API.\n\n"
                "To fix this:\n"
                "  1. Revoke existing application-default credentials:\n"
                "     gcloud auth application-default revoke\n\n"
                "  2. Re-authenticate with the Google Docs API scope:\n"
                "     gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents\n\n"
                "  3. Ensure Google Docs API is enabled in your project:\n"
                "     gcloud services enable docs.googleapis.com\n\n"
                "Alternatively, you can authenticate without specifying scopes:\n"
                "  gcloud auth application-default login\n"
                "(The script will request the necessary scopes automatically)"
            ) from e
        
        if status == 403:
            raise RuntimeError(
                f"Access denied to document {document_id}.\n\n"
                "Possible causes:\n"
                "  - The document is not shared with your Google account\n"
                "  - Insufficient authentication scopes (see above)\n"
                "  - Google Docs API not enabled in your project\n\n"
                "To fix:\n"
                "  1. Ensure the document is shared with your Google account\n"
                "  2. Re-authenticate: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents\n"
                "  3. Enable the API: gcloud services enable docs.googleapis.com\n"
                f"  4. Verify your project: gcloud config get-value project"
            ) from e
        elif status == 404:
            raise RuntimeError(
                f"Document {document_id} not found.\n\n"
                "Please verify:\n"
                "  - The document ID is correct\n"
                "  - The document exists and is accessible\n"
                "  - You have permission to view/edit the document"
            ) from e
        elif status == 401:
            raise RuntimeError(
                "Authentication failed. Your credentials may have expired.\n\n"
                "To fix:\n"
                "  gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents"
            ) from e
        else:
            raise RuntimeError(
                f"Failed to access document {document_id}.\n"
                f"HTTP {status}: {e}\n\n"
                "If this persists, try:\n"
                "  1. Re-authenticating: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/documents\n"
                "  2. Verifying the document is accessible\n"
                "  3. Checking that Google Docs API is enabled in your project"
            ) from e

    def get_document_title(self, document_id: str) -> str:
        """
        Get the title of a Google Doc.

        Args:
            document_id: The Google Docs document ID

        Returns:
            The document title, or "document" if unavailable
        """
        service = self._get_service()
        try:
            doc_metadata: Dict[str, Any] = service.documents().get(documentId=document_id).execute()
            return doc_metadata.get("title", "document")
        except HttpError as e:
            self._handle_http_error(e, document_id)
            return "document"  # Never reached, but satisfies type checker

    def download(self, document_id: str) -> str:
        """
        Download a Google Doc and convert it to Markdown format.

        Args:
            document_id: The Google Docs document ID

        Returns:
            The document content as Markdown
        """
        service = self._get_service()
        try:
            doc: Dict[str, Any] = service.documents().get(documentId=document_id).execute()
        except HttpError as e:
            self._handle_http_error(e, document_id)
            return ""  # Never reached, but satisfies type checker

        content: List[Dict[str, Any]] = doc.get("body", {}).get("content", [])
        markdown_parts: List[str] = []

        def process_element(element: Dict[str, Any], level: int = 0) -> None:
            """Process document elements and convert to Markdown."""
            if "paragraph" in element:
                para: Dict[str, Any] = element["paragraph"]
                para_elem: Dict[str, Any] = para.get("paragraphStyle", {})
                style: str = para_elem.get("namedStyleType", "NORMAL_TEXT")

                # Extract text from paragraph elements
                para_text: List[str] = []
                for elem in para.get("elements", []):
                    if "textRun" in elem:
                        text_run: Dict[str, Any] = elem["textRun"]
                        text: str = text_run.get("content", "")
                        text_style: Dict[str, Any] = text_run.get("textStyle", {})

                        # Apply formatting
                        if text_style.get("bold"):
                            text = f"**{text}**"
                        if text_style.get("italic"):
                            text = f"*{text}*"
                        if text_style.get("underline"):
                            text = f"<u>{text}</u>"

                        para_text.append(text)

                text_content: str = "".join(para_text).strip()

                if not text_content:
                    return

                # Apply paragraph-level formatting
                if style == "HEADING_1":
                    markdown_parts.append(f"# {text_content}\n")
                elif style == "HEADING_2":
                    markdown_parts.append(f"## {text_content}\n")
                elif style == "HEADING_3":
                    markdown_parts.append(f"### {text_content}\n")
                elif style == "HEADING_4":
                    markdown_parts.append(f"#### {text_content}\n")
                elif style == "HEADING_5":
                    markdown_parts.append(f"##### {text_content}\n")
                elif style == "HEADING_6":
                    markdown_parts.append(f"###### {text_content}\n")
                else:
                    markdown_parts.append(f"{text_content}\n")

            elif "table" in element:
                # Convert table to Markdown table format
                table: Dict[str, Any] = element["table"]
                rows: List[Dict[str, Any]] = table.get("tableRows", [])
                if not rows:
                    return

                # Process header row
                header_row: Dict[str, Any] = rows[0]
                header_cells: List[str] = []
                for cell in header_row.get("tableCells", []):
                    cell_text: List[str] = []
                    for content_elem in cell.get("content", []):
                        cell_text.extend(_extract_text_from_element(content_elem))
                    header_cells.append(" ".join(cell_text).strip())

                if header_cells:
                    markdown_parts.append("| " + " | ".join(header_cells) + " |\n")
                    markdown_parts.append("| " + " | ".join(["---"] * len(header_cells)) + " |\n")

                    # Process data rows
                    for row in rows[1:]:
                        row_cells: List[str] = []
                        for cell in row.get("tableCells", []):
                            cell_text = []
                            for content_elem in cell.get("content", []):
                                cell_text.extend(_extract_text_from_element(content_elem))
                            row_cells.append(" ".join(cell_text).strip())
                        if row_cells:
                            markdown_parts.append("| " + " | ".join(row_cells) + " |\n")
                    markdown_parts.append("\n")

        def _extract_text_from_element(elem: Dict[str, Any]) -> List[str]:
            """Helper to extract text from an element."""
            texts: List[str] = []
            if "paragraph" in elem:
                for para_elem in elem["paragraph"].get("elements", []):
                    if "textRun" in para_elem:
                        texts.append(para_elem["textRun"].get("content", ""))
            return texts

        for element in content:
            process_element(element)

        return "".join(markdown_parts)

    def download_to_file(
        self,
        document_id: str,
        output_path: Optional[pathlib.Path] = None,
    ) -> pathlib.Path:
        """
        Download a Google Doc as Markdown and save it to a file.

        Args:
            document_id: The Google Docs document ID
            output_path: Optional output file path. If not provided, will use
                        the document title with .md extension.

        Returns:
            The path to the saved file
        """
        # Get document title for default output filename
        doc_title: str = self.get_document_title(document_id)

        # Determine output file
        if output_path is None:
            # Sanitize filename
            safe_title: str = "".join(
                c for c in doc_title if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            safe_title = safe_title.replace(" ", "_")
            output_path = pathlib.Path(f"{safe_title}.md")

        # Download document
        content: str = self.download(document_id)

        # Write to file
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def upload(self, document_id: str, markdown_content: str) -> None:
        """
        Upload markdown content to a Google Doc, replacing its content.

        Args:
            document_id: The Google Docs document ID
            markdown_content: The markdown content to upload

        Note:
            This is a basic implementation that replaces the entire document content.
            For more complex markdown features (tables, images, etc.), you may need
            to use more advanced parsing and conversion.
        """
        service = self._get_service()
        
        # First, get the document to find the end index
        try:
            doc: Dict[str, Any] = service.documents().get(documentId=document_id).execute()
        except HttpError as e:
            self._handle_http_error(e, document_id)
            return

        # Get the end index of the document body
        body: Dict[str, Any] = doc.get("body", {})
        end_index: int = body.get("content", [{}])[-1].get("endIndex", 1) if body.get("content") else 1
        
        # If document has content, delete it first (except the last newline)
        requests: List[Dict[str, Any]] = []
        if end_index > 1:
            # Delete everything except the last newline character
            requests.append({
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": end_index - 1,
                    }
                }
            })

        # Parse markdown and convert to Google Docs format
        # This is a simplified parser - you may want to enhance this
        lines = markdown_content.split("\n")
        current_index = 1
        
        for line in lines:
            line = line.rstrip()
            if not line:
                # Empty line - insert a newline
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": "\n",
                    }
                })
                current_index += 1
            elif line.startswith("#"):
                # Heading
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("# ").strip()
                style = f"HEADING_{min(level, 6)}"
                
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": text + "\n",
                    }
                })
                requests.append({
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": current_index,
                            "endIndex": current_index + len(text),
                        },
                        "paragraphStyle": {
                            "namedStyleType": style,
                        },
                        "fields": "namedStyleType",
                    }
                })
                current_index += len(text) + 1
            elif line.startswith("|") and "|" in line[1:]:
                # Table row (simplified - doesn't handle full table structure)
                # For now, just insert as text
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": line + "\n",
                    }
                })
                current_index += len(line) + 1
            else:
                # Regular paragraph
                # Parse inline formatting (bold, italic)
                text = line
                # Simple markdown parsing for bold and italic
                # Note: This is basic - full markdown parsing would require a library
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": text + "\n",
                    }
                })
                current_index += len(text) + 1

        # Execute batch update
        if requests:
            try:
                service.documents().batchUpdate(
                    documentId=document_id,
                    body={"requests": requests}
                ).execute()
            except HttpError as e:
                self._handle_http_error(e, document_id)


def main() -> int:
    """CLI entry point for downloading and uploading Google Docs as Markdown."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download and edit Google Docs as Markdown using the Google Docs API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")
    
    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download a Google Doc as Markdown",
    )
    download_parser.add_argument(
        "uri",
        help="Google Docs URI (e.g., https://docs.google.com/document/d/DOC_ID/edit)",
    )
    download_parser.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        help="Output file path (default: document title with .md extension)",
    )
    
    # Upload command
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload markdown content to a Google Doc",
    )
    upload_parser.add_argument(
        "uri",
        help="Google Docs URI (e.g., https://docs.google.com/document/d/DOC_ID/edit)",
    )
    upload_parser.add_argument(
        "markdown_file",
        type=pathlib.Path,
        help="Path to the markdown file to upload",
    )

    args = parser.parse_args()

    try:
        # Extract document ID
        document_id: str = GoogleDocMarkdown.extract_document_id(args.uri)
        print(f"Document ID: {document_id}")

        # Create client instance
        print("Authenticating...")
        client = GoogleDocMarkdown()

        if args.command == "download":
            # Get document title for display
            doc_title: str = client.get_document_title(document_id)

            # Download document
            print(f"Downloading document '{doc_title}' as Markdown...")
            output_path: pathlib.Path = client.download_to_file(
                document_id=document_id,
                output_path=args.output,
            )
            print(f"✓ Document saved to: {output_path}")
            
        elif args.command == "upload":
            if not args.markdown_file.exists():
                print(f"Error: Markdown file not found: {args.markdown_file}", file=sys.stderr)
                return 1
            
            markdown_content = args.markdown_file.read_text(encoding="utf-8")
            print("Uploading markdown content to document...")
            client.upload(document_id, markdown_content)
            print("✓ Document updated successfully")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
