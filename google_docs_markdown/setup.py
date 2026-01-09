"""
Setup module for Google Docs Markdown tool.

Handles authentication, project configuration, and API enablement.
"""

import subprocess
import sys
from typing import Optional

import typer

from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Required scopes for the application
REQUIRED_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/sqlservice.login",
    "https://www.googleapis.com/auth/documents",
]

# Google Docs API service name
DOCS_API_SERVICE = "docs.googleapis.com"


def check_gcloud_installed() -> bool:
    """Check if gcloud CLI is installed."""
    try:
        subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_credentials_exist() -> bool:
    """Check if Application Default Credentials are already configured."""
    try:
        credentials, _ = default(scopes=REQUIRED_SCOPES)
        # If we can get credentials with the required scopes, they're configured
        return credentials is not None
    except DefaultCredentialsError:
        return False
    except Exception:
        # Any other exception means credentials might exist but aren't valid
        return False


def get_current_project() -> Optional[str]:
    """Get the current default GCP project."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        project = result.stdout.strip()
        return project if project else None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def list_available_projects() -> list[str]:
    """List available GCP projects."""
    try:
        result = subprocess.run(
            ["gcloud", "projects", "list", "--format=value(projectId)"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        projects = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        return projects
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return []


def set_project(project_id: str) -> bool:
    """Set the default GCP project."""
    try:
        subprocess.run(
            ["gcloud", "config", "set", "project", project_id],
            check=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_api_enabled(project_id: str) -> bool:
    """Check if Google Docs API is enabled for the project."""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "services",
                "list",
                "--enabled",
                f"--project={project_id}",
                f"--filter=name:{DOCS_API_SERVICE}",
                "--format=value(name)",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        enabled_services = result.stdout.strip().split("\n")
        return any(DOCS_API_SERVICE in service for service in enabled_services if service)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def enable_docs_api(project_id: str) -> bool:
    """Enable Google Docs API for the project."""
    try:
        subprocess.run(
            [
                "gcloud",
                "services",
                "enable",
                DOCS_API_SERVICE,
                f"--project={project_id}",
            ],
            check=True,
            timeout=60,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_auth_login() -> bool:
    """Run gcloud auth application-default login with required scopes."""
    scopes_str = ",".join(REQUIRED_SCOPES)
    try:
        subprocess.run(
            [
                "gcloud",
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
            ],
            check=True,
            timeout=300,  # 5 minutes timeout for interactive login
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def setup() -> None:
    """
    Set up authentication and configuration for Google Docs Markdown tool.

    This function:
    1. Checks if gcloud CLI is installed
    2. Sets up Application Default Credentials with required scopes
    3. Ensures a default project is set
    4. Enables the Google Docs API for that project

    Skips steps that are already configured correctly.
    """
    typer.echo("🔧 Setting up Google Docs Markdown tool...\n")

    # Step 1: Check if gcloud is installed
    typer.echo("Checking if gcloud CLI is installed...")
    if not check_gcloud_installed():
        typer.echo(
            "❌ gcloud CLI is not installed or not in PATH.\n"
            "Please install the Google Cloud SDK:\n"
            "  https://cloud.google.com/sdk/docs/install\n"
            "Or use: brew install google-cloud-sdk (on macOS)",
            err=True,
        )
        sys.exit(1)
    typer.echo("✅ gcloud CLI is installed\n")

    # Step 2: Check and set up credentials
    typer.echo("Checking Application Default Credentials...")
    if check_credentials_exist():
        typer.echo("✅ Application Default Credentials are already configured\n")
    else:
        typer.echo("Setting up Application Default Credentials...")
        typer.echo("This will open a browser window for authentication...")
        if not run_auth_login():
            typer.echo(
                "❌ Failed to set up Application Default Credentials.\n"
                "Please run manually:\n"
                f"  gcloud auth application-default login --scopes=\"{','.join(REQUIRED_SCOPES)}\"",
                err=True,
            )
            sys.exit(1)
        typer.echo("✅ Application Default Credentials configured\n")

    # Step 3: Check and set default project
    typer.echo("Checking default GCP project...")
    current_project = get_current_project()
    if current_project:
        typer.echo(f"✅ Default project is set to: {current_project}\n")
    else:
        typer.echo("No default project is set.")
        projects = list_available_projects()
        if not projects:
            typer.echo(
                "❌ No projects found. Please create a project first:\n"
                "  https://console.cloud.google.com/projectcreate",
                err=True,
            )
            sys.exit(1)

        typer.echo("\nAvailable projects:")
        for i, project in enumerate(projects, 1):
            typer.echo(f"  {i}. {project}")

        while True:
            try:
                choice = typer.prompt(
                    f"\nSelect a project (1-{len(projects)}) or enter project ID"
                ).strip()
                # Try to parse as number first
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(projects):
                        selected_project = projects[idx]
                        break
                # Otherwise treat as project ID
                elif choice in projects:
                    selected_project = choice
                    break
                else:
                    typer.echo(f"Invalid choice: {choice}. Please try again.", err=True)
            except KeyboardInterrupt:
                typer.echo("\n\nSetup cancelled.", err=True)
                sys.exit(1)

        if not set_project(selected_project):
            typer.echo(
                f"❌ Failed to set project to {selected_project}",
                err=True,
            )
            sys.exit(1)
        typer.echo(f"✅ Default project set to: {selected_project}\n")
        current_project = selected_project

    # Step 4: Enable Google Docs API
    if not current_project:
        typer.echo("❌ No project available to enable API", err=True)
        sys.exit(1)

    typer.echo(f"Checking if Google Docs API is enabled for project '{current_project}'...")
    if check_api_enabled(current_project):
        typer.echo("✅ Google Docs API is already enabled\n")
    else:
        typer.echo(f"Enabling Google Docs API for project '{current_project}'...")
        if not enable_docs_api(current_project):
            typer.echo(
                f"❌ Failed to enable Google Docs API for project '{current_project}'.\n"
                "Please enable manually:\n"
                f"  gcloud services enable {DOCS_API_SERVICE} --project={current_project}",
                err=True,
            )
            sys.exit(1)
        typer.echo("✅ Google Docs API enabled\n")

    typer.echo("🎉 Setup complete! You're ready to use google-docs-markdown.")

