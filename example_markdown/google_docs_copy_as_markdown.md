# Markdown Conversion Example

## Document Subtitle

Author: [Mark Koh](mailto:markkoh@spotify.com)  
Date: 2026-01-08

**Table of Contents**

[Project Overview: Markdown Tool Testing (Heading 1\)](#project-overview:-markdown-tool-testing-\(heading-1\))

[Section 1: Headings and Structure (Heading 2\)](#section-1:-headings-and-structure-\(heading-2\))

[Subsection 1.1: Lower Level Headings (Heading 3\)](#subsection-1.1:-lower-level-headings-\(heading-3\))

[Sub-Subsection 1.1.1: Deeper Dive (Heading 4\)](#sub-subsection-1.1.1:-deeper-dive-\(heading-4\))

[Sub-Sub-Subsection 1.1.1.1: Specific Detail (Heading 5\)](#sub-sub-subsection-1.1.1.1:-specific-detail-\(heading-5\))

[Sub-Sub-Sub-Subsection 1.1.1.1.1: Very detailed Level (Heading 6\)](#sub-sub-sub-subsection-1.1.1.1.1:-very-detailed-level-\(heading-6\))

[Section 2: Visual and Collaborative Elements (Heading 2\)](#section-2:-visual-and-collaborative-elements-\(heading-2\))

[Images (Heading 3\)](#images-\(heading-3\))

[Colored Text (Heading 3\)](#colored-text-\(heading-3\))

[Section 3: Data and Interactive Elements (Heading 2\)](#section-3:-data-and-interactive-elements-\(heading-2\))

[Tables (Heading 3\)](#tables-\(heading-3\))

[Item Pickers (Chips) (Heading 3\)](#item-pickers-\(chips\)-\(heading-3\))

[Code Blocks (Heading 3\)](#code-blocks-\(heading-3\))

# Project Overview: Markdown Tool Testing (Heading 1\) {#project-overview:-markdown-tool-testing-(heading-1)}

This document serves as a comprehensive example to test the fidelity of a Google Docs to Markdown conversion tool. It incorporates various complex and common document elements to ensure accurate translation.

## Section 1: Headings and Structure (Heading 2\) {#section-1:-headings-and-structure-(heading-2)}

This section focuses on testing the nested structure of headings, which should map correctly to Markdown's `#` syntax.

### Subsection 1.1: Lower Level Headings (Heading 3\) {#subsection-1.1:-lower-level-headings-(heading-3)}

This part of the document ensures that all heading levels, from 1 down to 6, are correctly parsed and converted.

#### Sub-Subsection 1.1.1: Deeper Dive (Heading 4\) {#sub-subsection-1.1.1:-deeper-dive-(heading-4)}

The tool should be able to handle this level without issue, maintaining the hierarchical integrity of the document.

##### Sub-Sub-Subsection 1.1.1.1: Specific Detail (Heading 5\) {#sub-sub-subsection-1.1.1.1:-specific-detail-(heading-5)}

This level is rarely used but is included for thorough testing of the heading structure.

###### *Sub-Sub-Sub-Subsection 1.1.1.1.1: Very detailed Level (Heading 6\)* {#sub-sub-sub-subsection-1.1.1.1.1:-very-detailed-level-(heading-6)}

This is a very low level heading supported by Google Docs and Markdown.

## Section 2: Visual and Collaborative Elements (Heading 2\) {#section-2:-visual-and-collaborative-elements-(heading-2)}

### Images (Heading 3\) {#images-(heading-3)}

The converter must be able to handle embedded image with the appropriate size, alignment, and cropping

![][image1]

### Colored Text (Heading 3\) {#colored-text-(heading-3)}

This text **should be bold**. This text *should be italic*. This text has a blue highlight and red font color.

## Section 3: Data and Interactive Elements (Heading 2\) {#section-3:-data-and-interactive-elements-(heading-2)}

### Tables (Heading 3\) {#tables-(heading-3)}

Tables are a crucial element for data representation and should be converted into Markdown table format (using pipes `|`). Pinned headers should be maintained.

| Header 1 | Header 2 | Header 3 |
| ----- | ----- | ----- |
| Data A1 | Data B1 | Data C1 |
| Data A2 | Data B2 | Data C2 |
| Data A3 | Data B3 | Data C3 |

### Item Pickers (Chips) (Heading 3\) {#item-pickers-(chips)-(heading-3)}

Item Pickers (or Smart Chips) are special interactive elements in Google Docs. The converter must decide how to represent this in plain Markdown text.

* **Project Lead:** [Mark Koh](mailto:markkoh@spotify.com)  
* Other person: Person  
* **Status Chip:** Not Started  
* **File Chip:** File  
* **Date Chip:** 2026-01-08 Date

### Code Blocks (Heading 3\) {#code-blocks-(heading-3)}

The tool must correctly identify and preserve pre-formatted text, typically using Markdown's fenced code blocks (three backticks ```` ``` ````).

```py
def calculate_markdown_conversion(doc_content):
    """Placeholder for a Python function."""
    if "table_of_contents" in doc_content:
        return "TOC converted"
    else:
        return "Content converted"
```

### This is an inline suggestion heading

This is an inline suggestion  


[image1]: <data:image/png;base64,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>