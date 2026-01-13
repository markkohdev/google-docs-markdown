"""
Tests for gcloud module.

Tests gcloud command execution, error handling, and exception raising.
"""

from __future__ import annotations

import subprocess
from unittest.mock import Mock, patch

import pytest

from google_docs_markdown.gcloud import GCloudException, gcloud_exec, gcloud_run


class TestGCloudException:
    """Test GCloudException class."""

    def test_exception_initialization(self) -> None:
        """Test exception initialization with all parameters."""
        original_error = FileNotFoundError("gcloud not found")
        exception = GCloudException(
            message="Test error message",
            operation="test operation",
            command=["gcloud", "test", "command"],
            original_error=original_error,
        )

        assert exception.message == "Test error message"
        assert exception.operation == "test operation"
        assert exception.command == ["gcloud", "test", "command"]
        assert exception.original_error == original_error
        assert "Test error message" in str(exception)
        assert "test operation" in str(exception)
        assert "gcloud test command" in str(exception)

    def test_exception_without_original_error(self) -> None:
        """Test exception initialization without original error."""
        exception = GCloudException(
            message="Test error",
            operation="test op",
            command=["gcloud", "cmd"],
        )

        assert exception.message == "Test error"
        assert exception.operation == "test op"
        assert exception.command == ["gcloud", "cmd"]
        assert exception.original_error is None


class TestGcloudRun:
    """Test gcloud_run function."""

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_success_with_output(self, mock_run: Mock) -> None:
        """Test successful execution with output."""
        mock_result = Mock()
        mock_result.stdout = "  my-project-id  \n"
        mock_run.return_value = mock_result

        result = gcloud_run(
            ["config", "get-value", "project"],
            operation="getting project",
        )

        assert result == "my-project-id"
        mock_run.assert_called_once_with(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True,
            timeout=None,
        )

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_success_with_empty_output(self, mock_run: Mock) -> None:
        """Test successful execution with empty output."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = gcloud_run(
            ["config", "get-value", "project"],
            operation="getting project",
        )

        assert result is None

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_success_with_timeout(self, mock_run: Mock) -> None:
        """Test successful execution with timeout parameter."""
        mock_result = Mock()
        mock_result.stdout = "output"
        mock_run.return_value = mock_result

        result = gcloud_run(
            ["projects", "list"],
            operation="listing projects",
            timeout=30,
        )

        assert result == "output"
        mock_run.assert_called_once_with(
            ["gcloud", "projects", "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_file_not_found_with_raise_exception_true(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test FileNotFoundError with raise_exception=True (default)."""
        mock_run.side_effect = FileNotFoundError("gcloud not found")

        with pytest.raises(GCloudException) as exc_info:
            gcloud_run(
                ["config", "get-value", "project"],
                operation="getting project",
            )

        exception = exc_info.value
        assert "gcloud CLI not found" in exception.message
        assert exception.operation == "getting project"
        assert exception.command == ["gcloud", "config", "get-value", "project"]
        assert isinstance(exception.original_error, FileNotFoundError)
        assert exception.original_error.args[0] == "gcloud not found"
        # Should not echo when raising exception
        mock_echo.assert_not_called()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_file_not_found_with_raise_exception_false(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test FileNotFoundError with raise_exception=False."""
        mock_run.side_effect = FileNotFoundError("gcloud not found")

        result = gcloud_run(
            ["config", "get-value", "project"],
            operation="getting project",
            raise_exception=False,
        )

        assert result is None
        mock_echo.assert_called_once()
        error_call = mock_echo.call_args
        assert error_call.kwargs.get("err") is True
        assert "gcloud CLI not found" in error_call.args[0]

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_called_process_error_with_raise_exception_true(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test CalledProcessError with raise_exception=True (default)."""
        error = subprocess.CalledProcessError(returncode=1, cmd=["gcloud", "config", "get-value", "project"])
        mock_run.side_effect = error

        with pytest.raises(GCloudException) as exc_info:
            gcloud_run(
                ["config", "get-value", "project"],
                operation="getting project",
            )

        exception = exc_info.value
        assert "getting project" in exception.message
        assert exception.operation == "getting project"
        assert exception.command == ["gcloud", "config", "get-value", "project"]
        assert exception.original_error == error
        # Should not echo when raising exception
        mock_echo.assert_not_called()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_called_process_error_with_raise_exception_false(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test CalledProcessError with raise_exception=False."""
        error = subprocess.CalledProcessError(returncode=1, cmd=["gcloud", "config", "get-value", "project"])
        mock_run.side_effect = error

        result = gcloud_run(
            ["config", "get-value", "project"],
            operation="getting project",
            raise_exception=False,
        )

        assert result is None
        mock_echo.assert_called_once()
        error_call = mock_echo.call_args
        assert error_call.kwargs.get("err") is True
        assert "getting project" in error_call.args[0]

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_timeout_expired_with_raise_exception_true(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test TimeoutExpired with raise_exception=True (default)."""
        error = subprocess.TimeoutExpired(cmd=["gcloud", "projects", "list"], timeout=30)
        mock_run.side_effect = error

        with pytest.raises(GCloudException) as exc_info:
            gcloud_run(
                ["projects", "list"],
                operation="listing projects",
                timeout=30,
            )

        exception = exc_info.value
        assert "timed out" in exception.message.lower()
        assert exception.operation == "listing projects"
        assert exception.command == ["gcloud", "projects", "list"]
        assert exception.original_error == error
        # Should not echo when raising exception
        mock_echo.assert_not_called()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_timeout_expired_with_raise_exception_false(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test TimeoutExpired with raise_exception=False."""
        error = subprocess.TimeoutExpired(cmd=["gcloud", "projects", "list"], timeout=30)
        mock_run.side_effect = error

        result = gcloud_run(
            ["projects", "list"],
            operation="listing projects",
            timeout=30,
            raise_exception=False,
        )

        assert result is None
        mock_echo.assert_called_once()
        error_call = mock_echo.call_args
        assert error_call.kwargs.get("err") is True
        assert "timed out" in error_call.args[0].lower()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_command_construction(self, mock_run: Mock) -> None:
        """Test that gcloud prefix is added to command."""
        mock_result = Mock()
        mock_result.stdout = "output"
        mock_run.return_value = mock_result

        gcloud_run(["config", "get-value", "project"], operation="test")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["gcloud", "config", "get-value", "project"]


class TestGcloudExec:
    """Test gcloud_exec function."""

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_success(self, mock_run: Mock) -> None:
        """Test successful execution."""
        mock_run.return_value = Mock(returncode=0)

        result = gcloud_exec(
            ["config", "set", "project", "my-project"],
            operation="setting project",
        )

        assert result is True
        mock_run.assert_called_once_with(
            ["gcloud", "config", "set", "project", "my-project"],
            check=True,
            timeout=None,
        )

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_success_with_timeout(self, mock_run: Mock) -> None:
        """Test successful execution with timeout parameter."""
        mock_run.return_value = Mock(returncode=0)

        result = gcloud_exec(
            ["services", "enable", "docs.googleapis.com"],
            operation="enabling API",
            timeout=60,
        )

        assert result is True
        mock_run.assert_called_once_with(
            ["gcloud", "services", "enable", "docs.googleapis.com"],
            check=True,
            timeout=60,
        )

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_file_not_found_with_raise_exception_true(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test FileNotFoundError with raise_exception=True (default)."""
        mock_run.side_effect = FileNotFoundError("gcloud not found")

        with pytest.raises(GCloudException) as exc_info:
            gcloud_exec(
                ["config", "set", "project", "my-project"],
                operation="setting project",
            )

        exception = exc_info.value
        assert "gcloud CLI not found" in exception.message
        assert exception.operation == "setting project"
        assert exception.command == ["gcloud", "config", "set", "project", "my-project"]
        assert isinstance(exception.original_error, FileNotFoundError)
        # Should not echo when raising exception
        mock_echo.assert_not_called()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_file_not_found_with_raise_exception_false(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test FileNotFoundError with raise_exception=False."""
        mock_run.side_effect = FileNotFoundError("gcloud not found")

        result = gcloud_exec(
            ["config", "set", "project", "my-project"],
            operation="setting project",
            raise_exception=False,
        )

        assert result is False
        mock_echo.assert_called_once()
        error_call = mock_echo.call_args
        assert error_call.kwargs.get("err") is True
        assert "gcloud CLI not found" in error_call.args[0]

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_called_process_error_with_raise_exception_true(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test CalledProcessError with raise_exception=True (default)."""
        error = subprocess.CalledProcessError(returncode=1, cmd=["gcloud", "config", "set", "project", "my-project"])
        mock_run.side_effect = error

        with pytest.raises(GCloudException) as exc_info:
            gcloud_exec(
                ["config", "set", "project", "my-project"],
                operation="setting project",
            )

        exception = exc_info.value
        assert "setting project" in exception.message
        assert exception.operation == "setting project"
        assert exception.command == ["gcloud", "config", "set", "project", "my-project"]
        assert exception.original_error == error
        # Should not echo when raising exception
        mock_echo.assert_not_called()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_called_process_error_with_raise_exception_false(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test CalledProcessError with raise_exception=False."""
        error = subprocess.CalledProcessError(returncode=1, cmd=["gcloud", "config", "set", "project", "my-project"])
        mock_run.side_effect = error

        result = gcloud_exec(
            ["config", "set", "project", "my-project"],
            operation="setting project",
            raise_exception=False,
        )

        assert result is False
        mock_echo.assert_called_once()
        error_call = mock_echo.call_args
        assert error_call.kwargs.get("err") is True
        assert "setting project" in error_call.args[0]

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_timeout_expired_with_raise_exception_true(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test TimeoutExpired with raise_exception=True (default)."""
        error = subprocess.TimeoutExpired(cmd=["gcloud", "services", "enable", "docs.googleapis.com"], timeout=60)
        mock_run.side_effect = error

        with pytest.raises(GCloudException) as exc_info:
            gcloud_exec(
                ["services", "enable", "docs.googleapis.com"],
                operation="enabling API",
                timeout=60,
            )

        exception = exc_info.value
        assert "timed out" in exception.message.lower()
        assert exception.operation == "enabling API"
        assert exception.command == [
            "gcloud",
            "services",
            "enable",
            "docs.googleapis.com",
        ]
        assert exception.original_error == error
        # Should not echo when raising exception
        mock_echo.assert_not_called()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    @patch("google_docs_markdown.gcloud.typer.echo")
    def test_timeout_expired_with_raise_exception_false(self, mock_echo: Mock, mock_run: Mock) -> None:
        """Test TimeoutExpired with raise_exception=False."""
        error = subprocess.TimeoutExpired(cmd=["gcloud", "services", "enable", "docs.googleapis.com"], timeout=60)
        mock_run.side_effect = error

        result = gcloud_exec(
            ["services", "enable", "docs.googleapis.com"],
            operation="enabling API",
            timeout=60,
            raise_exception=False,
        )

        assert result is False
        mock_echo.assert_called_once()
        error_call = mock_echo.call_args
        assert error_call.kwargs.get("err") is True
        assert "timed out" in error_call.args[0].lower()

    @patch("google_docs_markdown.gcloud.subprocess.run")
    def test_command_construction(self, mock_run: Mock) -> None:
        """Test that gcloud prefix is added to command."""
        mock_run.return_value = Mock(returncode=0)

        gcloud_exec(["config", "set", "project", "my-project"], operation="test")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["gcloud", "config", "set", "project", "my-project"]
