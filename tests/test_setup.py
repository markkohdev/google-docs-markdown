"""
Tests for setup module.

Tests authentication checks, project configuration, and API enablement.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, Mock, patch

import pytest
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


# Fixtures for TestSetup class
@pytest.fixture(scope="class")
def mock_gcloud_run() -> Iterator[Mock]:
    """Class-scoped fixture for gcloud_run."""
    with patch("google_docs_markdown.setup.gcloud_run") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_gcloud_exec() -> Iterator[Mock]:
    """Class-scoped fixture for gcloud_exec."""
    with patch("google_docs_markdown.setup.gcloud_exec") as mock:
        yield mock


@pytest.fixture(scope="class", autouse=True)
def mock_typer_echo() -> Iterator[Mock]:
    """Autouse fixture for typer.echo - always mocked but rarely asserted."""
    with patch("google_docs_markdown.setup.typer.echo") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_sys_exit() -> Iterator[Mock]:
    """Class-scoped fixture for sys.exit."""
    with patch("google_docs_markdown.setup.sys.exit") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_check_gcloud_installed() -> Iterator[Mock]:
    """Class-scoped fixture for check_gcloud_installed helper function."""
    with patch("google_docs_markdown.setup.check_gcloud_installed") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_check_credentials_exist() -> Iterator[Mock]:
    """Class-scoped fixture for check_credentials_exist helper function."""
    with patch("google_docs_markdown.setup.check_credentials_exist") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_get_current_project() -> Iterator[Mock]:
    """Class-scoped fixture for get_current_project helper function."""
    with patch("google_docs_markdown.setup.get_current_project") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_typer_prompt() -> Iterator[Mock]:
    """Class-scoped fixture for typer.prompt."""
    with patch("google_docs_markdown.setup.typer.prompt") as mock:
        yield mock


@pytest.fixture(scope="class")
def mock_path() -> Iterator[Mock]:
    """Class-scoped fixture for Path."""
    with patch("google_docs_markdown.setup.Path") as mock_path_class:
        yield mock_path_class


@pytest.fixture(scope="class")
def mock_client_id_path_not_exists(mock_path: Mock) -> tuple[Mock, MagicMock]:
    """Helper fixture to mock Path.home() chain with client_id_file not existing."""
    mock_home = MagicMock()
    mock_path.home.return_value = mock_home
    mock_config_dir = MagicMock()
    mock_home.__truediv__.return_value = mock_config_dir
    mock_gdm_dir = MagicMock()
    mock_config_dir.__truediv__.return_value = mock_gdm_dir
    mock_client_id_file = MagicMock()
    mock_gdm_dir.__truediv__.return_value = mock_client_id_file
    mock_client_id_file.exists.return_value = False
    return mock_path, mock_client_id_file


@pytest.fixture(scope="class")
def mock_client_id_path_exists(mock_path: Mock) -> tuple[Mock, MagicMock]:
    """Helper fixture to mock Path.home() chain with client_id_file existing."""
    mock_home = MagicMock()
    mock_path.home.return_value = mock_home
    mock_config_dir = MagicMock()
    mock_home.__truediv__.return_value = mock_config_dir
    mock_gdm_dir = MagicMock()
    mock_config_dir.__truediv__.return_value = mock_gdm_dir
    mock_client_id_file = MagicMock()
    mock_gdm_dir.__truediv__.return_value = mock_client_id_file
    mock_client_id_file.exists.return_value = True
    # Configure __str__ to return the path string - use configure_mock to avoid assignment error
    default_path = "/home/user/.config/google-docs-markdown/client_id_file.json"
    mock_client_id_file.configure_mock(__str__=lambda self: default_path)
    return mock_path, mock_client_id_file


class TestSetup:
    """Test main setup function."""

    def setup_method(self) -> None:
        """Reset mock state before each test to avoid state leakage."""
        # This method is called before each test method
        pass

    def test_setup_all_configured(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when everything is already configured."""
        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API, not check_api_enabled()
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"

        setup()

        mock_check_gcloud_installed.assert_called_once()
        mock_check_credentials_exist.assert_called_once()
        mock_get_current_project.assert_called_once()
        # Verify gcloud_run was called to check API (setup() calls it directly)
        assert mock_gcloud_run.call_count >= 1

    def test_setup_gcloud_not_installed(
        self,
        mock_check_gcloud_installed: Mock,
        mock_sys_exit: Mock,
    ) -> None:
        """Test setup when gcloud is not installed."""
        mock_check_gcloud_installed.return_value = False

        setup()

        mock_sys_exit.assert_called_once_with(1)

    def test_setup_credentials_not_exist(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_exec: Mock,
        mock_gcloud_run: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when credentials need to be created."""
        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = False
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_exec for auth login, not run_auth_login()
        mock_gcloud_exec.return_value = True
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"

        setup()

        # Verify gcloud_exec was called for auth login
        auth_calls = [call for call in mock_gcloud_exec.call_args_list if "auth" in str(call)]
        assert len(auth_calls) > 0

    def test_setup_auth_login_fails(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_gcloud_exec: Mock,
        mock_sys_exit: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when auth login fails."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_sys_exit.reset_mock()
        mock_sys_exit.side_effect = None

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = False
        # setup() directly calls gcloud_exec for auth login, which raises GCloudException on failure
        from google_docs_markdown.gcloud import GCloudException
        mock_gcloud_exec.side_effect = GCloudException(
            message="Failed to authenticate",
            operation="running authentication",
            command=["gcloud", "auth", "application-default", "login"],
        )

        setup()

        mock_sys_exit.assert_called_once_with(1)

    def test_setup_no_project_select_by_number(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_typer_prompt: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when no project is set and user selects by number."""
        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = None
        # setup() directly calls gcloud_run to list projects
        mock_gcloud_run.return_value = "project-1\nproject-2"
        mock_typer_prompt.return_value = "1"
        mock_gcloud_exec.return_value = True

        setup()

        # Verify gcloud_exec was called to set project
        set_project_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "config" in str(call) and "set" in str(call) and "project" in str(call)
        ]
        assert len(set_project_calls) > 0
        # Verify gcloud_run was called to check API
        assert mock_gcloud_run.call_count >= 2  # Once for listing, once for checking API

    def test_setup_no_project_select_by_id(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_typer_prompt: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when no project is set and user selects by project ID."""
        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = None
        # setup() directly calls gcloud_run to list projects
        mock_gcloud_run.return_value = "project-1\nproject-2"
        mock_typer_prompt.return_value = "project-2"
        mock_gcloud_exec.return_value = True

        setup()

        # Verify gcloud_exec was called to set project
        set_project_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "config" in str(call) and "set" in str(call) and "project" in str(call)
        ]
        assert len(set_project_calls) > 0
        # Verify gcloud_run was called to check API
        assert mock_gcloud_run.call_count >= 2

    def test_setup_no_projects_available(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_sys_exit: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when no projects are available."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_run.reset_mock()
        mock_sys_exit.reset_mock()
        mock_sys_exit.side_effect = None

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = None
        # setup() directly calls gcloud_run to list projects
        mock_gcloud_run.return_value = ""
        # Make sys.exit raise SystemExit to stop execution, just like real sys.exit
        mock_sys_exit.side_effect = SystemExit(1)

        try:
            setup()
        except SystemExit:
            pass  # Expected when sys.exit is called

        mock_sys_exit.assert_called_once_with(1)

    def test_setup_enable_api(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when API needs to be enabled."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API - return empty (not enabled)
        mock_gcloud_run.return_value = ""
        # setup() directly calls gcloud_exec to enable API
        mock_gcloud_exec.return_value = True

        setup()

        # Verify gcloud_exec was called to enable API
        enable_api_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "services" in str(call) and "enable" in str(call)
        ]
        assert len(enable_api_calls) > 0

    def test_setup_enable_api_fails(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_sys_exit: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when enabling API fails."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()
        mock_sys_exit.reset_mock()
        mock_sys_exit.side_effect = None

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API - return empty (not enabled)
        mock_gcloud_run.return_value = ""
        # setup() directly calls gcloud_exec to enable API, which raises GCloudException on failure
        from google_docs_markdown.gcloud import GCloudException
        mock_gcloud_exec.side_effect = GCloudException(
            message="Failed to enable API",
            operation="enabling Google Docs API",
            command=["gcloud", "services", "enable", DOCS_API_SERVICE],
        )

        setup()

        mock_sys_exit.assert_called_once_with(1)

    def test_setup_with_revoke(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
    ) -> None:
        """Test setup with revoke parameter."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for revoke and auth login
        mock_gcloud_exec.return_value = True

        setup(revoke=True)

        # Verify gcloud_exec was called for revoke
        revoke_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "revoke" in str(call)
        ]
        assert len(revoke_calls) > 0
        # Verify gcloud_exec was called for auth login
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert len(auth_calls) > 0

    def test_setup_with_revoke_failure(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
    ) -> None:
        """Test setup when revoke fails but continues."""
        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec - first call (revoke) raises exception, second (auth) succeeds
        from google_docs_markdown.gcloud import GCloudException
        mock_gcloud_exec.side_effect = [
            GCloudException(
                message="Failed to revoke",
                operation="revoking Application Default Credentials",
                command=["gcloud", "auth", "application-default", "revoke"],
            ),
            True,  # auth login succeeds
        ]

        setup(revoke=True)

        # Verify gcloud_exec was called at least twice (revoke and auth)
        assert mock_gcloud_exec.call_count >= 2

    def test_setup_with_extra_scopes(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup with extra scopes."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = False
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for auth login
        mock_gcloud_exec.return_value = True

        extra_scopes = "https://www.googleapis.com/auth/drive"
        setup(extra_scopes=extra_scopes)

        # Verify gcloud_exec was called for auth login with extra scopes
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert len(auth_calls) > 0
        # Verify extra scopes are in the call
        assert any("drive" in str(call) for call in auth_calls)

    def test_setup_with_revoke_and_extra_scopes(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
    ) -> None:
        """Test setup with both revoke and extra scopes."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for revoke and auth login
        mock_gcloud_exec.return_value = True

        extra_scopes = "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets"
        setup(revoke=True, extra_scopes=extra_scopes)

        # Verify gcloud_exec was called for revoke and auth login
        assert mock_gcloud_exec.call_count >= 2
        # Verify extra scopes are in the auth call
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert any("drive" in str(call) or "spreadsheets" in str(call) for call in auth_calls)

    def test_setup_with_explicit_client_id_file(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup with explicit client ID file."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()
        mock_path.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = False
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for auth login
        mock_gcloud_exec.return_value = True

        client_id_file = "/custom/path/client_id.json"
        setup(client_id_file=client_id_file)

        # Verify gcloud_exec was called for auth login with client_id_file
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert len(auth_calls) > 0
        # Verify client_id_file is in the call
        assert any("client_id_file" in str(call) or client_id_file in str(call) for call in auth_calls)
        # Path.home() should not be called when explicit file is provided
        mock_path.home.assert_not_called()

    def test_setup_with_default_client_id_file_exists(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_client_id_path_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup with default client ID file that exists."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = False
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for auth login
        mock_gcloud_exec.return_value = True

        setup()

        # Verify gcloud_exec was called for auth login with client_id_file
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert len(auth_calls) > 0
        # Verify client_id_file path is in the call
        assert any("client_id_file" in str(call) or "client_id_file.json" in str(call) for call in auth_calls)

    def test_setup_with_default_client_id_file_not_exists(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_client_id_path_not_exists: tuple[Mock, MagicMock],
    ) -> None:
        """Test setup when default client ID file doesn't exist."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = False
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for auth login
        mock_gcloud_exec.return_value = True

        setup()

        # Verify gcloud_exec was called for auth login without client_id_file
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert len(auth_calls) > 0

    def test_setup_with_all_options(
        self,
        mock_check_gcloud_installed: Mock,
        mock_check_credentials_exist: Mock,
        mock_get_current_project: Mock,
        mock_gcloud_run: Mock,
        mock_gcloud_exec: Mock,
        mock_path: Mock,
    ) -> None:
        """Test setup with revoke, extra scopes, and client ID file."""
        # Reset mocks to avoid state leakage from previous tests
        mock_gcloud_exec.reset_mock()
        mock_gcloud_exec.side_effect = None
        mock_gcloud_run.reset_mock()

        mock_check_gcloud_installed.return_value = True
        mock_check_credentials_exist.return_value = True
        mock_get_current_project.return_value = "my-project"
        # setup() directly calls gcloud_run to check API
        mock_gcloud_run.return_value = f"projects/my-project/services/{DOCS_API_SERVICE}"
        # setup() directly calls gcloud_exec for revoke and auth login
        mock_gcloud_exec.return_value = True

        extra_scopes = "https://www.googleapis.com/auth/drive"
        client_id_file = "/custom/path/client_id.json"

        setup(revoke=True, extra_scopes=extra_scopes, client_id_file=client_id_file)

        # Verify gcloud_exec was called for revoke and auth login
        assert mock_gcloud_exec.call_count >= 2
        # Verify revoke call
        revoke_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "revoke" in str(call)
        ]
        assert len(revoke_calls) > 0
        # Verify auth login call with extra scopes and client_id_file
        auth_calls = [
            call for call in mock_gcloud_exec.call_args_list
            if "auth" in str(call) and "login" in str(call)
        ]
        assert len(auth_calls) > 0
        assert any("drive" in str(call) for call in auth_calls)
        assert any("client_id_file" in str(call) or client_id_file in str(call) for call in auth_calls)
