"""
Tests for setup module.

Tests authentication checks, project configuration, and API enablement.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

from google.auth.exceptions import DefaultCredentialsError

from google_docs_markdown.setup import (
    DOCS_API_SERVICE,
    REQUIRED_SCOPES,
    check_api_enabled,
    check_credentials_exist,
    check_gcloud_installed,
    enable_docs_api,
    get_current_project,
    list_available_projects,
    revoke_credentials,
    run_auth_login,
    set_project,
    setup,
)


class TestCheckGcloudInstalled:
    """Test gcloud installation check."""

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_gcloud_installed(self, mock_gcloud_run: Mock) -> None:
        """Test when gcloud is installed."""
        mock_gcloud_run.return_value = "gcloud version output"
        assert check_gcloud_installed() is True
        mock_gcloud_run.assert_called_once_with(
            ["--version"],
            operation="checking gcloud installation",
            timeout=10,
        )

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_gcloud_not_installed(self, mock_gcloud_run: Mock) -> None:
        """Test when gcloud is not found."""
        mock_gcloud_run.return_value = None
        assert check_gcloud_installed() is False


class TestCheckCredentialsExist:
    """Test credential existence check."""

    @patch("google_docs_markdown.setup.default")
    def test_credentials_exist(self, mock_default: Mock) -> None:
        """Test when credentials exist."""
        mock_creds = Mock()
        mock_default.return_value = (mock_creds, None)
        assert check_credentials_exist() is True
        mock_default.assert_called_once_with(scopes=REQUIRED_SCOPES)

    @patch("google_docs_markdown.setup.default")
    def test_credentials_not_exist(self, mock_default: Mock) -> None:
        """Test when credentials don't exist."""
        mock_default.side_effect = DefaultCredentialsError("No credentials")
        assert check_credentials_exist() is False

    @patch("google_docs_markdown.setup.default")
    def test_credentials_error(self, mock_default: Mock) -> None:
        """Test when credentials check raises other exception."""
        mock_default.side_effect = Exception("Credentials error")
        assert check_credentials_exist() is False


class TestGetCurrentProject:
    """Test getting current project."""

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_get_project_success(self, mock_gcloud_run: Mock) -> None:
        """Test successfully getting project."""
        mock_gcloud_run.return_value = "my-project-id"
        assert get_current_project() == "my-project-id"
        mock_gcloud_run.assert_called_once_with(
            ["config", "get-value", "project"],
            operation="getting current default GCP project",
            timeout=10,
        )

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_get_project_empty(self, mock_gcloud_run: Mock) -> None:
        """Test when project is not set."""
        mock_gcloud_run.return_value = ""
        assert get_current_project() is None

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_get_project_error(self, mock_gcloud_run: Mock) -> None:
        """Test when getting project fails."""
        mock_gcloud_run.return_value = None
        assert get_current_project() is None


class TestListAvailableProjects:
    """Test listing available projects."""

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_list_projects_success(self, mock_gcloud_run: Mock) -> None:
        """Test successfully listing projects."""
        mock_gcloud_run.return_value = "project-1\nproject-2\nproject-3"
        projects = list_available_projects()
        assert projects == ["project-1", "project-2", "project-3"]
        mock_gcloud_run.assert_called_once_with(
            ["projects", "list", "--format=value(projectId)"],
            operation="listing available GCP projects",
            timeout=30,
        )

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_list_projects_empty(self, mock_gcloud_run: Mock) -> None:
        """Test when no projects are available."""
        mock_gcloud_run.return_value = ""
        assert list_available_projects() == []

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_list_projects_error(self, mock_gcloud_run: Mock) -> None:
        """Test when listing projects fails."""
        mock_gcloud_run.return_value = None
        assert list_available_projects() == []


class TestSetProject:
    """Test setting project."""

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_set_project_success(self, mock_gcloud_exec: Mock) -> None:
        """Test successfully setting project."""
        mock_gcloud_exec.return_value = True
        assert set_project("my-project-id") is True
        mock_gcloud_exec.assert_called_once_with(
            ["config", "set", "project", "my-project-id"],
            operation="setting default GCP project to 'my-project-id'",
            timeout=10,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_set_project_error(self, mock_gcloud_exec: Mock) -> None:
        """Test when setting project fails."""
        mock_gcloud_exec.return_value = False
        assert set_project("my-project-id") is False


class TestCheckApiEnabled:
    """Test checking if API is enabled."""

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_api_enabled(self, mock_gcloud_run: Mock) -> None:
        """Test when API is enabled."""
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        assert check_api_enabled("my-project") is True

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_api_not_enabled(self, mock_gcloud_run: Mock) -> None:
        """Test when API is not enabled."""
        mock_gcloud_run.return_value = ""
        assert check_api_enabled("my-project") is False

    @patch("google_docs_markdown.setup.gcloud_run")
    def test_check_api_error(self, mock_gcloud_run: Mock) -> None:
        """Test when checking API fails."""
        mock_gcloud_run.return_value = None
        assert check_api_enabled("my-project") is False


class TestEnableDocsApi:
    """Test enabling Docs API."""

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_enable_api_success(self, mock_gcloud_exec: Mock) -> None:
        """Test successfully enabling API."""
        mock_gcloud_exec.return_value = True
        assert enable_docs_api("my-project") is True
        mock_gcloud_exec.assert_called_once_with(
            [
                "services",
                "enable",
                DOCS_API_SERVICE,
                "--project=my-project",
            ],
            operation="enabling Google Docs API for project 'my-project'",
            timeout=60,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_enable_api_error(self, mock_gcloud_exec: Mock) -> None:
        """Test when enabling API fails."""
        mock_gcloud_exec.return_value = False
        assert enable_docs_api("my-project") is False


class TestRunAuthLogin:
    """Test running auth login."""

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_auth_login_success(self, mock_gcloud_exec: Mock) -> None:
        """Test successfully running auth login."""
        mock_gcloud_exec.return_value = True
        assert run_auth_login() is True
        scopes_str = ",".join(REQUIRED_SCOPES)
        mock_gcloud_exec.assert_called_once_with(
            [
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
            ],
            operation="running authentication",
            timeout=300,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_auth_login_with_extra_scopes(self, mock_gcloud_exec: Mock) -> None:
        """Test auth login with extra scopes."""
        mock_gcloud_exec.return_value = True
        extra_scopes = "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets"
        assert run_auth_login(extra_scopes) is True

        expected_scopes = REQUIRED_SCOPES + [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        scopes_str = ",".join(expected_scopes)
        mock_gcloud_exec.assert_called_once_with(
            [
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
            ],
            operation="running authentication",
            timeout=300,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_auth_login_with_extra_scopes_whitespace(self, mock_gcloud_exec: Mock) -> None:
        """Test auth login with extra scopes containing whitespace."""
        mock_gcloud_exec.return_value = True
        extra_scopes = "  https://www.googleapis.com/auth/drive  ,  https://www.googleapis.com/auth/spreadsheets  "
        assert run_auth_login(extra_scopes) is True

        expected_scopes = REQUIRED_SCOPES + [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        scopes_str = ",".join(expected_scopes)
        mock_gcloud_exec.assert_called_once_with(
            [
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
            ],
            operation="running authentication",
            timeout=300,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_auth_login_error(self, mock_gcloud_exec: Mock) -> None:
        """Test when auth login fails."""
        mock_gcloud_exec.return_value = False
        assert run_auth_login() is False

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_auth_login_with_client_id_file(self, mock_gcloud_exec: Mock) -> None:
        """Test auth login with client ID file."""
        mock_gcloud_exec.return_value = True
        client_id_file = "/path/to/client_id.json"
        assert run_auth_login(client_id_file=client_id_file) is True

        scopes_str = ",".join(REQUIRED_SCOPES)
        mock_gcloud_exec.assert_called_once_with(
            [
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
                f"--client-id-file={client_id_file}",
            ],
            operation="running authentication",
            timeout=300,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_auth_login_with_extra_scopes_and_client_id_file(self, mock_gcloud_exec: Mock) -> None:
        """Test auth login with both extra scopes and client ID file."""
        mock_gcloud_exec.return_value = True
        extra_scopes = "https://www.googleapis.com/auth/drive"
        client_id_file = "/path/to/client_id.json"
        assert run_auth_login(extra_scopes=extra_scopes, client_id_file=client_id_file) is True

        expected_scopes = REQUIRED_SCOPES + ["https://www.googleapis.com/auth/drive"]
        scopes_str = ",".join(expected_scopes)
        mock_gcloud_exec.assert_called_once_with(
            [
                "auth",
                "application-default",
                "login",
                f"--scopes={scopes_str}",
                f"--client-id-file={client_id_file}",
            ],
            operation="running authentication",
            timeout=300,
        )


class TestRevokeCredentials:
    """Test revoking credentials."""

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_revoke_success(self, mock_gcloud_exec: Mock) -> None:
        """Test successfully revoking credentials."""
        mock_gcloud_exec.return_value = True
        assert revoke_credentials() is True
        mock_gcloud_exec.assert_called_once_with(
            ["auth", "application-default", "revoke"],
            operation="revoking Application Default Credentials",
            timeout=30,
        )

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_revoke_not_installed(self, mock_gcloud_exec: Mock) -> None:
        """Test when gcloud is not installed."""
        mock_gcloud_exec.return_value = False
        assert revoke_credentials() is False

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_revoke_error(self, mock_gcloud_exec: Mock) -> None:
        """Test when revoke fails."""
        mock_gcloud_exec.return_value = False
        assert revoke_credentials() is False

    @patch("google_docs_markdown.setup.gcloud_exec")
    def test_revoke_timeout(self, mock_gcloud_exec: Mock) -> None:
        """Test when revoke times out."""
        mock_gcloud_exec.return_value = False
        assert revoke_credentials() is False


class TestSetup:
    """Test main setup function."""

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_all_configured(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when everything is already configured."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_check_gcloud.assert_called_once()
        mock_check_creds.assert_called_once()
        mock_get_project.assert_called_once()
        mock_check_api.assert_called_once_with("my-project")
        mock_enable_api.assert_not_called()

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.sys.exit")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.prompt")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_gcloud_not_installed(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        mock_check_gcloud: Mock,
        mock_exit: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when gcloud is not installed."""
        mock_check_gcloud.return_value = False

        setup()

        mock_exit.assert_called_once_with(1)

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    def test_setup_credentials_not_exist(
        self,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_auth_login: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when credentials need to be created."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = False
        mock_auth_login.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_auth_login.assert_called_once_with("", None)

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.sys.exit")
    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.prompt")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_auth_login_fails(
        self,
        mock_echo: Mock,
        mock_prompt: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_auth_login: Mock,
        mock_exit: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when auth login fails."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = False
        mock_auth_login.return_value = False

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_exit.assert_called_once_with(1)

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.set_project")
    @patch("google_docs_markdown.setup.list_available_projects")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.prompt")
    @patch("google_docs_markdown.setup.typer.echo")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    def test_setup_no_project_select_by_number(
        self,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_echo: Mock,
        mock_prompt: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_list_projects: Mock,
        mock_set_project: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when no project is set and user selects by number."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = None
        mock_list_projects.return_value = ["project-1", "project-2"]
        mock_prompt.return_value = "1"
        mock_set_project.return_value = True
        mock_check_api.return_value = True

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_set_project.assert_called_once_with("project-1")
        mock_check_api.assert_called_once_with("project-1")

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.set_project")
    @patch("google_docs_markdown.setup.list_available_projects")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.prompt")
    @patch("google_docs_markdown.setup.typer.echo")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    def test_setup_no_project_select_by_id(
        self,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_echo: Mock,
        mock_prompt: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_list_projects: Mock,
        mock_set_project: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when no project is set and user selects by project ID."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = None
        mock_list_projects.return_value = ["project-1", "project-2"]
        mock_prompt.return_value = "project-2"
        mock_set_project.return_value = True
        mock_check_api.return_value = True

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_set_project.assert_called_once_with("project-2")
        mock_check_api.assert_called_once_with("project-2")

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.sys.exit")
    @patch("google_docs_markdown.setup.list_available_projects")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_no_projects_available(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_list_projects: Mock,
        mock_exit: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when no projects are available."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = None
        mock_list_projects.return_value = []
        # Make sys.exit raise SystemExit to stop execution, just like real sys.exit
        mock_exit.side_effect = SystemExit(1)

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        try:
            setup()
        except SystemExit:
            pass  # Expected when sys.exit is called

        mock_exit.assert_called_once_with(1)

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_enable_api(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when API needs to be enabled."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = False
        mock_enable_api.return_value = True

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_enable_api.assert_called_once_with("my-project")

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.sys.exit")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_enable_api_fails(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_exit: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when enabling API fails."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = False
        mock_enable_api.return_value = False

        # Mock Path to return non-existent default client_id_file
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_exit.assert_called_once_with(1)

    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.revoke_credentials")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_revoke(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_revoke: Mock,
        mock_auth_login: Mock,
    ) -> None:
        """Test setup with revoke parameter."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_revoke.return_value = True
        mock_auth_login.return_value = True

        setup(revoke=True)

        mock_revoke.assert_called_once()
        mock_auth_login.assert_called_once_with("", None)

    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.revoke_credentials")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_revoke_failure(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_revoke: Mock,
        mock_auth_login: Mock,
    ) -> None:
        """Test setup when revoke fails but continues."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_revoke.return_value = False
        mock_auth_login.return_value = True

        setup(revoke=True)

        mock_revoke.assert_called_once()
        mock_auth_login.assert_called_once_with("", None)

    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_extra_scopes(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_auth_login: Mock,
    ) -> None:
        """Test setup with extra scopes."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = False
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_auth_login.return_value = True

        extra_scopes = "https://www.googleapis.com/auth/drive"
        setup(extra_scopes=extra_scopes)

        mock_auth_login.assert_called_once_with(extra_scopes, None)

    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.revoke_credentials")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_revoke_and_extra_scopes(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_revoke: Mock,
        mock_auth_login: Mock,
    ) -> None:
        """Test setup with both revoke and extra scopes."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_revoke.return_value = True
        mock_auth_login.return_value = True

        extra_scopes = "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets"
        setup(revoke=True, extra_scopes=extra_scopes)

        mock_revoke.assert_called_once()
        mock_auth_login.assert_called_once_with(extra_scopes, None)

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_explicit_client_id_file(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_auth_login: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup with explicit client ID file."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = False
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_auth_login.return_value = True

        client_id_file = "/custom/path/client_id.json"
        setup(client_id_file=client_id_file)

        mock_auth_login.assert_called_once_with("", client_id_file)
        # Path.home() should not be called when explicit file is provided
        mock_path.home.assert_not_called()

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_default_client_id_file_exists(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_auth_login: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup with default client ID file that exists."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = False
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_auth_login.return_value = True

        # Mock Path.home() and the client_id file existence
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = True
        mock_client_id_file.__str__.return_value = "/home/user/.config/google-docs-markdown/client_id_file.json"

        setup()

        mock_auth_login.assert_called_once_with("", "/home/user/.config/google-docs-markdown/client_id_file.json")

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_default_client_id_file_not_exists(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_auth_login: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup when default client ID file doesn't exist."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = False
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_auth_login.return_value = True

        # Mock Path.home() and the client_id file not existing
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home
        mock_config_dir = MagicMock()
        mock_home.__truediv__.return_value = mock_config_dir
        mock_gdm_dir = MagicMock()
        mock_config_dir.__truediv__.return_value = mock_gdm_dir
        mock_client_id_file = MagicMock()
        mock_gdm_dir.__truediv__.return_value = mock_client_id_file
        mock_client_id_file.exists.return_value = False

        setup()

        mock_auth_login.assert_called_once_with("", None)

    @patch("google_docs_markdown.setup.Path")
    @patch("google_docs_markdown.setup.run_auth_login")
    @patch("google_docs_markdown.setup.enable_docs_api")
    @patch("google_docs_markdown.setup.check_api_enabled")
    @patch("google_docs_markdown.setup.get_current_project")
    @patch("google_docs_markdown.setup.check_credentials_exist")
    @patch("google_docs_markdown.setup.check_gcloud_installed")
    @patch("google_docs_markdown.setup.typer.echo")
    def test_setup_with_all_options(
        self,
        mock_echo: Mock,
        mock_check_gcloud: Mock,
        mock_check_creds: Mock,
        mock_get_project: Mock,
        mock_check_api: Mock,
        mock_enable_api: Mock,
        mock_auth_login: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup with revoke, extra scopes, and client ID file."""
        mock_check_gcloud.return_value = True
        mock_check_creds.return_value = True
        mock_get_project.return_value = "my-project"
        mock_check_api.return_value = True
        mock_auth_login.return_value = True

        extra_scopes = "https://www.googleapis.com/auth/drive"
        client_id_file = "/custom/path/client_id.json"

        # Need to mock revoke_credentials
        with patch("google_docs_markdown.setup.revoke_credentials") as mock_revoke:
            mock_revoke.return_value = True
            setup(revoke=True, extra_scopes=extra_scopes, client_id_file=client_id_file)

            mock_revoke.assert_called_once()
            mock_auth_login.assert_called_once_with(extra_scopes, client_id_file)
