"""
GCloud module for executing gcloud CLI commands.

Provides a unified interface for running gcloud commands with consistent
error handling and messaging.
"""

import subprocess

import typer


class GCloudException(Exception):
    """Exception raised when a gcloud command fails."""

    def __init__(
        self,
        message: str,
        operation: str,
        command: list[str],
        original_error: Exception | None = None,
    ) -> None:
        """Initialize GCloudException.

        Args:
            message: Human-readable error message.
            operation: Description of the operation that failed.
            command: The full gcloud command that was executed.
            original_error: The original exception that caused this error, if any.
        """
        self.message = message
        self.operation = operation
        self.command = command
        self.original_error = original_error
        full_message = f"{message}\nOperation: {operation}\nCommand: {' '.join(command)}"
        super().__init__(full_message)


def gcloud_run(
    command: list[str],
    operation: str,
    timeout: int | None = None,
    raise_exception: bool = True,
) -> str | None:
    """Run a gcloud command and return stdout text or None on error.

    Args:
        command: List of command parts (e.g., ["config", "get-value", "project"]).
                 The "gcloud" prefix will be added automatically.
        operation: Description of the operation being performed, used in error messages.
        timeout: Optional timeout in seconds. Defaults to None (no timeout).
        raise_exception: If True (default), raise GCloudException on error.
                         If False, return None and print error message.

    Returns:
        The stdout text from the command, stripped of leading/trailing whitespace,
        or None if the command failed or gcloud is not installed (only when raise_exception=False).

    Raises:
        GCloudException: If the command fails and raise_exception=True.

    Examples:
        >>> # With exception handling (default)
        >>> try:
        ...     project = gcloud_run(
        ...         ["config", "get-value", "project"],
        ...         operation="getting current default GCP project"
        ...     )
        ... except GCloudException as e:
        ...     print(f"Error: {e}")
        >>> # Without exception handling
        >>> project = gcloud_run(
        ...     ["config", "get-value", "project"],
        ...     operation="getting current default GCP project",
        ...     raise_exception=False
        ... )
        >>> if project:
        ...     print(f"Current project: {project}")
    """
    full_command = ["gcloud"] + command

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        return result.stdout.strip() if result.stdout else None
    except FileNotFoundError as e:
        error_message = (
            f"❌ Error: gcloud CLI not found. Cannot {operation}.\n"
            "Please install the Google Cloud SDK:\n"
            "  https://cloud.google.com/sdk/docs/install\n"
            "Or use: brew install google-cloud-sdk (on macOS)"
        )
        if raise_exception:
            raise GCloudException(
                message=error_message,
                operation=operation,
                command=full_command,
                original_error=e,
            ) from e
        typer.echo(error_message, err=True)
        return None
    except subprocess.CalledProcessError as e:
        error_message = f"❌ Error {operation}: {e}\nCommand: {' '.join(full_command)}"
        if raise_exception:
            raise GCloudException(
                message=error_message,
                operation=operation,
                command=full_command,
                original_error=e,
            ) from e
        typer.echo(error_message, err=True)
        return None
    except subprocess.TimeoutExpired as e:
        error_message = (
            f"❌ Error: gcloud command timed out while {operation}.\n"
            f"Command: {' '.join(full_command)}"
        )
        if raise_exception:
            raise GCloudException(
                message=error_message,
                operation=operation,
                command=full_command,
                original_error=e,
            ) from e
        typer.echo(error_message, err=True)
        return None


def gcloud_exec(
    command: list[str],
    operation: str,
    timeout: int | None = None,
    raise_exception: bool = True,
) -> bool:
    """Execute a gcloud command that doesn't return output.

    Args:
        command: List of command parts (e.g., ["config", "set", "project", "my-project"]).
                 The "gcloud" prefix will be added automatically.
        operation: Description of the operation being performed, used in error messages.
        timeout: Optional timeout in seconds. Defaults to None (no timeout).
        raise_exception: If True (default), raise GCloudException on error.
                         If False, return False and print error message.

    Returns:
        True if the command succeeded, False if the command failed and raise_exception=False.

    Raises:
        GCloudException: If the command fails and raise_exception=True.

    Examples:
        >>> # With exception handling (default)
        >>> try:
        ...     gcloud_exec(
        ...         ["config", "set", "project", "my-project"],
        ...         operation="setting default GCP project"
        ...     )
        ... except GCloudException as e:
        ...     print(f"Failed to set project: {e}")
        >>> # Without exception handling
        >>> success = gcloud_exec(
        ...     ["config", "set", "project", "my-project"],
        ...     operation="setting default GCP project",
        ...     raise_exception=False
        ... )
        >>> if not success:
        ...     print("Failed to set project")
    """
    full_command = ["gcloud"] + command

    try:
        subprocess.run(
            full_command,
            check=True,
            timeout=timeout,
        )
        return True
    except FileNotFoundError as e:
        error_message = (
            f"❌ Error: gcloud CLI not found. Cannot {operation}.\n"
            "Please install the Google Cloud SDK:\n"
            "  https://cloud.google.com/sdk/docs/install\n"
            "Or use: brew install google-cloud-sdk (on macOS)"
        )
        if raise_exception:
            raise GCloudException(
                message=error_message,
                operation=operation,
                command=full_command,
                original_error=e,
            ) from e
        typer.echo(error_message, err=True)
        return False
    except subprocess.CalledProcessError as e:
        error_message = f"❌ Error {operation}: {e}\nCommand: {' '.join(full_command)}"
        if raise_exception:
            raise GCloudException(
                message=error_message,
                operation=operation,
                command=full_command,
                original_error=e,
            ) from e
        typer.echo(error_message, err=True)
        return False
    except subprocess.TimeoutExpired as e:
        error_message = (
            f"❌ Error: gcloud command timed out while {operation}.\n"
            f"Command: {' '.join(full_command)}"
        )
        if raise_exception:
            raise GCloudException(
                message=error_message,
                operation=operation,
                command=full_command,
                original_error=e,
            ) from e
        typer.echo(error_message, err=True)
        return False

