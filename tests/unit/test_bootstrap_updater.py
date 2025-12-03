"""Tests for update checking and application utilities."""

import json
import subprocess
import urllib.error

import pytest

from ai_rules.bootstrap.installer import UV_NOT_FOUND_ERROR
from ai_rules.bootstrap.updater import check_pypi_updates, perform_pypi_update


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

    def test_check_pypi_handles_missing_version_key(self, monkeypatch):
        """Test handling of malformed PyPI response."""

        class MockResponse:
            def read(self):
                return json.dumps({"info": {}}).encode()

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

    def test_check_pypi_handles_json_decode_error(self, monkeypatch):
        """Test handling of invalid JSON response."""

        class MockResponse:
            def read(self):
                return b"invalid json"

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
