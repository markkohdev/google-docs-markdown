.PHONY: help test lint format type-check check all clean

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
test: lint format-check type-check run-tests

# Run all fixers
fix: lint-fix format-fix

# Alias for check
all: check

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

