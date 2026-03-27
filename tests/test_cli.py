"""
Tests for CLI module.

Tests that commands exist and are properly configured.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import ANY, Mock, patch

import typer
from pytest import raises

from google_docs_markdown import cli
from google_docs_markdown.downloader import FileConflictError, TabSummary


class TestCLICommands:
    """Test that CLI commands exist and are callable."""

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
            overwrite=False,
            _prefetched=ANY,
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
            overwrite=False,
            _prefetched=ANY,
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
            overwrite=False,
            _prefetched=ANY,
        )

    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_force_passes_overwrite(self, mock_dl_cls: Mock) -> None:
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": Path("/out/Tab.md")}

        cli.download(document_url="doc-id", output="/out", tabs=None, force=True)

        mock_dl.download_to_files.assert_called_once_with(
            "doc-id",
            output_dir="/out",
            tab_names=None,
            overwrite=True,
            _prefetched=ANY,
        )

    @patch("typer.confirm", return_value=True)
    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_conflict_confirm_overwrites(self, mock_dl_cls: Mock, mock_confirm: Mock) -> None:
        mock_dl = mock_dl_cls.return_value
        conflict = FileConflictError([Path("/out/Tab.md")])
        mock_dl.download_to_files.side_effect = [conflict, {"Tab": Path("/out/Tab.md")}]

        cli.download(document_url="doc-id", output="/out", tabs=None)

        assert mock_dl.download_to_files.call_count == 2
        second_call = mock_dl.download_to_files.call_args_list[1]
        assert second_call.kwargs["overwrite"] is True
        mock_confirm.assert_called_once()

    @patch("typer.confirm", return_value=False)
    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_conflict_decline_aborts(self, mock_dl_cls: Mock, mock_confirm: Mock) -> None:
        mock_dl = mock_dl_cls.return_value
        conflict = FileConflictError([Path("/out/Tab.md")])
        mock_dl.download_to_files.side_effect = conflict

        with raises((SystemExit, typer.Abort)):
            cli.download(document_url="doc-id", output="/out", tabs=None)

        mock_dl.download_to_files.assert_called_once()

    @patch("google_docs_markdown.downloader.Downloader")
    def test_download_error_handling(self, mock_dl_cls: Mock) -> None:
        import click

        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.side_effect = RuntimeError("API error")

        with raises((SystemExit, click.exceptions.Exit)):
            cli.download(document_url="doc-id", output="/out", tabs=None)


class TestStaleFileCleanup:
    """Test the stale file detection and cleanup prompt."""

    def _setup_stale(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create a doc dir with one current and one stale .md file."""
        doc_dir = tmp_path / "Doc"
        doc_dir.mkdir()
        stale = doc_dir / "Old Tab.md"
        stale.write_text("stale content")
        current = doc_dir / "Tab.md"
        current.write_text("current content")
        return current, stale

    @patch("google_docs_markdown.downloader.Downloader")
    def test_force_deletes_stale_without_prompt(self, mock_dl_cls: Mock, tmp_path: Path) -> None:
        current, stale = self._setup_stale(tmp_path)
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": current}

        cli.download(document_url="doc-id", output=str(tmp_path), tabs=None, force=True)

        assert not stale.exists()
        assert current.exists()

    @patch("typer.confirm", return_value=True)
    @patch("google_docs_markdown.downloader.Downloader")
    def test_stale_files_deleted_when_confirmed(self, mock_dl_cls: Mock, mock_confirm: Mock, tmp_path: Path) -> None:
        current, stale = self._setup_stale(tmp_path)
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": current}

        cli.download(document_url="doc-id", output=str(tmp_path), tabs=None)

        assert not stale.exists()
        assert current.exists()
        mock_confirm.assert_called()

    @patch("typer.confirm", return_value=False)
    @patch("google_docs_markdown.downloader.Downloader")
    def test_stale_files_kept_when_declined(self, mock_dl_cls: Mock, mock_confirm: Mock, tmp_path: Path) -> None:
        current, stale = self._setup_stale(tmp_path)
        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": current}

        cli.download(document_url="doc-id", output=str(tmp_path), tabs=None)

        assert stale.exists()

    @patch("google_docs_markdown.downloader.Downloader")
    def test_no_prompt_when_no_stale_files(self, mock_dl_cls: Mock, tmp_path: Path) -> None:
        doc_dir = tmp_path / "Doc"
        doc_dir.mkdir()
        current = doc_dir / "Tab.md"
        current.write_text("content")

        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": current}

        cli.download(document_url="doc-id", output=str(tmp_path), tabs=None, force=True)

    @patch("google_docs_markdown.downloader.Downloader")
    def test_empty_dirs_cleaned_after_force_deletion(self, mock_dl_cls: Mock, tmp_path: Path) -> None:
        doc_dir = tmp_path / "Doc"
        doc_dir.mkdir()
        nested = doc_dir / "Removed Tab"
        nested.mkdir()
        stale = nested / "Child.md"
        stale.write_text("stale")
        current = doc_dir / "Tab.md"
        current.write_text("current")

        mock_dl = mock_dl_cls.return_value
        mock_dl.download_to_files.return_value = {"Tab": current}

        cli.download(document_url="doc-id", output=str(tmp_path), tabs=None, force=True)

        assert not stale.exists()
        assert not nested.exists()


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


class TestUploadCommand:
    """Test the upload command wiring."""

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_create_from_file(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.create_from_markdown.return_value = "new-doc-id"

        cli.upload(
            document_url=None,
            local_path=str(md_file),
            create=True,
        )

        mock_ul.create_from_markdown.assert_called_once_with("test", "# Hello\n")

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_create_from_directory(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_dir = tmp_path / "My Doc"
        md_dir.mkdir()
        (md_dir / "Tab.md").write_text("text\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.create_from_directory.return_value = "new-doc-id"

        cli.upload(
            document_url=None,
            local_path=str(md_dir),
            create=True,
        )

        mock_ul.create_from_directory.assert_called_once()

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_create_with_title(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_file = tmp_path / "data.md"
        md_file.write_text("content\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.create_from_markdown.return_value = "new-doc-id"

        cli.upload(
            document_url=None,
            local_path=str(md_file),
            create=True,
            title="Custom Title",
        )

        mock_ul.create_from_markdown.assert_called_once_with("Custom Title", "content\n")

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_update_file(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_file = tmp_path / "doc.md"
        md_file.write_text("updated\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.update_document.return_value = True

        cli.upload(
            document_url="doc-id-1234567890",
            local_path=str(md_file),
        )

        mock_ul.update_document.assert_called_once_with(
            "doc-id-1234567890",
            "updated\n",
            tab_id=None,
        )

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_update_directory(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_dir = tmp_path / "Doc"
        md_dir.mkdir()
        (md_dir / "Tab.md").write_text("text\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.update_from_directory.return_value = {"Tab": True}

        cli.upload(
            document_url="doc-id-1234567890",
            local_path=str(md_dir),
        )

        mock_ul.update_from_directory.assert_called_once_with("doc-id-1234567890", Path(str(md_dir)))

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_update_with_tab_id(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_file = tmp_path / "doc.md"
        md_file.write_text("changed\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.update_document.return_value = True

        cli.upload(
            document_url="doc-id-1234567890",
            local_path=str(md_file),
            tab="t.42",
        )

        mock_ul.update_document.assert_called_once_with(
            "doc-id-1234567890",
            "changed\n",
            tab_id="t.42",
        )

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_no_changes_detected(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        md_file = tmp_path / "doc.md"
        md_file.write_text("same\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.update_document.return_value = False

        cli.upload(
            document_url="doc-id-1234567890",
            local_path=str(md_file),
        )

        mock_ul.update_document.assert_called_once()

    def test_upload_create_nonexistent_path(self) -> None:
        import click

        with raises((SystemExit, click.exceptions.Exit)):
            cli.upload(
                document_url=None,
                local_path="/nonexistent/file.md",
                create=True,
            )

    @patch("google_docs_markdown.uploader.Uploader")
    def test_upload_update_error_handling(self, mock_ul_cls: Mock, tmp_path: Path) -> None:
        import click

        md_file = tmp_path / "doc.md"
        md_file.write_text("text\n", encoding="utf-8")

        mock_ul = mock_ul_cls.return_value
        mock_ul.update_document.side_effect = RuntimeError("API error")

        with raises((SystemExit, click.exceptions.Exit)):
            cli.upload(
                document_url="doc-id-1234567890",
                local_path=str(md_file),
            )


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
