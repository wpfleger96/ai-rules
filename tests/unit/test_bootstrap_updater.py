"""Tests for update checking and application utilities."""

import subprocess

import pytest

from ai_rules.bootstrap.installer import UV_NOT_FOUND_ERROR
from ai_rules.bootstrap.updater import check_index_updates, perform_pypi_update


@pytest.mark.unit
@pytest.mark.bootstrap
class TestCheckIndexUpdates:
    """Tests for check_index_updates function."""

    def test_check_index_no_update(self, monkeypatch):
        """Test when current version is up to date."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "test-package (1.0.0)\nAvailable versions: 1.0.0"
                stderr = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)

        update_info = check_index_updates("test-package", "1.0.0")
        assert update_info.has_update is False
        assert update_info.current_version == "1.0.0"
        assert update_info.latest_version == "1.0.0"

    def test_check_index_has_update(self, monkeypatch):
        """Test when newer version is available."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "test-package (1.1.0)\nAvailable versions: 1.1.0, 1.0.0"
                stderr = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)

        update_info = check_index_updates("test-package", "1.0.0")
        assert update_info.has_update is True
        assert update_info.current_version == "1.0.0"
        assert update_info.latest_version == "1.1.0"
        assert update_info.source == "index"

    def test_check_index_command_error(self, monkeypatch):
        """Test handling of command errors."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stdout = ""
                stderr = "Network error"

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)

        update_info = check_index_updates("test-package", "1.0.0")
        assert update_info.has_update is False

    def test_check_index_invalid_package_name(self):
        """Test that invalid package names are rejected."""
        update_info = check_index_updates("../../../etc/passwd", "1.0.0")
        assert update_info.has_update is False

    def test_check_index_package_name_validation(self):
        """Test package name validation with various invalid names."""
        invalid_names = [
            "package with spaces",
            "package/with/slashes",
            "../relative/path",
            "package;with;semicolons",
            "",
        ]
        for name in invalid_names:
            update_info = check_index_updates(name, "1.0.0")
            assert update_info.has_update is False, f"Should reject: {name}"

    def test_check_index_without_uvx(self, monkeypatch):
        """Test that missing uvx returns no update."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: False
        )
        update_info = check_index_updates("test-package", "1.0.0")
        assert update_info.has_update is False

    def test_check_index_unparseable_output(self, monkeypatch):
        """Test handling of unparseable output."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "Unexpected output format"
                stderr = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)

        update_info = check_index_updates("test-package", "1.0.0")
        assert update_info.has_update is False

    def test_check_index_timeout(self, monkeypatch):
        """Test handling of timeout."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("uvx", 30)

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)

        update_info = check_index_updates("test-package", "1.0.0")
        assert update_info.has_update is False


@pytest.mark.unit
@pytest.mark.bootstrap
class TestPerformPyPIUpdate:
    """Tests for perform_pypi_update function."""

    def test_perform_pypi_update_without_uv(self, monkeypatch):
        """Test that missing uv returns error."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: False
        )
        success, message, was_upgraded = perform_pypi_update("test-package")
        assert success is False
        assert message == UV_NOT_FOUND_ERROR
        assert was_upgraded is False

    def test_perform_pypi_update_success(self, monkeypatch):
        """Test successful upgrade."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stderr = ""
                stdout = "Upgraded test-package from 1.0.0 to 1.1.0"

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("test-package")
        assert success is True
        assert "successful" in message.lower()
        assert was_upgraded is True

    def test_perform_pypi_update_failure(self, monkeypatch):
        """Test upgrade failure."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = "Package not found"
                stdout = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("nonexistent")
        assert success is False
        assert "Package not found" in message
        assert was_upgraded is False

    def test_perform_pypi_update_timeout(self, monkeypatch):
        """Test handling of timeout."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("uv", 60)

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("test-package")
        assert success is False
        assert "timed out" in message.lower()
        assert was_upgraded is False

    def test_perform_pypi_update_unexpected_exception(self, monkeypatch):
        """Test handling of unexpected errors."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            raise ValueError("Unexpected error")

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("test-package")
        assert success is False
        assert "Unexpected error" in message
        assert was_upgraded is False

    def test_perform_pypi_update_empty_stderr(self, monkeypatch):
        """Test handling of failures with no stderr."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 1
                stderr = ""
                stdout = ""

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("test-package")
        assert success is False
        assert "failed" in message.lower()
        assert was_upgraded is False

    def test_local_installation_upgrades_successfully(self, monkeypatch):
        """Test that tools installed from local files can be upgraded."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.get_tool_source", lambda pkg: "local"
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stderr = ""
                stdout = "Successfully installed test-package 1.1.0"

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("test-package")

        assert success is True
        assert was_upgraded is True

    def test_pypi_installation_upgrades_successfully(self, monkeypatch):
        """Test that PyPI installations still upgrade correctly."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.is_command_available", lambda cmd: True
        )
        monkeypatch.setattr(
            "ai_rules.bootstrap.updater.get_tool_source", lambda pkg: "pypi"
        )

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stderr = ""
                stdout = "Upgraded test-package from 1.0.0 to 1.1.0"

            return Result()

        monkeypatch.setattr("ai_rules.bootstrap.updater.subprocess.run", mock_run)
        success, message, was_upgraded = perform_pypi_update("test-package")

        assert success is True
        assert was_upgraded is True
