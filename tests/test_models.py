"""Tests for Google Docs API Pydantic models.

Validates that generated models can parse real Google Docs API responses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from google_docs_markdown.models import Document


RESOURCES_DIR = Path(__file__).parent / "resources" / "document_jsons"


def load_document(name: str) -> dict[str, Any]:
    """Load a document JSON from test resources."""
    with (RESOURCES_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


def find_extra_fields(obj: BaseModel, path: str = "") -> list[str]:
    """Recursively find fields that landed in Pydantic's model_extra.

    These are fields present in the JSON but not defined in our models.
    """
    extras: list[str] = []
    if obj.model_extra:
        for key in obj.model_extra:
            extras.append(f"{path}.{key}" if path else key)

    for field_name in obj.model_fields_set | set(obj.__class__.model_fields):
        val = getattr(obj, field_name, None)
        child_path = f"{path}.{field_name}" if path else field_name
        if isinstance(val, BaseModel):
            extras.extend(find_extra_fields(val, child_path))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, BaseModel):
                    extras.extend(find_extra_fields(item, f"{child_path}[{i}]"))
        elif isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, BaseModel):
                    extras.extend(find_extra_fields(v, f"{child_path}[{k}]"))

    return extras


class TestDocumentParsing:
    """Test that models can parse real Google Docs API JSON responses."""

    def test_parse_markdown_conversion_example(self) -> None:
        data = load_document("Markdown_Conversion_Example.json")
        doc = Document.model_validate(data)

        assert doc.title == "Markdown Conversion Example"
        assert doc.documentId == "1JSbV5QEuG9kkG2YCBajqhWWgzBkXGJwu4moRSEUSg3M"
        assert doc.suggestionsViewMode == "SUGGESTIONS_INLINE"

    def test_tabs_parsed(self) -> None:
        data = load_document("Markdown_Conversion_Example.json")
        doc = Document.model_validate(data)

        assert doc.tabs is not None
        assert len(doc.tabs) == 2

        tab0 = doc.tabs[0]
        assert tab0.tabProperties is not None
        assert tab0.tabProperties.title == "First tab"
        assert tab0.tabProperties.tabId == "t.0"

        tab1 = doc.tabs[1]
        assert tab1.tabProperties is not None
        assert tab1.tabProperties.title == "Tab with child tab"

    def test_body_structural_elements(self) -> None:
        data = load_document("Markdown_Conversion_Example.json")
        doc = Document.model_validate(data)

        assert doc.tabs is not None
        body = doc.tabs[0].documentTab.body
        assert body is not None
        assert body.content is not None
        assert len(body.content) > 0

        first = body.content[0]
        assert first.sectionBreak is not None

        second = body.content[1]
        assert second.paragraph is not None
        assert second.paragraph.elements is not None
        assert len(second.paragraph.elements) > 0

    def test_text_run_content(self) -> None:
        data = load_document("Markdown_Conversion_Example.json")
        doc = Document.model_validate(data)

        assert doc.tabs is not None
        body = doc.tabs[0].documentTab.body
        assert body is not None

        para = body.content[1].paragraph
        assert para is not None
        text_run = para.elements[0].textRun
        assert text_run is not None
        assert text_run.content is not None
        assert len(text_run.content) > 0

    def test_date_elements_parsed(self) -> None:
        data = load_document("Markdown_Conversion_Example.json")
        doc = Document.model_validate(data)

        assert doc.tabs is not None
        body = doc.tabs[0].documentTab.body
        assert body is not None

        date_elements = []
        for elem in body.content:
            if elem.paragraph and elem.paragraph.elements:
                for pe in elem.paragraph.elements:
                    if pe.dateElement is not None:
                        date_elements.append(pe.dateElement)

        assert len(date_elements) == 2
        assert date_elements[0].dateId is not None
        assert date_elements[0].dateElementProperties is not None
        assert date_elements[0].dateElementProperties.timestamp == "2026-01-08T12:00:00Z"
        assert date_elements[0].dateElementProperties.dateFormat == "DATE_FORMAT_ISO8601"

    def test_no_extra_fields(self) -> None:
        """Verify all JSON fields are covered by our models (no data falls to extras)."""
        data = load_document("Markdown_Conversion_Example.json")
        doc = Document.model_validate(data)
        extras = find_extra_fields(doc)

        if extras:
            pytest.fail(
                f"Found {len(extras)} field(s) not defined in models:\n"
                + "\n".join(f"  - {e}" for e in sorted(set(extras)))
            )
