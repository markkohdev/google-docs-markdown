#!/usr/bin/env python3
"""
Update google-api-python-client-stubs and regenerate Pydantic models if the version changed.

Usage:
    uv run python scripts/update_models.py
    # or: make update-models
"""

from __future__ import annotations

import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

PACKAGE = "google-api-python-client-stubs"


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

    if before == after:
        print("No version change detected. Skipping model regeneration.")
        return

    print(f"Version changed ({before} -> {after}). Regenerating models...")
    regenerate_models()


if __name__ == "__main__":
    main()
