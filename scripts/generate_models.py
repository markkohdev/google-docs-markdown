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
        "DateElement",
        "DateElementProperties",
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
        "AddDocumentTabRequest",
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
        "DeleteTabRequest",
        "DeleteTableColumnRequest",
        "DeleteTableRowRequest",
        "InsertDateRequest",
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
        "UpdateDocumentTabPropertiesRequest",
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
        "AddDocumentTabResponse",
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
        # Date element suggestion states
        "DateElementPropertiesSuggestionState",
        "SuggestedDateElementProperties",
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

        models[class_name] = {"fields": fields}

    return models


def convert_type_to_pydantic(type_str: str) -> str:
    """Convert TypedDict type annotation to Pydantic-compatible annotation.

    Uses modern union syntax (``X | None``) and lowercase generics
    (``list``, ``dict``) which work at parse time thanks to
    ``from __future__ import annotations``.
    """
    type_str = type_str.strip()

    # Fix known typos in source file
    type_str = type_str.replace("Bod", "Body").replace("Bodyy", "Body")

    if type_str.startswith("_list["):
        inner = type_str[6:-1]
        inner_converted = convert_inner_type(inner)
        return f"list[{inner_converted}] | None"

    if type_str.startswith("dict["):
        inner = type_str[5:-1]
        parts = inner.split(",", 1)
        if len(parts) == 2:
            key_converted = convert_inner_type(parts[0].strip())
            value_converted = convert_inner_type(parts[1].strip())
            return f"dict[{key_converted}, {value_converted}] | None"

    if "Literal[" in type_str:
        literal_cleaned = type_str.replace("typing_extensions.Literal", "Literal")
        literal_cleaned = re.sub(r"\s+", " ", literal_cleaned.strip())
        literal_cleaned = re.sub(r"\s*\[\s*", "[", literal_cleaned)
        literal_cleaned = re.sub(r"\s*\]\s*", "]", literal_cleaned)
        literal_cleaned = re.sub(r"\s*,\s*", ", ", literal_cleaned)
        literal_cleaned = re.sub(r",\s*\]", "]", literal_cleaned)
        return f"{literal_cleaned} | None"

    simple = {"str": "str", "int": "int", "float": "float", "bool": "bool", "typing.Any": "Any"}
    if type_str in simple:
        return f"{simple[type_str]} | None"

    if re.match(r"^[A-Z][a-zA-Z0-9_]*$", type_str):
        return f"{type_str} | None"

    return f"{type_str} | None"


def convert_inner_type(type_str: str) -> str:
    """Convert inner type (for list, dict) without wrapping in ``| None``."""
    type_str = type_str.strip()

    type_str = type_str.replace("Bod", "Body").replace("Bodyy", "Body")

    simple = {"str": "str", "int": "int", "float": "float", "bool": "bool", "typing.Any": "Any"}
    if type_str in simple:
        return simple[type_str]

    # With ``from __future__ import annotations`` the annotation is already a
    # string, so we don't need to quote model names.
    return type_str


def generate_model_code(class_name: str, fields: dict[str, str], base_class: str = "GoogleDocsBaseModel") -> str:
    """Generate Pydantic model code for a class."""
    lines = [f"class {class_name}({base_class}):"]
    if not fields:
        lines.append(f'    """{class_name} model from Google Docs API (currently empty)."""')
        lines.append("")
        lines.append("    pass")
    else:
        lines.append(f'    """{class_name} model from Google Docs API."""')
        lines.append("")
        for field_name, field_type in fields.items():
            pydantic_type = convert_type_to_pydantic(field_type)
            lines.append(f"    {field_name}: {pydantic_type} = None")

    return "\n".join(lines)


FILE_TO_MODULE = {
    "common.py": "google_docs_markdown.models.common",
    "document.py": "google_docs_markdown.models.document",
    "elements.py": "google_docs_markdown.models.elements",
    "styles.py": "google_docs_markdown.models.styles",
    "requests.py": "google_docs_markdown.models.requests",
    "responses.py": "google_docs_markdown.models.responses",
}

RESERVED_TYPE_NAMES = {"Literal", "Optional", "List", "Dict", "Any", "Body"}


def _extract_referenced_models(field_type: str) -> set[str]:
    """Return PascalCase identifiers in *field_type* that look like model names."""
    candidates = set(re.findall(r"\b([A-Z][a-zA-Z0-9_]*)\b", field_type))
    return candidates - RESERVED_TYPE_NAMES


def _compute_type_checking_imports(
    file_name: str,
    model_names: list[str],
    all_models: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    """Return ``{module_path: [name, ...]}`` for cross-module references.

    These will be emitted inside an ``if TYPE_CHECKING:`` block.
    """
    model_to_file: dict[str, str] = {}
    for fn, names in MODEL_ORGANIZATION.items():
        for name in names:
            model_to_file[name] = fn

    external: dict[str, set[str]] = {}
    for model_name in model_names:
        if model_name not in all_models:
            continue
        for field_type in all_models[model_name]["fields"].values():
            for ref in _extract_referenced_models(field_type):
                ref_file = model_to_file.get(ref)
                if ref_file and ref_file != file_name and ref in all_models:
                    external.setdefault(ref_file, set()).add(ref)

    return {FILE_TO_MODULE[f]: sorted(names) for f, names in sorted(external.items())}


def generate_file_content(
    file_name: str, model_names: list[str], all_models: dict[str, dict[str, Any]], base_import: str
) -> str:
    """Generate the complete content for a model file."""
    lines: list[str] = ['"""Generated Pydantic models for Google Docs API."""', ""]
    lines.append("from __future__ import annotations")
    lines.append("")

    # --- determine typing imports ---
    needs_any = False
    needs_literal = False
    for model_name in model_names:
        if model_name not in all_models:
            continue
        for ft in all_models[model_name]["fields"].values():
            if "typing.Any" in ft:
                needs_any = True
            if "Literal[" in ft or "typing_extensions.Literal" in ft:
                needs_literal = True

    tc_imports = _compute_type_checking_imports(file_name, model_names, all_models)

    typing_parts: list[str] = []
    if tc_imports:
        typing_parts.append("TYPE_CHECKING")
    if needs_any:
        typing_parts.append("Any")
    if needs_literal:
        typing_parts.append("Literal")

    if typing_parts:
        lines.append(f"from typing import {', '.join(typing_parts)}")
        lines.append("")

    lines.append(f"from {base_import}.base import GoogleDocsBaseModel")

    # --- TYPE_CHECKING block ---
    if tc_imports:
        lines.append("")
        lines.append("if TYPE_CHECKING:")
        for module, names in tc_imports.items():
            if len(names) <= 3:
                lines.append(f"    from {module} import {', '.join(names)}")
            else:
                lines.append(f"    from {module} import (")
                for name in names:
                    lines.append(f"        {name},")
                lines.append("    )")

    lines.append("")

    # --- model definitions ---
    for model_name in model_names:
        if model_name not in all_models:
            print(f"  Warning: Model {model_name} not found in parsed schemas")
            continue
        fields = all_models[model_name]["fields"]
        model_code = generate_model_code(model_name, fields)
        lines.append("")
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
        "from google_docs_markdown.models import common as _common",
        "from google_docs_markdown.models import document as _document",
        "from google_docs_markdown.models import elements as _elements",
        "from google_docs_markdown.models import requests as _requests",
        "from google_docs_markdown.models import responses as _responses",
        "from google_docs_markdown.models import styles as _styles",
        "from google_docs_markdown.models.base import GoogleDocsBaseModel",
        "",
        "# Common models",
        "from google_docs_markdown.models.common import (",
        "    Color,",
        "    Dimension,",
        "    Location,",
        "    Range,",
        ")",
        "from google_docs_markdown.models.document import Body, Document, DocumentTab, Tab, TabProperties",
        "",
        "# Element models",
        "from google_docs_markdown.models.elements import (",
        "    Paragraph,",
        "    ParagraphElement,",
        "    StructuralElement,",
        "    Table,",
        "    TextRun,",
        ")",
        "",
        "# Request/Response models",
        "from google_docs_markdown.models.requests import BatchUpdateDocumentRequest, InsertTextRequest, Request",
        "from google_docs_markdown.models.responses import BatchUpdateDocumentResponse, Response",
        "",
        "# Collect all model classes into a shared namespace for forward reference resolution",
        "_namespace: dict[str, type] = {}",
        "for _module in [_common, _styles, _elements, _document, _requests, _responses]:",
        "    for _name in dir(_module):",
        "        _obj = getattr(_module, _name)",
        "        if isinstance(_obj, type) and issubclass(_obj, GoogleDocsBaseModel):",
        "            _namespace[_name] = _obj",
        "",
        "# Rebuild all models so Pydantic can resolve cross-module forward references",
        "for _model_cls in _namespace.values():",
        "    if hasattr(_model_cls, 'model_rebuild'):",
        "        _model_cls.model_rebuild(_types_namespace=_namespace)  # type: ignore[union-attr]",
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
        '    "InsertTextRequest",',
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
