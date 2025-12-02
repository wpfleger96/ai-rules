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
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        success, message = install_tool("test-package")
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_install_pypi_package(self, monkeypatch):
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
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )
        success, message = install_tool("test-package", dry_run=True)
        assert success is True
        assert "Would run:" in message

    @pytest.mark.parametrize(
        "error_type,expected_message",
        [
            ("timeout", "timed out"),
            ("command_failure", "package not found"),
            ("empty_error", "failed"),
            ("unexpected", "unexpected error"),
        ],
    )
    def test_install_handles_errors(self, monkeypatch, error_type, expected_message):
        """Test that install handles various error conditions gracefully."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            if error_type == "timeout":
                raise subprocess.TimeoutExpired("uv", 60)
            elif error_type == "command_failure":

                class CommandFailureResult:
                    returncode = 1
                    stderr = "Installation failed: package not found"
                    stdout = ""

                return CommandFailureResult()
            elif error_type == "empty_error":

                class EmptyErrorResult:
                    returncode = 1
                    stderr = ""
                    stdout = ""

                return EmptyErrorResult()
            elif error_type == "unexpected":
                raise ValueError("Unexpected error")

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = install_tool("test-package")
        assert success is False
        assert expected_message in message.lower()


@pytest.mark.unit
@pytest.mark.bootstrap
class TestUninstallTool:
    """Tests for uninstall_tool function."""

    def test_uninstall_without_uv_returns_error(self, monkeypatch):
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: False
        )
        success, message = uninstall_tool("test-package")
        assert success is False
        assert message == UV_NOT_FOUND_ERROR

    def test_uninstall_package(self, monkeypatch):
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

    @pytest.mark.parametrize(
        "error_type,expected_message",
        [
            ("timeout", "timed out"),
            ("command_failure", "package not installed"),
            ("empty_error", "failed"),
            ("unexpected", "unexpected error"),
        ],
    )
    def test_uninstall_handles_errors(self, monkeypatch, error_type, expected_message):
        """Test that uninstall handles various error conditions gracefully."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.installer.is_uv_available", lambda: True
        )

        def mock_run(*args, **kwargs):
            if error_type == "timeout":
                raise subprocess.TimeoutExpired("uv", 30)
            elif error_type == "command_failure":

                class CommandFailureResult:
                    returncode = 1
                    stderr = "Package not installed"
                    stdout = ""

                return CommandFailureResult()
            elif error_type == "empty_error":

                class EmptyErrorResult:
                    returncode = 1
                    stderr = ""
                    stdout = ""

                return EmptyErrorResult()
            elif error_type == "unexpected":
                raise ValueError("Unexpected error")

        monkeypatch.setattr("subprocess.run", mock_run)
        success, message = uninstall_tool("test-package")
        assert success is False
        assert expected_message in message.lower()
