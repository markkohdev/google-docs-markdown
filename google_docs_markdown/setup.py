"""
Setup module for Google Docs Markdown tool.

Handles authentication, project configuration, and API enablement.
"""

import subprocess
import sys
from pathlib import Path

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
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"❌ Error running gcloud command: {e}\ngcloud CLI may be installed but not working correctly.",
            err=True,
        )
        return False
    except subprocess.TimeoutExpired:
        typer.echo(
            "❌ gcloud command timed out. Please check your system.",
            err=True,
        )
        return False


def check_credentials_exist() -> bool:
    """Check if Application Default Credentials are already configured."""
    try:
        credentials, _ = default(scopes=REQUIRED_SCOPES)
        # If we can get credentials with the required scopes, they're configured
        return credentials is not None
    except DefaultCredentialsError:
        return False
    except Exception as e:
        typer.echo(
            f"⚠️  Warning: Error checking credentials: {e}\n"
            "Credentials may exist but may not be valid for the required scopes.",
            err=True,
        )
        return False


def get_current_project() -> str | None:
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
    except FileNotFoundError:
        typer.echo(
            "⚠️  Warning: gcloud CLI not found. Cannot get current project.",
            err=True,
        )
        return None
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"⚠️  Warning: Failed to get current project: {e}\nThis may be normal if no default project is set.",
            err=True,
        )
        return None
    except subprocess.TimeoutExpired:
        typer.echo(
            "⚠️  Warning: gcloud command timed out while getting current project.",
            err=True,
        )
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
    except FileNotFoundError:
        typer.echo(
            "❌ Error: gcloud CLI not found. Cannot list projects.",
            err=True,
        )
        return []
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"❌ Error listing projects: {e}\n"
            "Make sure you're authenticated and have permission to list projects.\n"
            "Try running: gcloud auth login",
            err=True,
        )
        return []
    except subprocess.TimeoutExpired:
        typer.echo(
            "❌ Error: gcloud command timed out while listing projects.\n"
            "This may indicate network issues or authentication problems.",
            err=True,
        )
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
    except FileNotFoundError:
        typer.echo(
            "❌ Error: gcloud CLI not found. Cannot set project.",
            err=True,
        )
        return False
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"❌ Error setting project '{project_id}': {e}\n"
            f"Make sure the project ID '{project_id}' is valid and you have access to it.\n"
            "Try running: gcloud projects list",
            err=True,
        )
        return False
    except subprocess.TimeoutExpired:
        typer.echo(
            f"❌ Error: gcloud command timed out while setting project '{project_id}'.",
            err=True,
        )
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
    except FileNotFoundError:
        typer.echo(
            "❌ Error: gcloud CLI not found. Cannot check API status.",
            err=True,
        )
        return False
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"⚠️  Warning: Failed to check if API is enabled for project '{project_id}': {e}\n"
            "This may be normal if you don't have permission to list services.",
            err=True,
        )
        return False
    except subprocess.TimeoutExpired:
        typer.echo(
            f"⚠️  Warning: gcloud command timed out while checking API status for project '{project_id}'.",
            err=True,
        )
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
    except FileNotFoundError:
        typer.echo(
            "❌ Error: gcloud CLI not found. Cannot enable API.",
            err=True,
        )
        return False
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"❌ Error enabling Google Docs API for project '{project_id}': {e}\n"
            "Make sure you have the 'Service Usage Admin' role or equivalent permissions.\n"
            f"Try running manually: gcloud services enable {DOCS_API_SERVICE} --project={project_id}",
            err=True,
        )
        return False
    except subprocess.TimeoutExpired:
        typer.echo(
            f"❌ Error: gcloud command timed out while enabling API for project '{project_id}'.\n"
            "This may indicate network issues. The API may still be enabling in the background.",
            err=True,
        )
        return False


def revoke_credentials() -> bool:
    """Revoke existing Application Default Credentials."""
    try:
        subprocess.run(
            [
                "gcloud",
                "auth",
                "application-default",
                "revoke",
            ],
            check=True,
            timeout=30,
        )
        return True
    except FileNotFoundError:
        typer.echo(
            "❌ Error: gcloud CLI not found. Cannot revoke credentials.",
            err=True,
        )
        return False
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"❌ Error revoking credentials: {e}\n"
            "Credentials may not exist or revocation failed.\n"
            "Try running manually: gcloud auth application-default revoke",
            err=True,
        )
        return False
    except subprocess.TimeoutExpired:
        typer.echo(
            "❌ Error: Revoke command timed out.",
            err=True,
        )
        return False


def run_auth_login(extra_scopes: str = "", client_id_file: str | None = None) -> bool:
    """Run gcloud auth application-default login with required scopes.

    Args:
        extra_scopes: Additional comma-separated scopes to append to REQUIRED_SCOPES.
        client_id_file: Path to client ID file for OAuth authentication.
    """
    scopes = REQUIRED_SCOPES.copy()
    if extra_scopes:
        # Split by comma, strip whitespace, and add non-empty scopes
        additional = [s.strip() for s in extra_scopes.split(",") if s.strip()]
        scopes.extend(additional)

    scopes_str = ",".join(scopes)

    cmd = [
        "gcloud",
        "auth",
        "application-default",
        "login",
        f"--scopes={scopes_str}",
    ]

    if client_id_file:
        cmd.append(f"--client-id-file={client_id_file}")

    try:
        subprocess.run(
            cmd,
            check=True,
            timeout=300,  # 5 minutes timeout for interactive login
        )
        return True
    except FileNotFoundError:
        typer.echo(
            "❌ Error: gcloud CLI not found. Cannot run authentication.",
            err=True,
        )
        return False
    except subprocess.CalledProcessError as e:
        cmd_str = f"gcloud auth application-default login --scopes={scopes_str}"
        if client_id_file:
            cmd_str += f" --client-id-file={client_id_file}"
        typer.echo(
            f"❌ Error during authentication: {e}\n"
            "Authentication may have been cancelled or failed.\n"
            f"Try running manually: {cmd_str}",
            err=True,
        )
        return False
    except subprocess.TimeoutExpired:
        typer.echo(
            "❌ Error: Authentication timed out after 5 minutes.\nPlease try again or run the authentication manually.",
            err=True,
        )
        return False


def setup(revoke: bool = False, extra_scopes: str = "", client_id_file: str | None = None) -> None:
    """
    Set up authentication and configuration for Google Docs Markdown tool.

    This function:
    1. Checks if gcloud CLI is installed
    2. Sets up Application Default Credentials with required scopes
    3. Ensures a default project is set
    4. Enables the Google Docs API for that project

    Skips steps that are already configured correctly.

    Args:
        revoke: If True, revoke existing Application Default Credentials before setting up new ones.
        extra_scopes: Additional comma-separated scopes to append to REQUIRED_SCOPES.
        client_id_file: Path to client ID file for OAuth authentication. If not provided,
                       checks for file at ~/.config/google-docs-markdown/client_id_file.json.
    """
    # Check for client ID file at default location if not provided
    if not client_id_file:
        default_client_id_path = Path.home() / ".config" / "google-docs-markdown" / "client_id_file.json"
        if default_client_id_path.exists():
            client_id_file = str(default_client_id_path)
            typer.echo(f"📄 Found client ID file at: {client_id_file}\n")
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

    # Revoke existing credentials if requested
    if revoke:
        typer.echo("Revoking existing Application Default Credentials...")
        if revoke_credentials():
            typer.echo("✅ Application Default Credentials revoked\n")
        else:
            typer.echo(
                "⚠️  Warning: Failed to revoke credentials. Continuing with setup...\n",
                err=True,
            )

    if check_credentials_exist() and not revoke:
        typer.echo("✅ Application Default Credentials are already configured\n")
    else:
        typer.echo("Setting up Application Default Credentials...")
        if extra_scopes:
            typer.echo(f"Including additional scopes: {extra_scopes}")
        if client_id_file:
            typer.echo(f"Using client ID file: {client_id_file}")
        typer.echo("This will open a browser window for authentication...")
        if not run_auth_login(extra_scopes, client_id_file):
            scopes = REQUIRED_SCOPES.copy()
            if extra_scopes:
                additional = [s.strip() for s in extra_scopes.split(",") if s.strip()]
                scopes.extend(additional)
            typer.echo(
                "❌ Failed to set up Application Default Credentials.\n"
                "Please run manually:\n"
                f'  gcloud auth application-default login --scopes="{",".join(scopes)}"',
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
                choice = typer.prompt(f"\nSelect a project (1-{len(projects)}) or enter project ID").strip()
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
