.PHONY: help test lint format type-check check all clean update-docs update-models update-api-reference update-all

help:
	@echo "Available commands:"
	@echo "  make test        - Run tests with pytest"
	@echo "  make lint        - Run ruff linter"
	@echo "  make format      - Check code formatting with ruff"
	@echo "  make format-fix  - Auto-fix formatting issues with ruff"
	@echo "  make type-check  - Run mypy type checker"
	@echo "  make check       - Run all checks (lint, format, type-check, test)"
	@echo "  make all         - Same as 'make check'"
	@echo "  make clean       - Clean cache files"
	@echo "  make update-docs    - Re-download all test doc JSONs from Google Docs API"
	@echo "  make update-models  - Update stubs and regenerate Pydantic models if needed"
	@echo "  make update-api-reference - Re-download Google Docs API reference text"
	@echo "  make update-all     - Update docs, models, and API reference"

# Run tests
run-tests:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=google_docs_markdown --cov-report=term-missing

# Run linter
lint-check:
	uv run ruff check .

# Auto-fix linting issues
lint-fix:
	uv run ruff check --fix .

# Ruff unsafe fixes
lint-fix-unsafe:
	uv run ruff check --fix --unsafe-fixes .

# Check formatting (without modifying files)
format-check:
	uv run ruff format --check .

# Auto-fix formatting issues
format-fix:
	uv run ruff format .

# Run type checker
type-check:
	uv run mypy google_docs_markdown tests

# Run all checks
test: format-fix lint-fix format-check lint-check type-check run-tests

# Run all fixers
fix: lint-fix format-fix

# Update test fixture JSONs from Google Docs API
update-docs:
	uv run python scripts/download_test_doc.py --urls-file tests/resources/document_jsons/doc_urls.txt --pretty --overwrite

# Update stubs and regenerate Pydantic models if the stubs version changed
update-models:
	uv run python scripts/update_models.py

# Re-download Google Docs API reference as plain text
update-api-reference:
	uv run scripts/download_api_reference.py

# Update all generated artifacts (docs, models, etc.)
update-all: update-docs update-models update-api-reference

# Alias for check
all: check

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

