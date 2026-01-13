"""
Tests for CLI module.

Tests that commands exist and are properly configured.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

from pytest import raises

from google_docs_markdown import cli


class TestCLICommands:
    """Test that CLI commands exist and are callable."""

    def test_list_tabs_command_exists(self) -> None:
        """Test that list-tabs command exists and raises NotImplementedError."""
        with raises(NotImplementedError, match="This command is not implemented yet"):
            cli.list_tabs(document_url="test-doc-id")

    def test_upload_command_exists(self) -> None:
        """Test that upload command exists and raises NotImplementedError."""
        with raises(NotImplementedError, match="This command is not implemented yet"):
            cli.upload(document_url="test-doc-id")

    def test_diff_command_exists(self) -> None:
        """Test that diff command exists and raises NotImplementedError."""
        with raises(NotImplementedError, match="This command is not implemented yet"):
            cli.diff(document_url="test-doc-id")

    @patch("google_docs_markdown.setup.setup")
    def test_setup_command_exists(self, mock_setup_module: Mock) -> None:
        """Test that setup command exists and calls the setup module."""
        cli.setup()
        mock_setup_module.assert_called_once()


class TestMain:
    """Test main entry point."""

    @patch("google_docs_markdown.cli.app")
    def test_main_calls_app(self, mock_app: Mock) -> None:
        """Test that main() calls the typer app."""
        cli.main()
        mock_app.assert_called_once()


class TestAppConfiguration:
    """Test that the typer app is properly configured."""

    def test_app_name(self) -> None:
        """Test that app has correct name."""
        assert cli.app.info.name == "google-docs-markdown"

    def test_app_has_commands(self) -> None:
        """Test that app has expected commands registered."""
        # Commands can have explicit names or use callback function names
        command_names = set()
        for cmd in cli.app.registered_commands:
            name = cmd.name if cmd.name else (cmd.callback.__name__ if cmd.callback else None)
            if name:
                command_names.add(name)
        expected_commands = {"download", "list-tabs", "upload", "diff", "setup"}
        assert expected_commands.issubset(command_names)
