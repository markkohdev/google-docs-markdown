"""
Tests for CLI module.

Tests that commands exist and are properly configured.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from pytest import raises

from google_docs_markdown import cli
from google_docs_markdown.downloader import TabSummary


class TestCLICommands:
    """Test that CLI commands exist and are callable."""

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


class TestDownloadCommand:
    """Test the download command wiring."""

    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_calls_downloader(self, mock_dl_cls: Mock) -> None:
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab 1": Path("/out/Tab 1.md")}

        cli.download(document_url="doc-id", output="/out", tabs=None)

        mock_dl.download_to_files.assert_called_once_with(
            "doc-id",
            output_dir="/out",
            tab_names=None,
        )

    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_passes_tab_filter(self, mock_dl_cls: Mock) -> None:
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab A": Path("/out/Tab A.md")}

        cli.download(document_url="doc-id", output="/out", tabs=["Tab A"])

        mock_dl.download_to_files.assert_called_once_with(
            "doc-id",
            output_dir="/out",
            tab_names=["Tab A"],
        )

    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_no_output_dir(self, mock_dl_cls: Mock) -> None:
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": Path("Doc/Tab.md")}

        cli.download(document_url="doc-id", output=None, tabs=None)

        mock_dl.download_to_files.assert_called_once_with(
            "doc-id",
            output_dir=None,
            tab_names=None,
        )

    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_error_handling(self, mock_dl_cls: Mock) -> None:
        import click

        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.side_effect = RuntimeError("API error")

        with raises((SystemExit, click.exceptions.Exit)):
            cli.download(document_url="doc-id", output="/out", tabs=None)


class TestListTabsCommand:
    """Test the list-tabs command wiring."""

    @patch("google_docs_markdown.downloader.Downloader")
    def test_list_tabs_calls_downloader(self, mock_dl_cls: Mock, capsys: object) -> None:
        mock_dl = mock_dl_cls.return_value
        mock_dl.get_tabs.return_value = [
            TabSummary(tab_id="t.0", title="First tab", nesting_level=0, parent_tab_id=None, child_tabs=[]),
        ]
        mock_dl.get_document_title.return_value = "My Doc"

        cli.list_tabs(document_url="doc-id")

        mock_dl.get_tabs.assert_called_once_with("doc-id")

    @patch("google_docs_markdown.downloader.Downloader")
    def test_list_tabs_nested(self, mock_dl_cls: Mock, capsys: object) -> None:
        mock_dl = mock_dl_cls.return_value
        mock_dl.get_tabs.return_value = [
            TabSummary(
                tab_id="t.1",
                title="Parent",
                nesting_level=0,
                parent_tab_id=None,
                child_tabs=[
                    TabSummary(tab_id="t.2", title="Child", nesting_level=1, parent_tab_id="t.1", child_tabs=[]),
                ],
            ),
        ]
        mock_dl.get_document_title.return_value = "My Doc"

        cli.list_tabs(document_url="doc-id")
        mock_dl.get_tabs.assert_called_once_with("doc-id")

    @patch("google_docs_markdown.downloader.Downloader")
    def test_list_tabs_error_handling(self, mock_dl_cls: Mock) -> None:
        import click

        mock_dl = mock_dl_cls.return_value
        mock_dl.get_tabs.side_effect = RuntimeError("API error")

        with raises((SystemExit, click.exceptions.Exit)):
            cli.list_tabs(document_url="doc-id")


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
        command_names = set()
        for cmd in cli.app.registered_commands:
            name = cmd.name if cmd.name else (cmd.callback.__name__ if cmd.callback else None)
            if name:
                command_names.add(name)
        expected_commands = {"download", "list-tabs", "upload", "diff", "setup"}
        assert expected_commands.issubset(command_names)
