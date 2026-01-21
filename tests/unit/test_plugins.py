"""Tests for plugin management functionality."""

from unittest.mock import patch

from ai_rules.plugins import (
    OperationResult,
    PluginConfig,
    PluginManager,
)


class TestPluginManager:
    def test_load_installed_plugins_file_not_exists(self, tmp_path):
        """Returns default when file doesn't exist."""
        manager = PluginManager()
        with patch.object(
            manager, "INSTALLED_PLUGINS_PATH", tmp_path / "nonexistent.json"
        ):
            result = manager.load_installed_plugins()
            assert result == {"version": 2, "plugins": {}}

    def test_get_status_shows_pending_plugins(self):
        """Status shows plugins not yet installed."""
        manager = PluginManager()
        with patch.object(
            manager,
            "load_installed_plugins",
            return_value={"version": 2, "plugins": {}},
        ):
            with patch.object(manager, "load_known_marketplaces", return_value=[]):
                status = manager.get_status(
                    [PluginConfig(name="test", marketplace="official")], []
                )
                assert len(status.pending) == 1
                assert status.pending[0]["name"] == "test"

    def test_get_status_shows_installed_plugins(self):
        """Status shows installed plugins."""
        manager = PluginManager()
        with patch.object(
            manager,
            "load_installed_plugins",
            return_value={
                "version": 2,
                "plugins": {"test@official": {"enabled": True}},
            },
        ):
            with patch.object(manager, "load_known_marketplaces", return_value=[]):
                status = manager.get_status(
                    [PluginConfig(name="test", marketplace="official")], []
                )
                assert "test@official" in status.installed
                assert len(status.pending) == 0

    def test_get_status_shows_extra_plugins(self):
        """Status shows unmanaged plugins."""
        manager = PluginManager()
        with patch.object(
            manager,
            "load_installed_plugins",
            return_value={"version": 2, "plugins": {"extra-plugin": {"enabled": True}}},
        ):
            with patch.object(manager, "load_known_marketplaces", return_value=[]):
                status = manager.get_status([], [])
                assert "extra-plugin" in status.extra

    def test_sync_returns_error_when_cli_unavailable(self):
        """Sync returns error when claude CLI not found."""
        manager = PluginManager()
        with patch.object(manager, "is_cli_available", return_value=False):
            result, msg, warnings = manager.sync_plugins([], [])
            assert result == OperationResult.ERROR
            assert "CLI not found" in msg

    def test_install_plugin_dry_run(self):
        """Install plugin in dry run mode."""
        manager = PluginManager()
        result, msg = manager.install_plugin("test", "official", dry_run=True)
        assert result == OperationResult.DRY_RUN
        assert "Would install" in msg

    def test_add_marketplace_dry_run(self):
        """Add marketplace in dry run mode."""
        manager = PluginManager()
        result, msg = manager.add_marketplace(
            "https://github.com/test/repo", dry_run=True
        )
        assert result == OperationResult.DRY_RUN
        assert "Would add marketplace" in msg

    def test_plugin_config_key_property(self):
        """PluginConfig.key returns correct format."""
        config = PluginConfig(name="test-plugin", marketplace="my-marketplace")
        assert config.key == "test-plugin@my-marketplace"

    def test_load_known_marketplaces_file_not_exists(self, tmp_path):
        """Returns empty list when file doesn't exist."""
        manager = PluginManager()
        with patch.object(
            manager, "KNOWN_MARKETPLACES_PATH", tmp_path / "nonexistent.json"
        ):
            result = manager.load_known_marketplaces()
            assert result == []

    def test_load_known_marketplaces_malformed_json(self, tmp_path):
        """Returns empty list when JSON is malformed."""
        manager = PluginManager()
        bad_json_file = tmp_path / "known_marketplaces.json"
        bad_json_file.write_text("{ invalid json }")
        with patch.object(manager, "KNOWN_MARKETPLACES_PATH", bad_json_file):
            result = manager.load_known_marketplaces()
            assert result == []

    def test_get_status_shows_missing_marketplaces(self):
        """Status shows marketplaces not yet added."""
        from ai_rules.plugins import MarketplaceConfig

        manager = PluginManager()
        with patch.object(
            manager,
            "load_installed_plugins",
            return_value={"version": 2, "plugins": {}},
        ):
            with patch.object(manager, "load_known_marketplaces", return_value=[]):
                status = manager.get_status(
                    [],
                    [MarketplaceConfig(name="test-mp", source="user/repo")],
                )
                assert len(status.marketplaces_missing) == 1
                assert status.marketplaces_missing[0]["name"] == "test-mp"
                assert status.marketplaces_missing[0]["source"] == "user/repo"
