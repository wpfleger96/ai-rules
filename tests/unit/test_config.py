from pathlib import Path

import pytest
import yaml

from ai_rules.config import (
    Config,
    navigate_path,
    parse_setting_path,
    validate_override_path,
)


@pytest.mark.unit
@pytest.mark.config
class TestConfigLoading:
    """Test configuration file loading and precedence."""

    def test_loads_repo_config_only(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text(
            "version: 1\nexclude_symlinks:\n  - ~/.claude/settings.json\n"
        )

        config = Config.load(tmp_path)

        assert "~/.claude/settings.json" in config.exclude_symlinks

    def test_loads_user_config_only(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        user_config = home / ".ai-rules-config.yaml"
        user_config.write_text(
            "version: 1\nexclude_symlinks:\n  - ~/.config/goose/config.yaml\n"
        )

        config = Config.load(tmp_path)

        assert "~/.config/goose/config.yaml" in config.exclude_symlinks

    def test_both_configs_are_combined(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text(
            "version: 1\nexclude_symlinks:\n  - ~/.claude/settings.json\n"
        )

        user_config = home / ".ai-rules-config.yaml"
        user_config.write_text(
            "version: 1\nexclude_symlinks:\n  - ~/.config/goose/config.yaml\n"
        )

        config = Config.load(tmp_path)

        assert "~/.claude/settings.json" in config.exclude_symlinks
        assert "~/.config/goose/config.yaml" in config.exclude_symlinks

    def test_handles_missing_config_files(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))

        config = Config.load(tmp_path)

        assert len(config.exclude_symlinks) == 0

    def test_handles_invalid_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text("invalid: yaml: content: [[[")

        with pytest.raises(yaml.YAMLError):
            Config.load(tmp_path)


@pytest.mark.unit
@pytest.mark.config
class TestExcludeSymlinks:
    """Test symlink exclusion filtering."""

    def test_exact_match_excluded(self, tmp_path):
        config = Config(exclude_symlinks=["~/.claude/settings.json"])

        assert config.is_excluded(Path("~/.claude/settings.json"))

    def test_non_matching_path_not_excluded(self, tmp_path):
        config = Config(exclude_symlinks=["~/.claude/settings.json"])

        assert not config.is_excluded(Path("~/.claude/agents/test.md"))

    def test_empty_exclude_list_excludes_nothing(self, tmp_path):
        config = Config(exclude_symlinks=[])

        assert not config.is_excluded(Path("~/.claude/settings.json"))

    def test_path_normalization_with_tilde(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        config = Config(exclude_symlinks=["~/.claude/settings.json"])

        assert config.is_excluded(Path("~/.claude/settings.json"))
        assert config.is_excluded(home / ".claude" / "settings.json")

    def test_multiple_exclusions(self, tmp_path):
        config = Config(
            exclude_symlinks=[
                "~/.claude/settings.json",
                "~/.config/goose/config.yaml",
            ]
        )

        assert config.is_excluded(Path("~/.claude/settings.json"))
        assert config.is_excluded(Path("~/.config/goose/config.yaml"))
        assert not config.is_excluded(Path("~/.claude/agents/test.md"))

    def test_absolute_path_exclusion(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        config = Config(exclude_symlinks=[str(home / ".claude" / "settings.json")])

        assert config.is_excluded(home / ".claude" / "settings.json")

    def test_glob_pattern_matching(self, tmp_path, monkeypatch):
        """Test that glob patterns work for exclusions."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        config = Config(exclude_symlinks=["~/.claude/*.json"])

        assert config.is_excluded(Path("~/.claude/settings.json"))
        assert config.is_excluded(Path("~/.claude/debug.json"))
        assert not config.is_excluded(Path("~/.claude/agents/test.md"))

    def test_glob_pattern_with_recursive(self, tmp_path, monkeypatch):
        """Test recursive glob patterns."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        config = Config(exclude_symlinks=["~/.config/**/*.yaml"])

        assert config.is_excluded(Path("~/.config/goose/config.yaml"))
        assert config.is_excluded(Path("~/.config/deep/nested/file.yaml"))
        assert not config.is_excluded(Path("~/.config/goose/file.json"))

    def test_exact_match_preferred_over_glob(self, tmp_path, monkeypatch):
        """Test that exact matches still work when glob patterns are also present."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        config = Config(
            exclude_symlinks=[
                "~/.claude/settings.json",  # Exact
                "~/.claude/*.md",  # Glob
            ]
        )

        assert config.is_excluded(Path("~/.claude/settings.json"))
        assert config.is_excluded(Path("~/.claude/readme.md"))


@pytest.mark.unit
@pytest.mark.config
class TestSettingsOverrides:
    """Test settings override loading and merging."""

    def test_loads_settings_overrides(self, tmp_path, monkeypatch):
        """Test that settings_overrides are loaded from user config."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        user_config = home / ".ai-rules-config.yaml"
        user_config.write_text(
            """version: 1
settings_overrides:
  claude:
    model: claude-sonnet-4-5-20250929
    theme: dark
"""
        )

        config = Config.load(tmp_path)

        assert "claude" in config.settings_overrides
        assert (
            config.settings_overrides["claude"]["model"] == "claude-sonnet-4-5-20250929"
        )
        assert config.settings_overrides["claude"]["theme"] == "dark"

    def test_settings_overrides_not_in_repo_config(self, tmp_path, monkeypatch):
        """Test that settings_overrides from repo config are ignored."""
        monkeypatch.setenv("HOME", str(tmp_path / "home"))

        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text(
            """version: 1
settings_overrides:
  claude:
    model: should-be-ignored
"""
        )

        config = Config.load(tmp_path)

        assert len(config.settings_overrides) == 0

    def test_merge_settings_with_overrides(self, tmp_path):
        """Test deep merging of settings with overrides."""
        config = Config(
            settings_overrides={
                "claude": {
                    "model": "claude-sonnet-4-5-20250929",
                    "theme": "dark",
                }
            }
        )

        base_settings = {
            "model": "claude-opus-4-20250514",
            "theme": "light",
            "other": "value",
        }

        merged = config.merge_settings("claude", base_settings)

        assert merged["model"] == "claude-sonnet-4-5-20250929"
        assert merged["theme"] == "dark"
        assert merged["other"] == "value"

    def test_merge_settings_without_overrides(self, tmp_path):
        """Test that settings without overrides are returned unchanged."""
        config = Config(settings_overrides={})

        base_settings = {"model": "claude-opus-4-20250514"}

        merged = config.merge_settings("claude", base_settings)

        assert merged == base_settings

    def test_deep_merge_nested_dicts(self, tmp_path):
        """Test that nested dictionaries are merged properly."""
        config = Config(
            settings_overrides={
                "claude": {
                    "nested": {
                        "override": "new_value",
                    }
                }
            }
        )

        base_settings = {
            "nested": {
                "override": "old_value",
                "keep": "unchanged",
            },
            "top_level": "value",
        }

        merged = config.merge_settings("claude", base_settings)

        assert merged["nested"]["override"] == "new_value"
        assert merged["nested"]["keep"] == "unchanged"
        assert merged["top_level"] == "value"

    def test_build_merged_settings_creates_cache(self, tmp_path, monkeypatch):
        """Test that merged settings are written to cache."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={
                "claude": {
                    "model": "claude-sonnet-4-5-20250929",
                }
            }
        )

        cache_path = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )

        assert cache_path is not None
        assert cache_path.exists()

        import json

        with open(cache_path) as f:
            cached = json.load(f)

        assert cached["model"] == "claude-sonnet-4-5-20250929"

    def test_build_merged_settings_without_overrides_returns_none(self, tmp_path):
        """Test that no cache is created when there are no overrides."""
        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(settings_overrides={})

        cache_path = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )

        assert cache_path is None

    def test_is_cache_stale_when_cache_missing(self, tmp_path, monkeypatch):
        """Test that cache is stale when it doesn't exist."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        assert config.is_cache_stale("claude", base_settings_path, tmp_path)

    def test_is_cache_fresh_when_no_changes(self, tmp_path, monkeypatch):
        """Test that cache is fresh when nothing has changed."""
        import time

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        user_config = home / ".ai-rules-config.yaml"
        user_config.write_text("version: 1\n")

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        config.build_merged_settings("claude", base_settings_path, tmp_path)

        time.sleep(0.01)

        assert not config.is_cache_stale("claude", base_settings_path, tmp_path)

    def test_is_cache_stale_when_base_settings_updated(self, tmp_path, monkeypatch):
        """Test that cache is stale when base settings are modified."""
        import time

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        config.build_merged_settings("claude", base_settings_path, tmp_path)

        time.sleep(0.01)

        base_settings_path.write_text(
            '{"model": "claude-opus-4-20250514", "new": "value"}'
        )

        assert config.is_cache_stale("claude", base_settings_path, tmp_path)

    def test_build_merged_settings_skips_rebuild_when_fresh(
        self, tmp_path, monkeypatch
    ):
        """Test that cache rebuild is skipped when cache is fresh."""
        import time

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        cache_path1 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )
        mtime1 = cache_path1.stat().st_mtime

        time.sleep(0.01)

        cache_path2 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )
        mtime2 = cache_path2.stat().st_mtime

        assert mtime1 == mtime2

    def test_build_merged_settings_rebuilds_when_forced(self, tmp_path, monkeypatch):
        """Test that cache rebuild happens when forced."""
        import time

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        cache_path1 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )
        mtime1 = cache_path1.stat().st_mtime

        time.sleep(0.01)

        cache_path2 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path, force_rebuild=True
        )
        mtime2 = cache_path2.stat().st_mtime

        assert mtime2 > mtime1

    def test_get_settings_file_for_symlink_returns_cache_when_exists(
        self, tmp_path, monkeypatch
    ):
        """Test that get_settings_file_for_symlink returns cached file when it exists."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        cache_path = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )

        result = config.get_settings_file_for_symlink(
            "claude", base_settings_path, tmp_path
        )
        assert result == cache_path

    def test_get_settings_file_for_symlink_returns_base_when_no_cache(
        self, tmp_path, monkeypatch
    ):
        """Test that get_settings_file_for_symlink returns base file when cache doesn't exist."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        base_settings_path = tmp_path / "settings.json"
        base_settings_path.write_text('{"model": "claude-opus-4-20250514"}')

        config = Config(
            settings_overrides={"claude": {"model": "claude-sonnet-4-5-20250929"}}
        )

        result = config.get_settings_file_for_symlink(
            "claude", base_settings_path, tmp_path
        )
        assert result == base_settings_path


@pytest.mark.unit
@pytest.mark.config
class TestPathParsing:
    """Test setting path parsing with array notation."""

    def test_parse_simple_path(self):
        """Test parsing a simple path without arrays."""
        result = parse_setting_path("model")
        assert result == ["model"]

    def test_parse_nested_path(self):
        """Test parsing a nested path."""
        result = parse_setting_path("env.SOME_VAR")
        assert result == ["env", "SOME_VAR"]

    def test_parse_path_with_array_index(self):
        """Test parsing a path with array index."""
        result = parse_setting_path("hooks.SubagentStop[0].command")
        assert result == ["hooks", "SubagentStop", 0, "command"]

    def test_parse_path_with_multiple_array_indices(self):
        """Test parsing a path with multiple array indices."""
        result = parse_setting_path("hooks.SubagentStop[0].hooks[0].command")
        assert result == ["hooks", "SubagentStop", 0, "hooks", 0, "command"]

    def test_parse_path_with_nested_array_indices(self):
        """Test parsing a path with nested array indices on same key."""
        result = parse_setting_path("matrix[0][1].value")
        assert result == ["matrix", 0, 1, "value"]

    def test_parse_empty_path_raises_error(self):
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            parse_setting_path("")

    def test_parse_invalid_array_notation_raises_error(self):
        """Test that invalid array notation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid array notation"):
            parse_setting_path("hooks[invalid].command")

    def test_parse_unclosed_bracket_raises_error(self):
        """Test that unclosed bracket raises ValueError."""
        with pytest.raises(ValueError, match="Invalid array notation"):
            parse_setting_path("hooks[0.command")


@pytest.mark.unit
@pytest.mark.config
class TestPathNavigation:
    """Test navigating data structures using path components."""

    def test_navigate_simple_dict(self):
        """Test navigating a simple dictionary."""
        data = {"model": "sonnet"}
        value, success, error = navigate_path(data, ["model"])
        assert success
        assert value == "sonnet"
        assert error == ""

    def test_navigate_nested_dict(self):
        """Test navigating a nested dictionary."""
        data = {"env": {"VAR": "value"}}
        value, success, error = navigate_path(data, ["env", "VAR"])
        assert success
        assert value == "value"

    def test_navigate_array_index(self):
        """Test navigating with array index."""
        data = {"items": ["first", "second", "third"]}
        value, success, error = navigate_path(data, ["items", 0])
        assert success
        assert value == "first"

    def test_navigate_nested_array_and_dict(self):
        """Test navigating through nested arrays and dicts."""
        data = {"hooks": {"SubagentStop": [{"command": "test.py"}]}}
        value, success, error = navigate_path(
            data, ["hooks", "SubagentStop", 0, "command"]
        )
        assert success
        assert value == "test.py"

    def test_navigate_missing_key_fails(self):
        """Test that navigating to missing key fails."""
        data = {"model": "sonnet"}
        value, success, error = navigate_path(data, ["missing"])
        assert not success
        assert "not found" in error.lower()

    def test_navigate_array_index_out_of_range_fails(self):
        """Test that out of range array index fails."""
        data = {"items": ["first"]}
        value, success, error = navigate_path(data, ["items", 5])
        assert not success
        assert "out of range" in error.lower()

    def test_navigate_expected_array_but_found_dict_fails(self):
        """Test that expecting array but finding dict fails."""
        data = {"items": {"key": "value"}}
        value, success, error = navigate_path(data, ["items", 0])
        assert not success
        assert "expected array" in error.lower()

    def test_navigate_expected_dict_but_found_array_fails(self):
        """Test that expecting dict but finding array fails."""
        data = {"items": ["first", "second"]}
        value, success, error = navigate_path(data, ["items", "key"])
        assert not success
        assert "expected object" in error.lower()


@pytest.mark.unit
@pytest.mark.config
class TestPathValidation:
    """Test validation of override paths against base settings."""

    def test_validate_invalid_agent_fails(self, tmp_path):
        """Test that invalid agent name fails validation."""
        is_valid, error, warning, suggestions = validate_override_path(
            "invalid", "model", tmp_path
        )
        assert not is_valid
        assert "unknown agent" in error.lower()
        assert "claude" in suggestions
        assert "goose" in suggestions

    def test_validate_missing_settings_file_fails(self, tmp_path):
        """Test that missing settings file fails validation."""
        is_valid, error, warning, suggestions = validate_override_path(
            "claude", "model", tmp_path
        )
        assert not is_valid
        assert "no base settings file" in error.lower()

    def test_validate_valid_simple_path_succeeds(self, tmp_path):
        """Test that valid simple path succeeds."""
        settings_file = tmp_path / "config" / "claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text('{"model": "sonnet"}')

        is_valid, error, warning, suggestions = validate_override_path(
            "claude", "model", tmp_path
        )
        assert is_valid
        assert error == ""
        assert warning == ""
        assert suggestions == []

    def test_validate_valid_nested_path_succeeds(self, tmp_path):
        """Test that valid nested path succeeds."""
        settings_file = tmp_path / "config" / "claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text('{"env": {"VAR": "value"}}')

        is_valid, error, warning, suggestions = validate_override_path(
            "claude", "env.VAR", tmp_path
        )
        assert is_valid
        assert warning == ""

    def test_validate_valid_array_path_succeeds(self, tmp_path):
        """Test that valid array path succeeds."""
        settings_file = tmp_path / "config" / "claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text('{"items": ["first", "second"]}')

        is_valid, error, warning, suggestions = validate_override_path(
            "claude", "items[0]", tmp_path
        )
        assert is_valid
        assert warning == ""

    def test_validate_invalid_path_provides_suggestions(self, tmp_path):
        """Test that invalid path provides suggestions (as error)."""
        settings_file = tmp_path / "config" / "claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text('{"model": "sonnet", "theme": "dark"}')

        is_valid, error, warning, suggestions = validate_override_path(
            "claude", "invalid", tmp_path
        )
        assert not is_valid
        assert "not found" in error.lower()
        assert warning == ""
        assert "model" in suggestions
        assert "theme" in suggestions

    def test_validate_malformed_array_notation_fails(self, tmp_path):
        """Test that malformed array notation fails."""
        settings_file = tmp_path / "config" / "claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text('{"items": ["first"]}')

        is_valid, error, warning, suggestions = validate_override_path(
            "claude", "items[invalid]", tmp_path
        )
        assert not is_valid
        assert "invalid array notation" in error.lower()


@pytest.mark.unit
@pytest.mark.config
class TestDeepMergeWithArrays:
    """Test deep merge functionality with array support."""

    def test_merge_arrays_element_by_element(self):
        """Test that arrays are merged element by element."""
        config = Config()
        base = {"items": ["a", "b", "c"]}
        override = {"items": ["x", "y"]}

        result = config._deep_merge(base, override)

        assert result["items"] == ["x", "y", "c"]

    def test_merge_array_with_dict_elements(self):
        """Test merging arrays containing dicts."""
        config = Config()
        base = {
            "hooks": {
                "SubagentStop": [
                    {"command": "old.py", "type": "command"},
                    {"command": "other.py"},
                ]
            }
        }
        override = {"hooks": {"SubagentStop": [{"command": "new.py"}]}}

        result = config._deep_merge(base, override)

        assert result["hooks"]["SubagentStop"][0]["command"] == "new.py"
        assert result["hooks"]["SubagentStop"][0]["type"] == "command"
        assert result["hooks"]["SubagentStop"][1]["command"] == "other.py"

    def test_merge_extends_base_array_if_override_longer(self):
        """Test that override can extend base array."""
        config = Config()
        base = {"items": ["a"]}
        override = {"items": ["x", "y", "z"]}

        result = config._deep_merge(base, override)

        assert result["items"] == ["x", "y", "z"]

    def test_merge_preserves_base_array_elements_not_overridden(self):
        """Test that array elements not in override are preserved."""
        config = Config()
        base = {"items": ["a", "b", "c", "d"]}
        override = {"items": ["x"]}

        result = config._deep_merge(base, override)

        assert result["items"] == ["x", "b", "c", "d"]

    def test_merge_nested_arrays_in_dicts(self):
        """Test merging nested structures with arrays."""
        config = Config()
        base = {
            "hooks": {
                "SubagentStop": [{"hooks": [{"type": "command", "command": "old.py"}]}]
            }
        }
        override = {"hooks": {"SubagentStop": [{"hooks": [{"command": "new.py"}]}]}}

        result = config._deep_merge(base, override)

        hooks_elem = result["hooks"]["SubagentStop"][0]["hooks"][0]
        assert hooks_elem["command"] == "new.py"
        assert hooks_elem["type"] == "command"


class TestCacheCleanup:
    """Tests for orphaned cache cleanup functionality."""

    def test_cleanup_orphaned_cache(self, tmp_path, monkeypatch):
        """Test that orphaned cache files are removed."""
        from pathlib import Path

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(Path, "home", staticmethod(lambda: home))

        cache_dir = home / ".ai-rules" / "cache" / "claude"
        cache_dir.mkdir(parents=True)
        (cache_dir / "settings.json").write_text('{"orphaned": true}')

        config = Config(settings_overrides={})

        removed = config.cleanup_orphaned_cache(tmp_path)
        assert "claude" in removed
        assert not cache_dir.exists()

    def test_cleanup_preserves_cache_with_overrides(self, tmp_path, monkeypatch):
        """Test that cache files with active overrides are preserved."""
        from pathlib import Path

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(Path, "home", staticmethod(lambda: home))

        cache_dir = home / ".ai-rules" / "cache" / "claude"
        cache_dir.mkdir(parents=True)
        (cache_dir / "settings.json").write_text('{"active": true}')

        config = Config(settings_overrides={"claude": {"model": "test"}})

        removed = config.cleanup_orphaned_cache(tmp_path)
        assert removed == []
        assert cache_dir.exists()

    def test_cleanup_when_no_cache_dir(self, tmp_path, monkeypatch):
        """Test cleanup when cache directory doesn't exist."""
        from pathlib import Path

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(Path, "home", staticmethod(lambda: home))

        config = Config(settings_overrides={})
        removed = config.cleanup_orphaned_cache(tmp_path)
        assert removed == []
