"""Tests for update checking and application utilities."""

import json
import subprocess
import urllib.error

from pathlib import Path

import pytest

from ai_rules.bootstrap.detection import UV_NOT_FOUND_ERROR, InstallationInfo
from ai_rules.bootstrap.updater import (
    _get_default_branch,
    check_git_updates,
    check_pypi_updates,
    perform_git_update,
    perform_pypi_update,
    perform_update,
)


@pytest.mark.unit
@pytest.mark.bootstrap
class TestGetDefaultBranch:
    """Tests for _get_default_branch helper function."""

    def test_get_current_branch(self, monkeypatch):
        """Test getting current branch name."""

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "main\n"

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        branch = _get_default_branch(Path("/fake/repo"))
        assert branch == "main"

    def test_get_branch_from_symbolic_ref(self, monkeypatch):
        """Test getting branch from symbolic ref when current branch empty."""

        def mock_run(*args, **kwargs):
            class Result:
                returncode: int
                stdout: str

            result = Result()
            if "branch" in args[0]:
                result.returncode = 0
                result.stdout = ""
            else:
                result.returncode = 0
                result.stdout = "refs/remotes/origin/master\n"
            return result

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        branch = _get_default_branch(Path("/fake/repo"))
        assert branch == "master"

    def test_fallback_to_main(self, monkeypatch):
        """Test fallback to 'main' on error."""

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="git", timeout=5)

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        branch = _get_default_branch(Path("/fake/repo"))
        assert branch == "main"


@pytest.mark.unit
@pytest.mark.bootstrap
class TestCheckGitUpdates:
    """Tests for check_git_updates function."""

    def test_check_git_updates_no_update(self, monkeypatch):
        """Test when local and remote are in sync."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "main"
        )
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1

            class Result:
                returncode = 0
                stdout = {
                    1: "",
                    2: "abc1234\n",
                    3: "abc1234\n",
                    4: "v1.0.0\n",
                }.get(call_count[0], "")

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        update_info = check_git_updates(Path("/fake/repo"))
        assert update_info.has_update is False
        assert update_info.current_version == "v1.0.0"

    def test_check_git_updates_has_update(self, monkeypatch):
        """Test when remote has new commits."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "main"
        )
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1

            class Result:
                returncode = 0
                stdout = {
                    1: "",
                    2: "abc1234\n",
                    3: "def5678\n",
                    4: "v1.0.0\n",
                    5: "v1.1.0\n",
                }.get(call_count[0], "")

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        update_info = check_git_updates(Path("/fake/repo"))
        assert update_info.has_update is True
        assert update_info.current_version == "v1.0.0"
        assert update_info.latest_version == "v1.1.0"
        assert update_info.source == "git"

    def test_check_git_updates_uses_detected_branch(self, monkeypatch):
        """Test that detected branch is used in git commands."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "develop"
        )
        calls = []
        call_count = [0]

        def mock_run(*args, **kwargs):
            calls.append(args)
            call_count[0] += 1

            class Result:
                returncode = 0
                stdout = {
                    1: "",
                    2: "abc1234\n",
                    3: "abc1234\n",
                    4: "v1.0.0\n",
                }.get(call_count[0], "")

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        check_git_updates(Path("/fake/repo"))
        assert any("origin/develop" in str(call) for call in calls)

    def test_check_git_updates_error_returns_no_update(self, monkeypatch):
        """Test that errors return no update."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "main"
        )

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "git")

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        update_info = check_git_updates(Path("/fake/repo"))
        assert update_info.has_update is False


@pytest.mark.unit
@pytest.mark.bootstrap
class TestCheckPyPIUpdates:
    """Tests for check_pypi_updates function."""

    def test_check_pypi_no_update(self, monkeypatch):
        """Test when current version is up to date."""

        class MockResponse:
            def read(self):
                return json.dumps({"info": {"version": "1.0.0"}}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.urllib.request.urlopen",
            lambda req, timeout: MockResponse(),
        )

        update_info = check_pypi_updates("test-package", "1.0.0")
        assert update_info.has_update is False
        assert update_info.current_version == "1.0.0"
        assert update_info.latest_version == "1.0.0"

    def test_check_pypi_has_update(self, monkeypatch):
        """Test when newer version is available."""

        class MockResponse:
            def read(self):
                return json.dumps({"info": {"version": "1.1.0"}}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.urllib.request.urlopen",
            lambda req, timeout: MockResponse(),
        )

        update_info = check_pypi_updates("test-package", "1.0.0")
        assert update_info.has_update is True
        assert update_info.current_version == "1.0.0"
        assert update_info.latest_version == "1.1.0"
        assert update_info.source == "pypi"

    def test_check_pypi_network_error(self, monkeypatch):
        """Test handling of network errors."""

        def mock_urlopen(*args, **kwargs):
            raise urllib.error.URLError("Network error")

        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.urllib.request.urlopen", mock_urlopen
        )
        update_info = check_pypi_updates("test-package", "1.0.0")
        assert update_info.has_update is False

    def test_check_pypi_invalid_package_name(self):
        """Test that invalid package names are rejected."""
        update_info = check_pypi_updates("../../../etc/passwd", "1.0.0")
        assert update_info.has_update is False

    def test_check_pypi_package_name_validation(self):
        """Test package name validation with various invalid names."""
        invalid_names = [
            "package with spaces",
            "package/with/slashes",
            "../relative/path",
            "package;with;semicolons",
            "",
        ]
        for name in invalid_names:
            update_info = check_pypi_updates(name, "1.0.0")
            assert update_info.has_update is False, f"Should reject: {name}"


@pytest.mark.unit
@pytest.mark.bootstrap
class TestPerformGitUpdate:
    """Tests for perform_git_update function."""

    def test_perform_git_update_success(self, monkeypatch):
        """Test successful git pull."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "main"
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stderr = ""
                stdout = "Already up to date"

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message = perform_git_update(Path("/fake/repo"))
        assert success is True
        assert "successful" in message.lower()

    def test_perform_git_update_uses_detected_branch(self, monkeypatch):
        """Test that detected branch is used in pull command."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "develop"
        )
        call_args = []

        def mock_run(*args, **kwargs):
            call_args.append(args[0])

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        perform_git_update(Path("/fake/repo"))
        assert "develop" in call_args[0]

    def test_perform_git_update_failure(self, monkeypatch):
        """Test git pull failure."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "main"
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Merge conflict"
                stdout = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message = perform_git_update(Path("/fake/repo"))
        assert success is False
        assert "Merge conflict" in message

    def test_perform_git_update_timeout(self, monkeypatch):
        """Test git pull timeout."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater._get_default_branch", lambda path: "main"
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="git", timeout=30)

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message = perform_git_update(Path("/fake/repo"))
        assert success is False
        assert "timed out" in message.lower()


@pytest.mark.unit
@pytest.mark.bootstrap
class TestPerformPyPIUpdate:
    """Tests for perform_pypi_update function."""

    def test_perform_pypi_update_without_uv(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr("ai_rules.bootstrap.updater.is_uv_available", lambda: False)
        success, message = perform_pypi_update("test-package")
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_perform_pypi_update_success(self, monkeypatch):
        """Test successful upgrade."""
        monkeypatch.setattr("ai_rules.bootstrap.updater.is_uv_available", lambda: True)

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message = perform_pypi_update("test-package")
        assert success is True
        assert "successful" in message.lower()

    def test_perform_pypi_update_failure(self, monkeypatch):
        """Test upgrade failure."""
        monkeypatch.setattr("ai_rules.bootstrap.updater.is_uv_available", lambda: True)

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Package not found"
                stdout = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message = perform_pypi_update("nonexistent")
        assert success is False
        assert "Package not found" in message


@pytest.mark.unit
@pytest.mark.bootstrap
class TestPerformUpdate:
    """Tests for perform_update function."""

    def test_perform_update_git_source(self, monkeypatch):
        """Test update for git-based installation."""
        git_calls = []
        install_calls = []

        def mock_git_update(repo_path):
            git_calls.append(repo_path)
            return (True, "Git update success")

        def mock_install_tool(*args, **kwargs):
            install_calls.append(args)
            return (True, "Install success")

        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.perform_git_update", mock_git_update
        )
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.install_tool", mock_install_tool
        )
        info = InstallationInfo(
            source="git",
            package_path=Path("/fake/path"),
            repo_path=Path("/fake/repo"),
            is_editable=False,
            package_name="test-package",
        )
        success, message = perform_update(info)
        assert success is True
        assert len(git_calls) == 1
        assert git_calls[0] == Path("/fake/repo")
        assert len(install_calls) == 1

    def test_perform_update_editable_source(self, monkeypatch):
        """Test update for editable installation."""
        git_calls = []
        install_calls = []

        def mock_git_update(repo_path):
            git_calls.append(repo_path)
            return (True, "Git update success")

        def mock_install_tool(*args, **kwargs):
            install_calls.append(args)
            return (True, "Install success")

        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.perform_git_update", mock_git_update
        )
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.install_tool", mock_install_tool
        )
        info = InstallationInfo(
            source="editable",
            package_path=Path("/fake/path"),
            repo_path=Path("/fake/repo"),
            is_editable=True,
            package_name="test-package",
        )
        success, message = perform_update(info)
        assert success is True
        assert len(git_calls) == 1
        assert len(install_calls) == 1

    def test_perform_update_pypi_source(self, monkeypatch):
        """Test update for PyPI installation."""
        pypi_calls = []

        def mock_pypi_update(package_name):
            pypi_calls.append(package_name)
            return (True, "Success")

        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.perform_pypi_update", mock_pypi_update
        )
        info = InstallationInfo(
            source="pypi",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = perform_update(info)
        assert success is True
        assert len(pypi_calls) == 1
        assert pypi_calls[0] == "test-package"

    def test_perform_update_unknown_source(self):
        """Test update with unknown source."""
        info = InstallationInfo(
            source="unknown",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = perform_update(info)
        assert success is False
        assert "Unknown installation source" in message
