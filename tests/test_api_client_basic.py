"""
Basic syntax and import tests for API client.

These tests verify the code structure without requiring API credentials.
"""


def test_import() -> None:
    """Test that the API client can be imported."""
    from google_docs_markdown.api_client import (
        MAX_RETRIES,
        SCOPES,
        GoogleDocsAPIClient,
        TabInfo,
    )

    assert GoogleDocsAPIClient is not None
    assert TabInfo is not None
    assert SCOPES == ["https://www.googleapis.com/auth/documents"]
    assert MAX_RETRIES == 3


def test_extract_document_id() -> None:
    """Test document ID extraction logic."""
    from google_docs_markdown.api_client import GoogleDocsAPIClient

    # Test various URL formats (using IDs that meet minimum length requirement)
    test_cases = [
        ("https://docs.google.com/document/d/abc123def456/edit", "abc123def456"),
        ("https://docs.google.com/document/d/abc123def456/view", "abc123def456"),
        ("https://docs.google.com/document/d/abc123def456", "abc123def456"),
        ("abc123def456", "abc123def456"),  # Already extracted
    ]

    for url, expected_id in test_cases:
        result = GoogleDocsAPIClient.extract_document_id(url)
        assert result == expected_id, f"Failed for {url}: got {result}, expected {expected_id}"

    # Test invalid URL (too short to be a valid document ID)
    try:
        GoogleDocsAPIClient.extract_document_id("invalid")
        raise AssertionError("Should have raised ValueError")
    except ValueError:
        pass  # Expected


if __name__ == "__main__":
    print("Running basic API client tests...")
    print()

    try:
        test_import()
        print("✓ Import test passed")
    except Exception as e:
        print(f"✗ Import test failed: {e}")

    try:
        test_extract_document_id()
        print("✓ Document ID extraction test passed")
    except Exception as e:
        print(f"✗ Document ID extraction test failed: {e}")

    print()
    print("Note: Run with pytest for full test output")
