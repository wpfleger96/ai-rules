"""Tests for tool installation utilities."""

import subprocess

import pytest

from ai_rules.bootstrap.installer import (
    UV_NOT_FOUND_ERROR,
    install_tool,
    uninstall_tool,
)


@pytest.mark.unit
@pytest.mark.bootstrap
class TestInstallTool:
    """Tests for install_tool function."""

    def test_install_without_uv_returns_error(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        success, message = install_tool("test-package")
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

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
        success, message = install_tool("test-package")
        assert success is True
        assert message == "Installation successful"
        assert len(captured_args) == 1
        call_args = captured_args[0][0][0]
        assert "uv" in call_args
        assert "tool" in call_args
        assert "install" in call_args
        assert "test-package" in call_args

    def test_install_with_force_flag(self, monkeypatch):
        """Test that force flag is passed to uv."""
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
        success, message = install_tool("test-package", force=True)
        assert success is True
        assert len(captured_args) == 1
        call_args = captured_args[0][0][0]
        assert "--force" in call_args

    def test_install_dry_run(self, monkeypatch):
        """Test dry run mode."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )
        success, message = install_tool("test-package", dry_run=True)
        assert success is True
        assert "Would run:" in message

    def test_install_handles_timeout(self, monkeypatch):
        """Test that timeouts are handled gracefully."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("uv", 60)

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_tool("test-package")
        assert success is False
        assert "timed out" in message.lower()

    def test_install_handles_command_failure(self, monkeypatch):
        """Test handling of failed uv command."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Installation failed: package not found"
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_tool("test-package")
        assert success is False
        assert "package not found" in message

    def test_install_handles_empty_error(self, monkeypatch):
        """Test handling of failures with no stderr."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_tool("test-package")
        assert success is False
        assert "failed" in message.lower()

    def test_install_handles_unexpected_exception(self, monkeypatch):
        """Test handling of unexpected errors."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            raise ValueError("Unexpected error")

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_tool("test-package")
        assert success is False
        assert "Unexpected error" in message


@pytest.mark.unit
@pytest.mark.bootstrap
class TestUninstallTool:
    """Tests for uninstall_tool function."""

    def test_uninstall_without_uv_returns_error(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        success, message = uninstall_tool("test-package")
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_uninstall_package(self, monkeypatch):
        """Test uninstalling package."""
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
        assert "uv" in call_args
        assert "tool" in call_args
        assert "uninstall" in call_args
        assert "test-package" in call_args

    def test_uninstall_handles_timeout(self, monkeypatch):
        """Test that timeouts are handled gracefully."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("uv", 30)

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("test-package")
        assert success is False
        assert "timed out" in message.lower()

    def test_uninstall_handles_command_failure(self, monkeypatch):
        """Test handling of failed uv command."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Package not installed"
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("test-package")
        assert success is False
        assert "Package not installed" in message

    def test_uninstall_handles_empty_error(self, monkeypatch):
        """Test handling of failures with no stderr."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("test-package")
        assert success is False
        assert "failed" in message.lower()

    def test_uninstall_handles_unexpected_exception(self, monkeypatch):
        """Test handling of unexpected errors."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            raise ValueError("Unexpected error")

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("test-package")
        assert success is False
        assert "Unexpected error" in message
