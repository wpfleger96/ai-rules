"""Integration tests for override commands."""

import yaml

from ai_rules.cli import main


class TestOverrideSetCommand:
    """Tests for the override set command."""

    def test_override_set_creates_config_if_missing(
        self, runner, tmp_path, monkeypatch
    ):
        """Test override set creates config file if it doesn't exist."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        result = runner.invoke(
            main, ["override", "set", "claude.model", "claude-3-opus"]
        )

        assert result.exit_code == 0
        assert config_path.exists()

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert data["settings_overrides"]["claude"]["model"] == "claude-3-opus"

    def test_override_set_with_json_value(self, runner, tmp_path, monkeypatch):
        """Test override set parses JSON values."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        result = runner.invoke(main, ["override", "set", "claude.timeout", "30"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Should be parsed as integer, not string
        assert data["settings_overrides"]["claude"]["timeout"] == 30
        assert isinstance(data["settings_overrides"]["claude"]["timeout"], int)

    def test_override_set_with_string_value(self, runner, tmp_path, monkeypatch):
        """Test override set handles string values."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        result = runner.invoke(
            main, ["override", "set", "claude.model", "my-model-name"]
        )

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert data["settings_overrides"]["claude"]["model"] == "my-model-name"

    def test_override_set_with_nested_key(self, runner, tmp_path, monkeypatch):
        """Test override set handles nested keys."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        result = runner.invoke(
            main, ["override", "set", "claude.api.endpoint", "https://api.example.com"]
        )

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert (
            data["settings_overrides"]["claude"]["api"]["endpoint"]
            == "https://api.example.com"
        )

    def test_override_set_updates_existing_value(self, runner, tmp_path, monkeypatch):
        """Test override set updates existing override."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create existing config
        existing_data = {
            "version": 1,
            "settings_overrides": {"claude": {"model": "old-model"}},
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        result = runner.invoke(main, ["override", "set", "claude.model", "new-model"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert data["settings_overrides"]["claude"]["model"] == "new-model"

    def test_override_set_supports_multiple_agents(self, runner, tmp_path, monkeypatch):
        """Test override set works for different agents."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        runner.invoke(main, ["override", "set", "claude.model", "claude-model"])
        result = runner.invoke(main, ["override", "set", "goose.model", "goose-model"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert data["settings_overrides"]["claude"]["model"] == "claude-model"
        assert data["settings_overrides"]["goose"]["model"] == "goose-model"


class TestOverrideUnsetCommand:
    """Tests for the override unset command."""

    def test_override_unset_removes_setting(self, runner, tmp_path, monkeypatch):
        """Test override unset removes a setting."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create config with overrides
        existing_data = {
            "version": 1,
            "settings_overrides": {"claude": {"model": "claude-3-opus", "timeout": 30}},
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        result = runner.invoke(main, ["override", "unset", "claude.model"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert "model" not in data["settings_overrides"]["claude"]
        assert data["settings_overrides"]["claude"]["timeout"] == 30

    def test_override_unset_removes_nested_setting(self, runner, tmp_path, monkeypatch):
        """Test override unset removes nested settings."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create config with nested overrides
        existing_data = {
            "version": 1,
            "settings_overrides": {
                "claude": {
                    "api": {"endpoint": "https://api.example.com", "key": "secret"}
                }
            },
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        result = runner.invoke(main, ["override", "unset", "claude.api.endpoint"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert "endpoint" not in data["settings_overrides"]["claude"]["api"]
        assert data["settings_overrides"]["claude"]["api"]["key"] == "secret"

    def test_override_unset_cleans_up_empty_dicts(self, runner, tmp_path, monkeypatch):
        """Test override unset removes empty nested dictionaries and agent entry."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create config with nested override (only one key)
        existing_data = {
            "version": 1,
            "settings_overrides": {
                "claude": {"api": {"endpoint": "https://api.example.com"}}
            },
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        result = runner.invoke(main, ["override", "unset", "claude.api.endpoint"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Empty "api" dict and "claude" entry should both be removed
        assert "claude" not in data.get("settings_overrides", {})

    def test_override_unset_removes_agent_when_empty(
        self, runner, tmp_path, monkeypatch
    ):
        """Test override unset removes agent entry when all overrides removed."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create config with single override
        existing_data = {
            "version": 1,
            "settings_overrides": {"claude": {"model": "claude-3-opus"}},
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        result = runner.invoke(main, ["override", "unset", "claude.model"])

        assert result.exit_code == 0

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Claude entry should be removed entirely
        assert "claude" not in data.get("settings_overrides", {})

    def test_override_unset_fails_on_missing_config(
        self, runner, tmp_path, monkeypatch
    ):
        """Test override unset fails when config doesn't exist."""
        monkeypatch.setenv("HOME", str(tmp_path))

        result = runner.invoke(main, ["override", "unset", "claude.model"])

        assert result.exit_code == 1
        assert "No user config found" in result.output

    def test_override_unset_fails_on_nonexistent_override(
        self, runner, tmp_path, monkeypatch
    ):
        """Test override unset fails when override doesn't exist."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create config without the override
        existing_data = {
            "version": 1,
            "settings_overrides": {"claude": {"timeout": 30}},
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        result = runner.invoke(main, ["override", "unset", "claude.model"])

        assert result.exit_code == 1
        assert "Override not found" in result.output


class TestOverrideListCommand:
    """Tests for the override list command."""

    def test_override_list_shows_overrides(self, runner, tmp_path, monkeypatch):
        """Test override list displays all overrides."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create config with overrides
        existing_data = {
            "version": 1,
            "settings_overrides": {
                "claude": {"model": "claude-3-opus", "timeout": 30},
                "goose": {"model": "gpt-4"},
            },
        }
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        # Need to set up a minimal repo root for Config.load()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        monkeypatch.chdir(repo_root)

        result = runner.invoke(main, ["override", "list"])

        assert result.exit_code == 0
        assert "claude:" in result.output
        assert "model:" in result.output or "model" in result.output
        assert "goose:" in result.output

    def test_override_list_shows_empty_message(self, runner, tmp_path, monkeypatch):
        """Test override list shows message when no overrides exist."""
        config_path = tmp_path / ".ai-rules-config.yaml"
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create empty config
        existing_data = {"version": 1}
        with open(config_path, "w") as f:
            yaml.dump(existing_data, f)

        # Need to set up a minimal repo root for Config.load()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        monkeypatch.chdir(repo_root)

        result = runner.invoke(main, ["override", "list"])

        assert result.exit_code == 0
        assert "No settings overrides" in result.output
