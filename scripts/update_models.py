#!/usr/bin/env python3
"""
Update google-api-python-client-stubs and regenerate Pydantic models if the version changed.

Also bumps the >= constraint in pyproject.toml and re-locks all dependencies so
transitive updates (e.g. google-api-python-client) are picked up.

Usage:
    uv run python scripts/update_models.py
    # or: make update-models
"""

from __future__ import annotations

import re
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PACKAGE = "google-api-python-client-stubs"
PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


def get_installed_version() -> str | None:
    try:
        return version(PACKAGE)
    except PackageNotFoundError:
        return None


def get_installed_version_subprocess() -> str | None:
    """Get the version via a fresh subprocess to avoid stale importlib caches."""
    result = subprocess.run(
        [sys.executable, "-c", f"from importlib.metadata import version; print(version('{PACKAGE}'))"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def update_pyproject_constraint(package: str, new_version: str) -> bool:
    """Bump the >= version constraint for *package* in pyproject.toml.

    Returns True if the file was changed.
    """
    content = PYPROJECT_PATH.read_text()
    pattern = rf'("{re.escape(package)}\s*>=\s*)[^"]*(")'
    new_content, count = re.subn(pattern, rf"\g<1>{new_version}\2", content)
    if count > 0 and new_content != content:
        PYPROJECT_PATH.write_text(new_content)
        return True
    return False


def upgrade_package() -> None:
    subprocess.run(["uv", "lock", "--upgrade-package", PACKAGE], check=True)
    subprocess.run(["uv", "sync"], check=True)


def regenerate_models() -> None:
    subprocess.run([sys.executable, "scripts/generate_models.py"], check=True)


def main() -> None:
    before = get_installed_version()
    print(f"Current {PACKAGE} version: {before or '(not installed)'}")

    print(f"Upgrading {PACKAGE}...")
    upgrade_package()

    after = get_installed_version_subprocess()
    print(f"Post-upgrade {PACKAGE} version: {after or '(not installed)'}")

    if after and update_pyproject_constraint(PACKAGE, after):
        print(f"Updated {PACKAGE} constraint in pyproject.toml to >={after}")
        print("Re-locking all dependencies...")
        subprocess.run(["uv", "lock", "--upgrade"], check=True)
        subprocess.run(["uv", "sync"], check=True)

    if before != after:
        print(f"Version changed ({before} -> {after}). Regenerating models...")
        regenerate_models()
        return

    print("No version change detected.")
    answer = input("Regenerate models anyway? [y/N] ").strip().lower()
    if answer in ("y", "yes"):
        print("Regenerating models...")
        regenerate_models()
    else:
        print("Skipping model regeneration.")


if __name__ == "__main__":
    main()
