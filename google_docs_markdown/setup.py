"""
Setup module for Google Docs Markdown tool.

Handles authentication, project configuration, and API enablement.
"""

import sys
from pathlib import Path

import typer
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

from google_docs_markdown.gcloud import GCloudException, gcloud_exec, gcloud_run

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
    result = gcloud_run(["--version"], operation="checking gcloud installation", timeout=10)
    return result is not None


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
    current_project = gcloud_run(
        ["config", "get-value", "project"],
        operation="getting current default GCP project",
        timeout=10,
    )
    return current_project if current_project else None


def list_available_projects() -> list[str]:
    """List available GCP projects."""
    output = gcloud_run(
        ["projects", "list", "--format=value(projectId)"],
        operation="listing available GCP projects",
        timeout=30,
    )
    if output is None:
        return []
    projects = [p.strip() for p in output.split("\n") if p.strip()]
    return projects


def set_project(project_id: str) -> bool:
    """Set the default GCP project."""
    return gcloud_exec(
        ["config", "set", "project", project_id],
        operation=f"setting default GCP project to '{project_id}'",
        timeout=10,
    )


def check_api_enabled(project_id: str) -> bool:
    """Check if Google Docs API is enabled for the project."""
    output = gcloud_run(
        [
            "services",
            "list",
            "--enabled",
            f"--project={project_id}",
            f"--filter=name:{DOCS_API_SERVICE}",
            "--format=value(name)",
        ],
        operation=f"checking if Google Docs API is enabled for project '{project_id}'",
        timeout=30,
    )
    if output is None:
        return False
    enabled_services = output.split("\n")
    return any(DOCS_API_SERVICE in service for service in enabled_services if service)


def enable_docs_api(project_id: str) -> bool:
    """Enable Google Docs API for the project."""
    return gcloud_exec(
        [
            "services",
            "enable",
            DOCS_API_SERVICE,
            f"--project={project_id}",
        ],
        operation=f"enabling Google Docs API for project '{project_id}'",
        timeout=60,
    )


def revoke_credentials() -> bool:
    """Revoke existing Application Default Credentials."""
    return gcloud_exec(
        ["auth", "application-default", "revoke"],
        operation="revoking Application Default Credentials",
        timeout=30,
    )


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
        "auth",
        "application-default",
        "login",
        f"--scopes={scopes_str}",
    ]

    if client_id_file:
        cmd.append(f"--client-id-file={client_id_file}")

    return gcloud_exec(
        cmd,
        operation="running authentication",
        timeout=300,  # 5 minutes timeout for interactive login
    )


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
        try:
            gcloud_exec(
                ["auth", "application-default", "revoke"],
                operation="revoking Application Default Credentials",
                timeout=30,
            )
            typer.echo("✅ Application Default Credentials revoked\n")
        except GCloudException as e:
            typer.echo(
                f"⚠️  Warning: Failed to revoke credentials: {e.message}\n"
                "Continuing with setup...\n",
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
        try:
            scopes = REQUIRED_SCOPES.copy()
            if extra_scopes:
                additional = [s.strip() for s in extra_scopes.split(",") if s.strip()]
                scopes.extend(additional)
            scopes_str = ",".join(scopes)
            cmd = [
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
            ]
            if client_id_file:
                cmd.append(f"--client-id-file={client_id_file}")
            gcloud_exec(
                cmd,
                operation="running authentication",
                timeout=300,  # 5 minutes timeout for interactive login
            )
            typer.echo("✅ Application Default Credentials configured\n")
        except GCloudException as e:
            scopes = REQUIRED_SCOPES.copy()
            if extra_scopes:
                additional = [s.strip() for s in extra_scopes.split(",") if s.strip()]
                scopes.extend(additional)
            typer.echo(
                f"❌ Failed to set up Application Default Credentials: {e.message}\n"
                "Please run manually:\n"
                f'  gcloud auth application-default login --scopes="{",".join(scopes)}"',
                err=True,
            )
            sys.exit(1)

    # Step 3: Check and set default project
    typer.echo("Checking default GCP project...")
    current_project = get_current_project()
    if current_project:
        typer.echo(f"✅ Default project is set to: {current_project}\n")
    else:
        typer.echo("No default project is set.")
        try:
            output = gcloud_run(
                ["projects", "list", "--format=value(projectId)"],
                operation="listing available GCP projects",
                timeout=30,
            )
            if output is None:
                projects = []
            else:
                projects = [p.strip() for p in output.split("\n") if p.strip()]
        except GCloudException as e:
            typer.echo(
                f"❌ Failed to list projects: {e.message}\n"
                "Make sure you're authenticated and have permission to list projects.\n"
                "Try running: gcloud auth login",
                err=True,
            )
            sys.exit(1)

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

        try:
            gcloud_exec(
                ["config", "set", "project", selected_project],
                operation=f"setting default GCP project to '{selected_project}'",
                timeout=10,
            )
            typer.echo(f"✅ Default project set to: {selected_project}\n")
            current_project = selected_project
        except GCloudException as e:
            typer.echo(
                f"❌ Failed to set project to {selected_project}: {e.message}\n"
                f"Make sure the project ID '{selected_project}' is valid and you have access to it.\n"
                "Try running: gcloud projects list",
                err=True,
            )
            sys.exit(1)

    # Step 4: Enable Google Docs API
    if not current_project:
        typer.echo("❌ No project available to enable API", err=True)
        sys.exit(1)

    typer.echo(f"Checking if Google Docs API is enabled for project '{current_project}'...")
    try:
        output = gcloud_run(
            [
                "services",
                "list",
                "--enabled",
                f"--project={current_project}",
                f"--filter=name:{DOCS_API_SERVICE}",
                "--format=value(name)",
            ],
            operation=f"checking if Google Docs API is enabled for project '{current_project}'",
            timeout=30,
        )
        api_enabled = False
        if output:
            enabled_services = output.split("\n")
            api_enabled = any(DOCS_API_SERVICE in service for service in enabled_services if service)
    except GCloudException as e:
        typer.echo(
            f"⚠️  Warning: Failed to check if API is enabled: {e.message}\n"
            "This may be normal if you don't have permission to list services.\n"
            "Continuing with API enablement...",
            err=True,
        )
        api_enabled = False

    if api_enabled:
        typer.echo("✅ Google Docs API is already enabled\n")
    else:
        typer.echo(f"Enabling Google Docs API for project '{current_project}'...")
        try:
            gcloud_exec(
                [
                    "services",
                    "enable",
                    DOCS_API_SERVICE,
                    f"--project={current_project}",
                ],
                operation=f"enabling Google Docs API for project '{current_project}'",
                timeout=60,
            )
            typer.echo("✅ Google Docs API enabled\n")
        except GCloudException as e:
            typer.echo(
                f"❌ Failed to enable Google Docs API for project '{current_project}': {e.message}\n"
                "Make sure you have the 'Service Usage Admin' role or equivalent permissions.\n"
                f"Try running manually: gcloud services enable {DOCS_API_SERVICE} --project={current_project}",
                err=True,
            )
            sys.exit(1)

    typer.echo("🎉 Setup complete! You're ready to use google-docs-markdown.")
