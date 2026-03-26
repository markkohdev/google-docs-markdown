---
name: fix-tests
description: >-
  Run `make test` and automatically identify and fix any failures including
  formatting, linting, type errors, and pytest test failures. Use when the user
  asks to fix tests, run tests, fix failing checks, or resolve test errors.
---

# Fix Tests

Run the full test suite and iteratively fix all failures.

## Workflow

### Step 1: Run `make test`

```bash
make test
```

This runs the full pipeline in order:
1. `format-fix` — auto-fix formatting with ruff
2. `lint-fix` — auto-fix lint issues with ruff
3. `format-check` — verify formatting
4. `lint-check` — verify linting
5. `type-check` — run mypy
6. `run-tests` — run pytest

If the command succeeds with exit code 0, report success and stop.

### Step 2: Identify the failure stage

Read the terminal output to determine which stage failed:

| Output pattern | Stage | Fix approach |
|---|---|---|
| `ruff format` errors after auto-fix | Formatting | Manually fix the formatting issue ruff couldn't auto-fix |
| `ruff check` errors after auto-fix | Linting | Read the error, fix the code (usually import ordering, unused vars, etc.) |
| `mypy` errors | Type checking | Fix type annotations, add type ignores only as last resort |
| `pytest` failures | Tests | Read the failing test and source code, fix the root cause |

### Step 3: Fix failures

**For formatting/linting failures:**
- Read the specific error messages from the output
- Fix the source files directly
- These are usually straightforward fixes

**For type-check (mypy) failures:**
- Read the error message and the referenced file/line
- Fix type annotations in the source code
- Prefer proper typing over `# type: ignore`

**For pytest failures:**
- Read the full traceback to understand the failure
- Read both the test file and the source file being tested
- Determine if the bug is in the test or the source code:
  - If a test expectation is wrong (e.g., the source behavior is intentionally changed), update the test
  - If the source code has a bug, fix the source code
- For assertion errors, compare expected vs actual output carefully

### Step 4: Re-run and iterate

After making fixes, re-run `make test`. Repeat Steps 2-4 until all checks pass.

**Important:** Cap iterations at 5 attempts. If still failing after 5 rounds, report the remaining failures to the user and ask for guidance.

## Tips

- `make test` auto-runs `format-fix` and `lint-fix` first, so many formatting/linting issues self-resolve. Focus on errors that persist after the auto-fix stages.
- When pytest fails, always read the actual test code — don't guess at what it asserts.
- When mypy fails, check if the issue is a missing stub package before modifying code.
