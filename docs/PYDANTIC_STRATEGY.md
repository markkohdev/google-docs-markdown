# Pydantic Migration Strategy for Google Docs Markdown

**Date:** 2026-01-08  
**Status:** Strategy Document (Pre-Implementation)

## Overview

This document outlines the strategy for migrating from `google-api-python-client-stubs` TypedDicts to Pydantic models, enabling attribute-based access (`my_doc.title`) instead of dictionary access (`my_doc.get("title")`), and establishing patterns for serializing/deserializing between Pydantic models and Markdown.

## Goals

1. **Replace TypedDict usage** with Pydantic models for better developer experience
2. **Enable attribute access** (`doc.title` instead of `doc.get("title")`)
3. **Maintain API compatibility** - seamlessly convert between Pydantic models and dicts for Google Docs API
4. **Establish markdown conversion patterns** - serialize Pydantic models to Markdown and deserialize Markdown back to Pydantic models

## Part 1: Converting TypedDict Schemas to Pydantic Models

### 1.1 Schema Conversion Strategy

**Source:** `.venv/lib/python3.12/site-packages/googleapiclient-stubs/_apis/docs/v1/schemas.pyi`

**Approach:**
1. Create a new module `google_docs_markdown/models/` to house all Pydantic models
2. Convert each TypedDict class to a Pydantic `BaseModel`
3. Handle `total=False` TypedDicts (all fields optional) using Pydantic's `Optional` types
4. Preserve field names exactly as they appear in the API (camelCase)
5. Use Pydantic's `Field` for additional metadata when needed

### 1.2 Conversion Patterns

**TypedDict Pattern:**
```python
@typing.type_check_only
class Document(typing_extensions.TypedDict, total=False):
    body: Body
    documentId: str
    title: str
    tabs: _list[Tab]
```

**Pydantic Model Pattern:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class Document(BaseModel):
    body: Optional[Body] = None
    documentId: Optional[str] = None
    title: Optional[str] = None
    tabs: Optional[List[Tab]] = None
    
    class Config:
        # Allow population by field name (camelCase from API)
        populate_by_name = True
        # Allow extra fields (for forward compatibility)
        extra = "allow"
```

### 1.3 Handling Complex Types

**Nested Models:**
- Convert nested TypedDicts to nested Pydantic models
- Use forward references with `from __future__ import annotations` for circular dependencies

**Union Types:**
- Use Pydantic's `Union` or discriminated unions for polymorphic types
- Example: `StructuralElement` can be `Paragraph | Table | SectionBreak`

**Literal Types:**
- Preserve `Literal` types exactly as they appear
- Example: `suggestionsViewMode: Literal["DEFAULT_FOR_CURRENT_ACCESS", "SUGGESTIONS_INLINE", ...]`

**Dict Types:**
- For `dict[str, typing.Any]` fields, use `Dict[str, Any]` in Pydantic
- Consider creating specific models if the dict structure is known

### 1.4 Model Generation Script

**Approach:** Instead of manually converting each TypedDict, we'll create a script that automatically generates all Pydantic models from the `google-api-python-client-stubs` source code.

**Script Location:** `scripts/generate_models.py`

**Script Responsibilities:**
1. Parse the `.pyi` stub file (`.venv/lib/python3.12/site-packages/googleapiclient-stubs/_apis/docs/v1/schemas.pyi`)
2. Extract TypedDict class definitions
3. Convert each TypedDict to a Pydantic model following the patterns in section 1.2
4. Handle forward references and circular dependencies
5. Organize models into appropriate files (document.py, elements.py, etc.)
6. Generate proper imports and module structure

**Script Implementation Strategy:**
- Parse the `.pyi` file to extract TypedDict class definitions
- **Approach Options:**
  - **Option A (Recommended):** Use `ast` module to parse the Python AST, but note that `.pyi` files may have type-check-only constructs that `ast` can't parse directly
  - **Option B:** Use regex/string parsing to extract class definitions and type annotations (more flexible for `.pyi` files)
  - **Option C:** Use a combination - parse with `ast` where possible, fall back to regex for type-check-only constructs
- Extract class name, field names, and type annotations
- Convert `total=False` TypedDicts to Pydantic models with all `Optional` fields
- Handle forward references by generating models in dependency order or using string annotations
- Map TypedDict types to Pydantic equivalents:
  - `_list[T]` → `Optional[List[T]]`
  - `dict[str, typing.Any]` → `Optional[Dict[str, Any]]`
  - `Literal[...]` → preserve as `Literal[...]`
  - Forward references → use string annotations
- Organize models into files based on logical groupings
- Generate proper imports and module structure
- Write generated code to appropriate files in `google_docs_markdown/models/`

**Script Usage:**
```bash
# Run the generation script
python scripts/generate_models.py

# This will:
# 1. Read schemas.pyi from the installed stubs package
# 2. Generate all Pydantic models
# 3. Write them to google_docs_markdown/models/
# 4. Format with black/ruff
```

**Benefits:**
- Generate all models at once (100+ models)
- Consistent conversion patterns
- Easy to regenerate when stubs are updated
- Reduces manual conversion errors

**Post-Generation:**
- Review generated models for correctness
- Manually adjust edge cases if needed
- Add custom methods/validators where appropriate
- Run tests to verify models work with real API responses

### 1.5 Model Organization

**Structure:**
```
google_docs_markdown/models/
├── __init__.py
├── base.py              # BaseModel configuration
├── document.py          # Document, DocumentTab, Body (generated)
├── elements.py          # StructuralElement, Paragraph, Table, etc. (generated)
├── styles.py            # TextStyle, ParagraphStyle, etc. (generated)
├── requests.py          # Request types for batchUpdate (generated)
└── responses.py         # Response types (generated)
```

**Import Strategy:**
- Export commonly used models from `__init__.py`
- Use lazy imports for less common models to avoid circular dependencies
- Generated models can be imported directly or via `__init__.py`

## Part 2: Google Docs API Integration

### 2.1 Converting API Responses to Pydantic Models

**Pattern:**
```python
from google_docs_markdown.models import Document

# API returns dict
api_response: dict = client.get_document(document_id)

# Convert to Pydantic model
doc: Document = Document.model_validate(api_response)

# Now use attribute access
title = doc.title  # Instead of doc.get("title")
```

**Error Handling:**
- Use Pydantic's validation errors to catch API schema mismatches
- Log validation errors for debugging
- Consider `model_validate` with `strict=False` for forward compatibility

### 2.2 Converting Pydantic Models Back to API Format

**Pattern:**
```python
# Convert Pydantic model to dict for API
doc_dict: dict = doc.model_dump(exclude_none=True, by_alias=True)

# Use in API calls
client.create_document(body=doc_dict)
client.batch_update(document_id, requests=requests_dict)
```

**Key Considerations:**
- Use `exclude_none=True` to match API expectations (API doesn't expect `None` values)
- Use `by_alias=True` if using field aliases
- Consider `mode='json'` for JSON serialization if needed

### 2.3 Updating API Client

**Changes to `api_client.py`:**
```python
from google_docs_markdown.models import Document, Request, Response

class GoogleDocsAPIClient:
    def get_document(self, document_id: str) -> Document:
        """Return Pydantic model instead of dict."""
        result = self.service.documents().get(...).execute()
        return Document.model_validate(result)
    
    def batch_update(
        self, 
        document_id: str, 
        requests: list[Request]
    ) -> list[Response]:
        """Accept Pydantic models, convert to dicts for API."""
        requests_dict = [r.model_dump(exclude_none=True) for r in requests]
        result = self.service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests_dict}
        ).execute()
        return [Response.model_validate(r) for r in result.get("replies", [])]
```

## Part 3: Markdown Serialization Strategy

### 3.1 High-Level Approach

Markdown conversion is **not** a built-in Pydantic feature. We need to implement custom serialization/deserialization logic that:

1. **Traverses** the Pydantic model structure (Document → Body → StructuralElements → ParagraphElements)
2. **Converts** each element to its Markdown representation
3. **Handles** formatting, links, images, tables, etc.
4. **Preserves** metadata that doesn't map to Markdown (via HTML comments or JSON)

### 3.2 Design Pattern: Visitor Pattern

**Why Visitor Pattern:**
- Google Docs has a hierarchical structure (Document → Body → Elements → Paragraph Elements)
- Each element type needs different Markdown conversion logic
- Visitor pattern allows clean separation of traversal and conversion logic

**Structure:**
```python
from abc import ABC, abstractmethod
from google_docs_markdown.models import (
    Document, Paragraph, Table, TextRun, 
    StructuralElement, ParagraphElement
)

class MarkdownVisitor(ABC):
    """Base visitor for converting Pydantic models to Markdown."""
    
    @abstractmethod
    def visit_document(self, doc: Document) -> str:
        pass
    
    @abstractmethod
    def visit_paragraph(self, para: Paragraph) -> str:
        pass    
    
    @abstractmethod
    def visit_table(self, table: Table) -> str:
        pass
    
    @abstractmethod
    def visit_text_run(self, text_run: TextRun) -> str:
        pass
    
    # ... more visit methods
```

**Implementation:**
```python
class MarkdownSerializer(MarkdownVisitor):
    """Converts Pydantic models to Markdown."""
    
    def visit_document(self, doc: Document) -> str:
        """Convert Document to Markdown."""
        if not doc.body or not doc.body.content:
            return ""
        
        markdown_parts = []
        for element in doc.body.content:
            markdown_parts.append(self.visit_structural_element(element))
        
        return "\n\n".join(markdown_parts)
    
    def visit_structural_element(self, element: StructuralElement) -> str:
        """Dispatch to appropriate visitor method."""
        if isinstance(element, Paragraph):
            return self.visit_paragraph(element)
        elif isinstance(element, Table):
            return self.visit_table(element)
        # ... handle other types
        else:
            return ""  # or raise NotImplementedError
    
    def visit_paragraph(self, para: Paragraph) -> str:
        """Convert Paragraph to Markdown."""
        if not para.elements:
            return ""
        
        # Handle heading styles
        style = para.paragraphStyle
        if style and style.namedStyleType:
            level = self._get_heading_level(style.namedStyleType)
            if level:
                content = self._visit_paragraph_elements(para.elements)
                return f"{'#' * level} {content}"
        
        # Handle lists
        if para.bullet:
            content = self._visit_paragraph_elements(para.elements)
            return f"- {content}"  # Simplified
        
        # Regular paragraph
        return self._visit_paragraph_elements(para.elements)
    
    def visit_text_run(self, text_run: TextRun) -> str:
        """Convert TextRun to Markdown with formatting."""
        content = text_run.content or ""
        style = text_run.textStyle
        
        if not style:
            return content
        
        # Apply formatting
        if style.bold:
            content = f"**{content}**"
        if style.italic:
            content = f"*{content}*"
        if style.strikethrough:
            content = f"~~{content}~~"
        if style.link:
            content = f"[{content}]({style.link.url})"
        
        return content
    
    # ... more methods
```

### 3.3 Alternative: Model Methods

**Approach:** Add serialization methods directly to Pydantic models

**Pros:**
- Co-located with model definition
- Easy to access model fields
- Type-safe

**Cons:**
- Mixes concerns (data model + serialization)
- Harder to swap serialization strategies
- Can bloat model classes

**Example:**
```python
class Paragraph(BaseModel):
    elements: Optional[List[ParagraphElement]] = None
    paragraphStyle: Optional[ParagraphStyle] = None
    
    def to_markdown(self) -> str:
        """Convert this paragraph to Markdown."""
        # Implementation here
        pass
```

**Recommendation:** Use Visitor Pattern for flexibility and separation of concerns.

### 3.4 Markdown Library Integration

**Library Choice:** `markdown-it-py` (as recommended in DEVELOPMENT_PLAN.md)

**Important Clarification:** `markdown-it-py` is used **ONLY for deserialization** (Markdown → Pydantic), **NOT for serialization** (Pydantic → Markdown).

**Serialization (Pydantic → Markdown):**
- **Build Markdown strings manually** using the Visitor Pattern (section 3.2)
- We have full control over the output format
- We know the structure of our Pydantic models
- No need for a Markdown library - we're generating Markdown, not parsing it

**Deserialization (Markdown → Pydantic):**
- **Use `markdown-it-py` to parse Markdown** into tokens
- Traverse the token stream to build Pydantic models
- Handle Markdown syntax (headings, lists, links, etc.) by examining token types

**Pattern:**

**Serialization (no markdown-it-py needed):**
```python
class MarkdownSerializer(MarkdownVisitor):
    """Converts Pydantic models to Markdown - builds strings directly."""
    
    def visit_paragraph(self, para: Paragraph) -> str:
        """Build Markdown string directly from Pydantic model."""
        # No markdown library needed - we're generating Markdown
        content = self._visit_paragraph_elements(para.elements)
        if para.paragraphStyle and para.paragraphStyle.namedStyleType == "HEADING_1":
            return f"# {content}"
        return content
```

**Deserialization (uses markdown-it-py):**
```python
from markdown_it import MarkdownIt

class MarkdownDeserializer:
    """Converts Markdown to Pydantic models - uses markdown-it-py for parsing."""
    
    def __init__(self):
        # Initialize markdown-it-py parser
        self.md = MarkdownIt()
    
    def parse(self, markdown: str) -> Document:
        """Parse Markdown string into Document model."""
        # Parse Markdown into tokens using markdown-it-py
        tokens = self.md.parse(markdown)
        
        # Traverse tokens and build Pydantic models
        body_content = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.type == 'heading_open':
                # Extract heading level from token tag (h1, h2, etc.)
                level = int(token.tag[1])  # 'h1' -> 1
                # Get heading content from next tokens
                heading_text = self._extract_text_until_close(tokens, i, 'heading_close')
                para = self._create_heading_paragraph(heading_text, level)
                body_content.append(para)
                i = self._skip_until_close(tokens, i, 'heading_close')
            
            elif token.type == 'paragraph_open':
                # Extract paragraph content
                para_text = self._extract_text_until_close(tokens, i, 'paragraph_close')
                para = self._create_paragraph(para_text)
                body_content.append(para)
                i = self._skip_until_close(tokens, i, 'paragraph_close')
            
            # ... handle other token types (lists, links, etc.)
            
            i += 1
        
        return Document(body=Body(content=body_content))
    
    def _extract_text_until_close(self, tokens, start_idx, close_type):
        """Extract text content between open and close tokens."""
        # Implementation to extract text and handle inline formatting
        pass
```

**Why This Approach:**
- **Serialization:** We control the output, so we build Markdown strings directly
- **Deserialization:** We need to parse arbitrary Markdown, so we use `markdown-it-py` to handle all the edge cases and syntax variations

### 3.5 Deserialization Strategy (Markdown → Pydantic)

**Challenge:** Markdown is lossy - many Google Docs features don't map to Markdown

**Approach:**
1. **Parse Markdown** into tokens using `markdown-it-py`
2. **Build Pydantic models** by traversing tokens
3. **Restore metadata** from HTML comments and JSON files
4. **Apply defaults** for features not representable in Markdown

**Pattern:**
```python
class MarkdownDeserializer:
    def parse(self, markdown: str, metadata: Optional[dict] = None) -> Document:
        """Parse Markdown to Document model."""
        tokens = self.md.parse(markdown)
        
        # Extract metadata from HTML comments
        metadata = metadata or {}
        metadata.update(self._extract_html_comments(markdown))
        
        # Build document structure
        body_content = []
        for token in tokens:
            if token.type == 'heading_open':
                para = self._parse_heading(token, tokens)
                body_content.append(para)
            elif token.type == 'paragraph_open':
                para = self._parse_paragraph(token, tokens)
                body_content.append(para)
            # ... handle other token types
        
        return Document(
            body=Body(content=body_content),
            # Apply metadata
            **metadata
        )
```

### 3.6 Handling Metadata

**Strategy:** As outlined in TECH_SPEC.md section 5.8

**HTML Comments (User-Editable):**
```python
def serialize_metadata_inline(self, doc: Document) -> str:
    """Add metadata as HTML comments in Markdown."""
    markdown = self.visit_document(doc)
    
    # Add date pickers, custom colors, etc. as comments
    comments = []
    for element in doc.body.content:
        if isinstance(element, DateElement):
            comments.append(
                f"<!-- date-picker: {element.model_dump_json()} -->"
            )
    
    return markdown + "\n\n" + "\n".join(comments)
```

**Companion JSON Files:**
```python
def serialize_with_metadata_file(self, doc: Document, base_path: Path) -> None:
    """Serialize document and metadata to separate files."""
    markdown = self.visit_document(doc)
    
    # Write Markdown
    markdown_path = base_path / "document.md"
    markdown_path.write_text(markdown)
    
    # Write metadata
    metadata = self._extract_metadata(doc)
    metadata_path = base_path / "document.metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, default=str)
    )
```

## Part 4: Implementation Strategy

### 4.1 Phased Approach

**Phase 0: Model Generation Script** (Prerequisite)
1. Create `scripts/generate_models.py` script
2. Implement TypedDict → Pydantic model conversion logic
3. Handle edge cases (forward references, unions, literals, etc.)
4. Generate all models to `google_docs_markdown/models/`
5. Review and test generated models with sample API responses
6. Document any manual adjustments needed

**Phase 1: Core Models & API Integration**
1. Set up `google_docs_markdown/models/` module structure
2. Create base model configuration (`base.py`)
3. Run model generation script (Phase 0)
4. Update `api_client.py` to use Pydantic models
5. Test API round-trip (dict → Pydantic → dict)
6. Verify essential models work: `Document`, `DocumentTab`, `Body`, `Paragraph`, `TextRun`

**Phase 2: Markdown Serialization**
1. Implement `MarkdownSerializer` visitor
2. Handle basic elements: paragraphs, headings, text formatting
3. Test serialization: Pydantic → Markdown

**Phase 3: Markdown Deserialization**
1. Implement `MarkdownDeserializer`
2. Parse Markdown tokens to Pydantic models
3. Test deserialization: Markdown → Pydantic
4. Test round-trip: Pydantic → Markdown → Pydantic

**Phase 4: Advanced Features**
1. Convert remaining models (tables, images, etc.)
2. Handle complex features (footnotes, headers, footers)
3. Implement metadata serialization/deserialization

### 4.2 Testing Strategy

**Unit Tests:**
- Test model conversion: `Document.model_validate(api_dict)`
- Test model serialization: `doc.model_dump(exclude_none=True)`
- Test markdown serialization: `serializer.visit_document(doc)`
- Test markdown deserialization: `deserializer.parse(markdown)`

**Integration Tests:**
- Test API → Pydantic → API round-trip
- Test Pydantic → Markdown → Pydantic round-trip
- Test with real Google Docs API responses

**Determinism Tests:**
- Same Pydantic model always produces same Markdown
- Same Markdown (with same metadata) always produces same Pydantic model

## Part 5: Pydantic Configuration

### 5.1 Base Model Configuration

**Create `google_docs_markdown/models/base.py`:**
```python
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
```

**Usage:**
```python
from google_docs_markdown.models.base import GoogleDocsBaseModel

class Document(GoogleDocsBaseModel):
    # All models inherit the config
    pass
```

### 5.2 Field Aliases (Optional)

**If you want snake_case in Python but camelCase in API:**
```python
from pydantic import Field, AliasChoices

class Document(GoogleDocsBaseModel):
    document_id: Optional[str] = Field(
        default=None,
        alias="documentId",
        validation_alias=AliasChoices("documentId", "document_id")
    )
    # Access as: doc.document_id (Python) or doc.documentId (API)
```

**Recommendation:** Keep camelCase field names to match API exactly (simpler, less confusion).

## Part 6: Benefits and Trade-offs

### Benefits

1. **Better Developer Experience:**
   - `doc.title` instead of `doc.get("title")`
   - IDE autocomplete and type checking
   - Runtime validation

2. **Type Safety:**
   - Catch errors at runtime with Pydantic validation
   - Better static type checking with mypy

3. **Flexibility:**
   - Easy to add computed properties
   - Easy to add validation logic
   - Easy to add helper methods

4. **Serialization:**
   - Built-in JSON/dict conversion
   - Custom serialization hooks available

### Trade-offs

1. **Performance:**
   - Pydantic models have slight overhead vs. dicts
   - Validation adds processing time
   - Mitigation: Use `model_validate` with `strict=False` for trusted API responses

2. **Complexity:**
   - More code to maintain (model definitions)
   - Need to keep models in sync with API changes
   - Mitigation: Generate models from API schema if possible

3. **Memory:**
   - Pydantic models use more memory than dicts
   - Usually negligible for document-sized objects

## Part 7: Open Questions

1. **Model Generation Script Details:** 
   - What parsing approach? (AST parsing vs. regex/string parsing)
   - How to handle forward references automatically?
   - Should script be idempotent (can re-run safely)?
2. **Validation Strictness:** How strict should validation be? (Strict vs. lenient for API compatibility)
3. **Field Names:** Keep camelCase or convert to snake_case? (Decided: Keep camelCase)
4. **Backward Compatibility:** How to handle API schema changes gracefully?
5. **Markdown Library:** Finalized - using `markdown-it-py` for parsing only (deserialization)

## Next Steps

1. Review and approve this strategy
2. **Create model generation script** (`scripts/generate_models.py`)
3. Set up `google_docs_markdown/models/` module structure
4. Create base model configuration (`base.py`)
5. **Run model generation script** to generate all Pydantic models
6. Review and test generated models
7. Update API client to use Pydantic models
8. Implement basic Markdown serializer (Visitor Pattern, no markdown library)
9. Implement Markdown deserializer (using `markdown-it-py` for parsing)
10. Test end-to-end workflow

