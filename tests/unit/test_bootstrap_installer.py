"""Tests for tool installation utilities."""

import subprocess

from pathlib import Path

import pytest

from ai_rules.bootstrap.detection import UV_NOT_FOUND_ERROR, InstallationInfo
from ai_rules.bootstrap.installer import install_from_pypi, install_tool, uninstall_tool


@pytest.mark.unit
@pytest.mark.bootstrap
class TestInstallTool:
    """Tests for install_tool function."""

    def test_install_without_uv_returns_error(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        info = InstallationInfo(
            source="git",
            package_path=Path("/fake/path"),
            repo_path=Path("/fake/repo"),
            is_editable=True,
            package_name="test-package",
        )
        success, message = install_tool(info)
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_install_editable_package(self, monkeypatch):
        """Test installing editable package."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.append((args, kwargs))

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        info = InstallationInfo(
            source="editable",
            package_path=Path("/fake/path"),
            repo_path=Path("/fake/repo"),
            is_editable=True,
            package_name="test-package",
        )
        success, message = install_tool(info)
        assert success is True
        assert message == "Installation successful"
        assert len(captured_args) == 1
        call_args = captured_args[0][0][0]
        assert "-e" in call_args
        assert str(info.repo_path) in call_args

    def test_install_pypi_package(self, monkeypatch):
        """Test installing PyPI package."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.append((args, kwargs))

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        info = InstallationInfo(
            source="pypi",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = install_tool(info)
        assert success is True
        assert len(captured_args) == 1
        call_args = captured_args[0][0][0]
        assert "-e" not in call_args
        assert "test-package" in call_args

    def test_install_with_force_flag(self, monkeypatch):
        """Test installing with force flag."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.append((args, kwargs))

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        info = InstallationInfo(
            source="pypi",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = install_tool(info, force=True)
        assert success is True
        call_args = captured_args[0][0][0]
        assert "--force" in call_args

    def test_install_with_dry_run(self, monkeypatch):
        """Test dry-run mode."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )
        info = InstallationInfo(
            source="pypi",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = install_tool(info, dry_run=True)
        assert success is True
        assert "Would run:" in message

    def test_install_failure_returns_error(self, monkeypatch):
        """Test that installation failure returns error message."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Installation failed"
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        info = InstallationInfo(
            source="pypi",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = install_tool(info)
        assert success is False
        assert "Installation failed" in message

    def test_install_timeout(self, monkeypatch):
        """Test that timeout is handled."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="uv", timeout=60)

        monkeypatch.setattr("subprocess.run", mock_run)
        info = InstallationInfo(
            source="pypi",
            package_path=Path("/fake/path"),
            repo_path=None,
            is_editable=False,
            package_name="test-package",
        )
        success, message = install_tool(info)
        assert success is False
        assert "timed out" in message.lower()


@pytest.mark.unit
@pytest.mark.bootstrap
class TestUninstallTool:
    """Tests for uninstall_tool function."""

    def test_uninstall_without_uv_returns_error(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        success, message = uninstall_tool()
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_uninstall_success(self, monkeypatch):
        """Test successful uninstallation."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.append((args, kwargs))

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("test-package")
        assert success is True
        assert message == "Uninstallation successful"
        assert len(captured_args) == 1
        call_args = captured_args[0][0][0]
        assert "uninstall" in call_args
        assert "test-package" in call_args

    def test_uninstall_failure(self, monkeypatch):
        """Test uninstallation failure."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Package not found"
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("nonexistent-package")
        assert success is False
        assert "Package not found" in message

    def test_uninstall_timeout(self, monkeypatch):
        """Test uninstall timeout handling."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="uv", timeout=30)

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool()
        assert success is False
        assert "timed out" in message.lower()


@pytest.mark.unit
@pytest.mark.bootstrap
class TestInstallFromPyPI:
    """Tests for install_from_pypi function."""

    def test_install_from_pypi_without_uv(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        success, message = install_from_pypi()
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_install_from_pypi_success(self, monkeypatch):
        """Test successful PyPI installation."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.append((args, kwargs))

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_from_pypi("test-package")
        assert success is True
        assert message == "Installation successful"
        assert len(captured_args) == 1
        call_args = captured_args[0][0][0]
        assert "install" in call_args
        assert "test-package" in call_args
        assert "-e" not in call_args  # Should NOT be editable

    def test_install_from_pypi_with_force(self, monkeypatch):
        """Test PyPI installation with force flag."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.append((args, kwargs))

            class Result:
                returncode = 0
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_from_pypi(force=True)
        assert success is True
        call_args = captured_args[0][0][0]
        assert "--force" in call_args

    def test_install_from_pypi_dry_run(self, monkeypatch):
        """Test dry-run mode."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )
        success, message = install_from_pypi(dry_run=True)
        assert success is True
        assert "Would run:" in message

    def test_install_from_pypi_failure(self, monkeypatch):
        """Test PyPI installation failure."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Network error"
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_from_pypi()
        assert success is False
        assert "Network error" in message
