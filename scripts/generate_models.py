#!/usr/bin/env python3
"""
Generate Pydantic models from google-api-python-client-stubs TypedDict definitions.

This script parses the schemas.pyi file and generates Pydantic models organized
into logical files.
"""

import re
from pathlib import Path
from typing import Any

# Model organization mapping
MODEL_ORGANIZATION = {
    "document.py": [
        "Document",
        "DocumentTab",
        "Body",
        "Tab",
        "TabProperties",
        "DocumentStyle",
        "DocumentFormat",
        "DocumentStyleSuggestionState",
        "NamedStyles",
        "NamedStyle",
        "NamedStyleSuggestionState",
        "NamedStylesSuggestionState",
    ],
    "elements.py": [
        "StructuralElement",
        "Paragraph",
        "Table",
        "TableOfContents",
        "SectionBreak",
        "TableRow",
        "TableCell",
        "ParagraphElement",
        "TextRun",
        "AutoText",
        "ColumnBreak",
        "PageBreak",
        "HorizontalRule",
        "Equation",
        "FootnoteReference",
        "Person",
        "RichLink",
        "InlineObjectElement",
    ],
    "styles.py": [
        "ParagraphStyle",
        "TextStyle",
        "TableCellStyle",
        "TableRowStyle",
        "TableStyle",
        "SectionStyle",
        "SectionColumnProperties",
        "ParagraphBorder",
        "TableCellBorder",
        "Bullet",
        "NestingLevel",
        "TabStop",
        "ParagraphStyleSuggestionState",
        "TextStyleSuggestionState",
        "TableCellStyleSuggestionState",
        "TableRowStyleSuggestionState",
        "BulletSuggestionState",
        "NestingLevelSuggestionState",
    ],
    "requests.py": [
        "Request",
        "BatchUpdateDocumentRequest",
        "CreateFooterRequest",
        "CreateHeaderRequest",
        "CreateFootnoteRequest",
        "CreateNamedRangeRequest",
        "CreateParagraphBulletsRequest",
        "DeleteContentRangeRequest",
        "DeleteFooterRequest",
        "DeleteHeaderRequest",
        "DeleteNamedRangeRequest",
        "DeleteParagraphBulletsRequest",
        "DeletePositionedObjectRequest",
        "DeleteTableColumnRequest",
        "DeleteTableRowRequest",
        "InsertInlineImageRequest",
        "InsertPageBreakRequest",
        "InsertPersonRequest",
        "InsertSectionBreakRequest",
        "InsertTableRequest",
        "InsertTableColumnRequest",
        "InsertTableRowRequest",
        "InsertTextRequest",
        "MergeTableCellsRequest",
        "PinTableHeaderRowsRequest",
        "ReplaceAllTextRequest",
        "ReplaceImageRequest",
        "ReplaceNamedRangeContentRequest",
        "UnmergeTableCellsRequest",
        "UpdateDocumentStyleRequest",
        "UpdateParagraphStyleRequest",
        "UpdateSectionStyleRequest",
        "UpdateTableCellStyleRequest",
        "UpdateTableColumnPropertiesRequest",
        "UpdateTableRowStyleRequest",
        "UpdateTextStyleRequest",
    ],
    "responses.py": [
        "Response",
        "BatchUpdateDocumentResponse",
        "CreateFooterResponse",
        "CreateHeaderResponse",
        "CreateFootnoteResponse",
        "CreateNamedRangeResponse",
        "InsertInlineImageResponse",
        "InsertInlineSheetsChartResponse",
        "ReplaceAllTextResponse",
    ],
    "common.py": [
        # Colors and formatting
        "Color",
        "OptionalColor",
        "RgbColor",
        "Background",
        "Shading",
        "Dimension",
        "Size",
        "Link",
        "WeightedFontFamily",
        # Location and ranges
        "Location",
        "Range",
        "EndOfSegmentLocation",
        "TableCellLocation",
        "TableRange",
        # Objects and references
        "InlineObject",
        "InlineObjectProperties",
        "PositionedObject",
        "PositionedObjectPositioning",
        "PositionedObjectProperties",
        "EmbeddedObject",
        "EmbeddedObjectBorder",
        "EmbeddedDrawingProperties",
        "ImageProperties",
        "SheetsChartReference",
        "LinkedContentReference",
        "ObjectReferences",
        # Lists
        "List",
        "ListProperties",
        "NamedRange",
        "NamedRanges",
        "TabsCriteria",
        "BookmarkLink",
        "HeadingLink",
        # Headers/Footers/Footnotes
        "Header",
        "Footer",
        "Footnote",
        # Rich content
        "RichLinkProperties",
        "PersonProperties",
        # Table properties
        "TableColumnProperties",
        # Suggestion states
        "BackgroundSuggestionState",
        "ShadingSuggestionState",
        "SizeSuggestionState",
        "ImagePropertiesSuggestionState",
        "InlineObjectPropertiesSuggestionState",
        "EmbeddedObjectBorderSuggestionState",
        "EmbeddedDrawingPropertiesSuggestionState",
        "EmbeddedObjectSuggestionState",
        "PositionedObjectPositioningSuggestionState",
        "PositionedObjectPropertiesSuggestionState",
        "SheetsChartReferenceSuggestionState",
        "LinkedContentReferenceSuggestionState",
        "ListPropertiesSuggestionState",
        # Suggested types
        "SuggestedBullet",
        "SuggestedDocumentStyle",
        "SuggestedInlineObjectProperties",
        "SuggestedListProperties",
        "SuggestedNamedStyles",
        "SuggestedParagraphStyle",
        "SuggestedPositionedObjectProperties",
        "SuggestedTableCellStyle",
        "SuggestedTableRowStyle",
        "SuggestedTextStyle",
        # Crop properties
        "CropProperties",
        "CropPropertiesSuggestionState",
        # Write control
        "WriteControl",
        # Substring match
        "SubstringMatchCriteria",
    ],
}


def parse_schemas_file(schemas_path: Path) -> dict[str, dict[str, Any]]:
    """Parse the schemas.pyi file and extract TypedDict definitions."""
    with open(schemas_path, encoding="utf-8") as f:
        content = f.read()

    models = {}

    # Split by class definitions
    # Pattern: @typing.type_check_only\nclass ClassName(...):
    class_pattern = r"@typing\.type_check_only\s+class\s+(\w+)\([^)]+\):"

    class_matches = list(re.finditer(class_pattern, content))

    for idx, match in enumerate(class_matches):
        class_name = match.group(1)
        start_pos = match.end()

        # Find the end of this class (start of next class or end of file)
        if idx + 1 < len(class_matches):
            end_pos = class_matches[idx + 1].start()
        else:
            end_pos = len(content)

        class_body = content[start_pos:end_pos]

        # Parse fields from class body
        fields = {}
        lines = class_body.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines, comments, and ellipsis
            if not line or line.startswith("#") or line == "...":
                i += 1
                continue

            # Check if we've hit a non-indented line (next class or end)
            if line and not line.startswith(" ") and ":" not in line:
                break

            # Parse field: type
            field_match = re.match(r"(\w+):\s*(.+)", line)
            if field_match:
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()

                # Handle multi-line Literal types
                if ("Literal[" in field_type or "typing_extensions.Literal[" in field_type) and field_type.count(
                    "["
                ) > field_type.count("]"):
                    # Collect continuation lines until brackets balance
                    i += 1
                    while i < len(lines):
                        next_line = lines[i].strip()
                        if not next_line:
                            i += 1
                            continue
                        field_type += " " + next_line
                        if field_type.count("[") == field_type.count("]"):
                            break
                        i += 1

                fields[field_name] = field_type

            i += 1

        if fields:
            models[class_name] = {"fields": fields}

    return models


def convert_type_to_pydantic(type_str: str) -> str:
    """Convert TypedDict type annotation to Pydantic type annotation."""
    type_str = type_str.strip()

    # Fix known typos in source file
    type_str = type_str.replace("Bod", "Body").replace("Bodyy", "Body")

    # Handle _list[T] -> Optional[List[T]]
    if type_str.startswith("_list["):
        inner = type_str[6:-1]  # Extract content inside brackets
        inner_converted = convert_inner_type(inner)
        return f"Optional[List[{inner_converted}]]"

    # Handle dict[str, typing.Any] -> Optional[Dict[str, Any]]
    if type_str.startswith("dict["):
        inner = type_str[5:-1]
        # Parse dict[K, V]
        parts = inner.split(",", 1)
        if len(parts) == 2:
            key_type = parts[0].strip()
            value_type = parts[1].strip()
            # For dict keys/values, don't double-wrap in Optional
            key_converted = convert_inner_type(key_type)
            value_converted = convert_inner_type(value_type)
            return f"Optional[Dict[{key_converted}, {value_converted}]]"

    # Handle Literal types - convert to typing_extensions.Literal and clean up
    if "Literal[" in type_str:
        # Replace typing_extensions.Literal with Literal (we'll import it)
        literal_cleaned = type_str.replace("typing_extensions.Literal", "Literal")
        # Clean up multi-line formatting - remove extra spaces but preserve structure
        # First, remove leading/trailing spaces from the entire literal
        literal_cleaned = literal_cleaned.strip()
        # Replace multiple spaces/newlines with single space, but preserve quotes
        literal_cleaned = re.sub(r"\s+", " ", literal_cleaned)
        # Clean up spaces around brackets and commas
        literal_cleaned = re.sub(r"\s*\[\s*", "[", literal_cleaned)
        literal_cleaned = re.sub(r"\s*\]\s*", "]", literal_cleaned)
        literal_cleaned = re.sub(r"\s*,\s*", ", ", literal_cleaned)
        # Remove trailing comma before closing bracket
        literal_cleaned = re.sub(r",\s*\]", "]", literal_cleaned)
        return f"Optional[{literal_cleaned}]"

    # Handle basic types
    type_mapping = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "typing.Any": "Any",
    }

    if type_str in type_mapping:
        return f"Optional[{type_mapping[type_str]}]"

    # Handle forward references (model names) - use string annotation
    if re.match(r"^[A-Z][a-zA-Z0-9_]*$", type_str):
        return f'Optional["{type_str}"]'

    # For other types, wrap in Optional
    return f"Optional[{type_str}]"


def convert_inner_type(type_str: str) -> str:
    """Convert inner type (for List, Dict) without wrapping in Optional."""
    type_str = type_str.strip()

    # Fix known typos
    type_str = type_str.replace("Bod", "Body").replace("Bodyy", "Body")

    # Handle basic types
    type_mapping = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "typing.Any": "Any",
    }

    if type_str in type_mapping:
        return type_mapping[type_str]

    # Handle forward references
    if re.match(r"^[A-Z][a-zA-Z0-9_]*$", type_str):
        return f'"{type_str}"'

    # Return as-is (might be a complex type)
    return type_str


def generate_model_code(class_name: str, fields: dict[str, str], base_class: str = "GoogleDocsBaseModel") -> str:
    """Generate Pydantic model code for a class."""
    lines = [f"class {class_name}({base_class}):"]
    lines.append(f'    """{class_name} model from Google Docs API."""')
    lines.append("")

    if not fields:
        lines.append("    pass")
    else:
        for field_name, field_type in fields.items():
            pydantic_type = convert_type_to_pydantic(field_type)
            lines.append(f"    {field_name}: {pydantic_type} = None")

    return "\n".join(lines)


def get_imports_for_file(model_names: list[str], all_models: dict[str, dict[str, Any]]) -> set[str]:
    """Determine what imports are needed for a file based on model dependencies."""
    imports = {"from __future__ import annotations", "from typing import Optional, List, Dict, Any"}

    # Check for Literal usage
    for model_name in model_names:
        if model_name not in all_models:
            continue
        fields = all_models[model_name]["fields"]
        for field_type in fields.values():
            if "Literal[" in field_type or "typing_extensions.Literal" in field_type:
                imports.add("from typing_extensions import Literal")
                break

    return imports


def generate_file_content(
    file_name: str, model_names: list[str], all_models: dict[str, dict[str, Any]], base_import: str
) -> str:
    """Generate the complete content for a model file."""
    lines = []
    lines.append('"""Generated Pydantic models for Google Docs API."""')
    lines.append("")

    # Add imports
    imports = get_imports_for_file(model_names, all_models)
    for imp in sorted(imports):
        lines.append(imp)

    lines.append("")
    lines.append(f"from {base_import}.base import GoogleDocsBaseModel")
    lines.append("")

    # Add model definitions
    for model_name in model_names:
        if model_name not in all_models:
            print(f"Warning: Model {model_name} not found in parsed models")
            continue

        fields = all_models[model_name]["fields"]
        model_code = generate_model_code(model_name, fields)
        lines.append(model_code)
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Main function to generate all Pydantic models."""
    # Paths
    project_root = Path(__file__).parent.parent
    schemas_path = project_root / ".venv/lib/python3.12/site-packages/googleapiclient-stubs/_apis/docs/v1/schemas.pyi"
    models_dir = project_root / "google_docs_markdown/models"

    if not schemas_path.exists():
        # Try alternative path (might be in different Python version)
        venv_base = project_root / ".venv/lib"
        if venv_base.exists():
            python_dirs = [d for d in venv_base.iterdir() if d.is_dir() and d.name.startswith("python")]
            if python_dirs:
                alt_path = python_dirs[0] / "site-packages/googleapiclient-stubs/_apis/docs/v1/schemas.pyi"
                if alt_path.exists():
                    schemas_path = alt_path
                else:
                    raise FileNotFoundError(
                        f"Could not find schemas.pyi. Tried:\n"
                        f"  - {schemas_path}\n"
                        f"  - {alt_path}\n"
                        f"Please ensure google-api-python-client-stubs is installed."
                    )
        else:
            raise FileNotFoundError(
                f"Could not find schemas.pyi at {schemas_path}. "
                "Please ensure google-api-python-client-stubs is installed."
            )

    print(f"Parsing {schemas_path}...")
    all_models = parse_schemas_file(schemas_path)
    print(f"Found {len(all_models)} models")

    # Create models directory
    models_dir.mkdir(parents=True, exist_ok=True)

    # Generate base.py if it doesn't exist (it should already exist, but check)
    base_file = models_dir / "base.py"
    if not base_file.exists():
        print("Creating base.py...")
        base_content = '''"""Base model configuration for Google Docs API Pydantic models."""

from pydantic import BaseModel, ConfigDict


class GoogleDocsBaseModel(BaseModel):
    """Base model for all Google Docs API models."""

    model_config = ConfigDict(
        # Allow population by field name (camelCase from API)
        populate_by_name=True,
        # Allow extra fields for forward compatibility
        extra="allow",
        # Validate assignment (catch errors early)
        validate_assignment=True,
        # Use enum values (not names)
        use_enum_values=True,
    )
'''
        base_file.write_text(base_content)

    # Generate model files
    base_import = "google_docs_markdown.models"
    for file_name, model_names in MODEL_ORGANIZATION.items():
        file_path = models_dir / file_name
        print(f"Generating {file_name}...")
        content = generate_file_content(file_name, model_names, all_models, base_import)
        file_path.write_text(content)
        print(f"  Generated {len([m for m in model_names if m in all_models])} models")

    # Generate __init__.py
    print("Generating __init__.py...")
    init_lines = [
        '"""Google Docs API Pydantic models."""',
        "",
        "# Core document models",
        "from google_docs_markdown.models.document import Document, DocumentTab, Body, Tab, TabProperties",
        "",
        "# Element models",
        "from google_docs_markdown.models.elements import (",
        "    StructuralElement,",
        "    Paragraph,",
        "    Table,",
        "    ParagraphElement,",
        "    TextRun,",
        ")",
        "",
        "# Request/Response models",
        "from google_docs_markdown.models.requests import Request, BatchUpdateDocumentRequest",
        "from google_docs_markdown.models.responses import Response, BatchUpdateDocumentResponse",
        "",
        "# Common models",
        "from google_docs_markdown.models.common import (",
        "    Location,",
        "    Range,",
        "    Color,",
        "    Dimension,",
        ")",
        "",
        "__all__ = [",
        "    # Document",
        '    "Document",',
        '    "DocumentTab",',
        '    "Body",',
        '    "Tab",',
        '    "TabProperties",',
        "    # Elements",
        '    "StructuralElement",',
        '    "Paragraph",',
        '    "Table",',
        '    "ParagraphElement",',
        '    "TextRun",',
        "    # Requests/Responses",
        '    "Request",',
        '    "Response",',
        '    "BatchUpdateDocumentRequest",',
        '    "BatchUpdateDocumentResponse",',
        "    # Common",
        '    "Location",',
        '    "Range",',
        '    "Color",',
        '    "Dimension",',
        "]",
    ]
    init_file = models_dir / "__init__.py"
    init_file.write_text("\n".join(init_lines))

    print("\nModel generation complete!")
    print(f"Generated models in {models_dir}")


if __name__ == "__main__":
    main()
