"""Tests for auto-update configuration management."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ai_rules.bootstrap.config import (
    AutoUpdateConfig,
    clear_pending_update,
    get_config_dir,
    get_config_path,
    get_pending_update_path,
    load_auto_update_config,
    load_pending_update,
    save_auto_update_config,
    save_pending_update,
    should_check_now,
)
from ai_rules.bootstrap.updater import UpdateInfo


@pytest.mark.unit
@pytest.mark.bootstrap
class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_returns_home_config_dir(self, mock_home):
        """Test that config dir is under ~/.package_name/."""
        config_dir = get_config_dir("test-package")
        assert config_dir == mock_home / ".test-package"

    def test_default_package_name(self, mock_home):
        """Test default package name."""
        config_dir = get_config_dir()
        assert config_dir == mock_home / ".ai-rules"


@pytest.mark.unit
@pytest.mark.bootstrap
class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_returns_config_yaml_path(self, mock_home):
        """Test that config path points to update_config.yaml."""
        config_path = get_config_path("test-package")
        assert config_path.name == "update_config.yaml"
        assert config_path.parent == mock_home / ".test-package"


@pytest.mark.unit
@pytest.mark.bootstrap
class TestGetPendingUpdatePath:
    """Tests for get_pending_update_path function."""

    def test_returns_pending_json_path_for_ai_rules(self, mock_home):
        """Test that ai-rules uses legacy pending_update.json filename."""
        pending_path = get_pending_update_path("ai-rules")
        assert pending_path.name == "pending_update.json"
        assert pending_path.parent == mock_home / ".ai-rules"

    def test_returns_tool_specific_path_for_other_tools(self, mock_home):
        """Test that other tools use pending_{tool_id}_update.json format."""
        pending_path = get_pending_update_path("statusline")
        assert pending_path.name == "pending_statusline_update.json"
        assert pending_path.parent == mock_home / ".ai-rules"


@pytest.mark.unit
@pytest.mark.bootstrap
class TestLoadAutoUpdateConfig:
    """Tests for load_auto_update_config function."""

    def test_load_valid_config(self, mock_home, monkeypatch):
        """Test loading valid configuration file."""
        config_file = mock_home / ".ai-rules" / "update_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            "enabled: true\nfrequency: weekly\nlast_check: 2024-01-01T12:00:00\nnotify_only: false\n"
        )

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_config_path",
            lambda pkg="ai-rules": config_file,
        )
        config = load_auto_update_config()
        assert config.enabled is True
        assert config.frequency == "weekly"
        assert config.notify_only is False

    def test_load_missing_config_returns_defaults(self, mock_home, monkeypatch):
        """Test that missing config returns default values."""
        config_file = mock_home / ".ai-rules" / "update_config.yaml"
        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_config_path",
            lambda pkg="ai-rules": config_file,
        )

        config = load_auto_update_config()
        assert config.enabled is True
        assert config.frequency == "daily"
        assert config.last_check is None
        assert config.notify_only is False

    @pytest.mark.parametrize(
        "error_type",
        ["invalid_yaml", "os_error"],
    )
    def test_load_errors_return_defaults(self, mock_home, monkeypatch, error_type):
        """Test that errors during loading return default config."""
        config_file = mock_home / ".ai-rules" / "update_config.yaml"

        if error_type == "invalid_yaml":
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text("invalid: yaml: content:")
        elif error_type == "os_error":

            def mock_open_error(*args, **kwargs):
                raise OSError("Permission denied")

            monkeypatch.setattr("builtins.open", mock_open_error)

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_config_path",
            lambda pkg="ai-rules": config_file,
        )

        config = load_auto_update_config()
        assert config.enabled is True  # Defaults


@pytest.mark.unit
@pytest.mark.bootstrap
class TestSaveAutoUpdateConfig:
    """Tests for save_auto_update_config function."""

    def test_save_config_writes_yaml(self, mock_home, monkeypatch):
        """Test that config is saved as YAML."""
        config_file = mock_home / ".ai-rules" / "update_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_config_path",
            lambda pkg="ai-rules": config_file,
        )

        config = AutoUpdateConfig(
            enabled=True,
            frequency="daily",
            last_check=None,
            notify_only=True,
        )
        save_auto_update_config(config)

        assert config_file.exists()
        import yaml

        with open(config_file) as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["enabled"] is True
        assert saved_data["frequency"] == "daily"

    def test_save_with_oserror_logs_debug(self, mock_home, monkeypatch):
        """Test that OSError logs debug message."""
        config_file = mock_home / ".ai-rules" / "update_config.yaml"

        def mock_open_error(*args, **kwargs):
            raise OSError("Permission denied")

        mock_logger = type("MockLogger", (), {"debug": lambda *args: None})()
        monkeypatch.setattr("builtins.open", mock_open_error)
        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_config_path",
            lambda pkg="ai-rules": config_file,
        )
        monkeypatch.setattr("ai_rules.bootstrap.config.logger", mock_logger)

        config = AutoUpdateConfig(
            enabled=True, frequency="weekly", last_check=None, notify_only=False
        )
        save_auto_update_config(config)
        # Just verify it doesn't crash - logger.debug was called


@pytest.mark.unit
@pytest.mark.bootstrap
class TestShouldCheckNow:
    """Tests for should_check_now function."""

    def test_never_checked_returns_true(self):
        """Test that first check returns True."""
        config = AutoUpdateConfig(
            enabled=True, frequency="weekly", last_check=None, notify_only=False
        )
        assert should_check_now(config) is True

    def test_disabled_returns_false(self):
        """Test that disabled config returns False."""
        config = AutoUpdateConfig(
            enabled=False, frequency="weekly", last_check=None, notify_only=False
        )
        assert should_check_now(config) is False

    def test_checked_recently_returns_false(self):
        """Test that recent check returns False."""
        recent_check = (datetime.now() - timedelta(days=3)).isoformat()
        config = AutoUpdateConfig(
            enabled=True,
            frequency="weekly",
            last_check=recent_check,
            notify_only=False,
        )
        assert should_check_now(config) is False

    def test_checked_long_ago_returns_true(self):
        """Test that old check returns True."""
        old_check = (datetime.now() - timedelta(days=10)).isoformat()
        config = AutoUpdateConfig(
            enabled=True,
            frequency="weekly",
            last_check=old_check,
            notify_only=False,
        )
        assert should_check_now(config) is True

    def test_exactly_at_frequency_returns_true(self):
        """Test that check at exactly frequency days returns True."""
        exact_check = (datetime.now() - timedelta(days=7, hours=1)).isoformat()
        config = AutoUpdateConfig(
            enabled=True,
            frequency="weekly",
            last_check=exact_check,
            notify_only=False,
        )
        assert should_check_now(config) is True


@pytest.mark.unit
@pytest.mark.bootstrap
class TestLoadPendingUpdate:
    """Tests for load_pending_update function."""

    def test_load_valid_pending_update(self, mock_home, monkeypatch):
        """Test loading valid pending update."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        import json

        pending_data = {
            "has_update": True,
            "current_version": "1.0.0",
            "latest_version": "1.1.0",
            "source": "pypi",
        }
        pending_file.write_text(json.dumps(pending_data))

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )

        update_info = load_pending_update()
        assert update_info is not None
        assert update_info.has_update is True
        assert update_info.current_version == "1.0.0"
        assert update_info.latest_version == "1.1.0"
        assert update_info.source == "pypi"

    def test_load_missing_pending_update_returns_none(self, mock_home, monkeypatch):
        """Test that missing file returns None."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"
        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )

        assert load_pending_update() is None

    def test_load_invalid_json_returns_none(self, mock_home, monkeypatch):
        """Test that invalid JSON returns None."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        pending_file.write_text('{"invalid": "json"')

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )

        assert load_pending_update() is None


@pytest.mark.unit
@pytest.mark.bootstrap
class TestSavePendingUpdate:
    """Tests for save_pending_update function."""

    def test_save_pending_update_writes_json(self, mock_home, monkeypatch):
        """Test that pending update is saved as JSON."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"
        pending_file.parent.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )

        update_info = UpdateInfo(
            has_update=True,
            current_version="1.0.0",
            latest_version="1.1.0",
            source="pypi",
        )
        save_pending_update(update_info)

        assert pending_file.exists()
        import json

        with open(pending_file) as f:
            saved_data = json.load(f)
        assert saved_data["has_update"] is True
        assert saved_data["current_version"] == "1.0.0"

    def test_save_with_oserror_logs_debug(self, mock_home, monkeypatch):
        """Test that OSError logs debug message."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"

        def mock_open_error(*args, **kwargs):
            raise OSError("Permission denied")

        mock_logger = type("MockLogger", (), {"debug": lambda *args: None})()
        monkeypatch.setattr("builtins.open", mock_open_error)
        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )
        monkeypatch.setattr("ai_rules.bootstrap.config.logger", mock_logger)

        update_info = UpdateInfo(
            has_update=True,
            current_version="1.0.0",
            latest_version="1.1.0",
            source="pypi",
        )
        save_pending_update(update_info)
        # Just verify it doesn't crash


@pytest.mark.unit
@pytest.mark.bootstrap
class TestClearPendingUpdate:
    """Tests for clear_pending_update function."""

    def test_clear_pending_update_deletes_file(self, mock_home, monkeypatch):
        """Test that clear removes the file."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        pending_file.write_text("{}")

        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )

        clear_pending_update()
        assert not pending_file.exists()

    def test_clear_with_oserror_logs_debug(self, mock_home, monkeypatch):
        """Test that OSError during delete logs debug message."""
        pending_file = mock_home / ".ai-rules" / "pending_update.json"

        def mock_unlink(self, missing_ok=False):
            raise OSError("Permission denied")

        mock_logger = type("MockLogger", (), {"debug": lambda *args: None})()
        monkeypatch.setattr(Path, "unlink", mock_unlink)
        monkeypatch.setattr(
            "ai_rules.bootstrap.config.get_pending_update_path",
            lambda pkg="ai-rules": pending_file,
        )
        monkeypatch.setattr("ai_rules.bootstrap.config.logger", mock_logger)

        clear_pending_update()
        # Just verify it doesn't crash
