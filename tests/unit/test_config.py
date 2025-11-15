from pathlib import Path

import pytest

from ai_rules.config import Config


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

    def test_handles_empty_config_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text("")

        config = Config.load(tmp_path)

        assert len(config.exclude_symlinks) == 0

    def test_handles_invalid_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text("invalid: yaml: content: [[[")

        with pytest.raises(Exception):
            Config.load(tmp_path)

    def test_handles_config_without_exclude_symlinks(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        repo_config = tmp_path / ".ai-rules-config.yaml"
        repo_config.write_text("version: 1\n")

        config = Config.load(tmp_path)

        assert len(config.exclude_symlinks) == 0


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

        # Create base settings
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

        with open(cache_path, "r") as f:
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

        # Build cache
        config.build_merged_settings("claude", base_settings_path, tmp_path)

        # Wait a moment to ensure different timestamps
        time.sleep(0.01)

        # Cache should be fresh
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

        # Build cache
        config.build_merged_settings("claude", base_settings_path, tmp_path)

        # Wait to ensure different timestamp
        time.sleep(0.01)

        # Modify base settings
        base_settings_path.write_text(
            '{"model": "claude-opus-4-20250514", "new": "value"}'
        )

        # Cache should now be stale
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

        # Build cache first time
        cache_path1 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )
        mtime1 = cache_path1.stat().st_mtime

        # Wait a moment
        time.sleep(0.01)

        # Build again - should use existing cache
        cache_path2 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )
        mtime2 = cache_path2.stat().st_mtime

        # Cache file should not have been modified (same timestamp)
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

        # Build cache first time
        cache_path1 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )
        mtime1 = cache_path1.stat().st_mtime

        # Wait a moment
        time.sleep(0.01)

        # Build again with force_rebuild
        cache_path2 = config.build_merged_settings(
            "claude", base_settings_path, tmp_path, force_rebuild=True
        )
        mtime2 = cache_path2.stat().st_mtime

        # Cache file should have been rebuilt (different timestamp)
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

        # Build cache
        cache_path = config.build_merged_settings(
            "claude", base_settings_path, tmp_path
        )

        # get_settings_file_for_symlink should return cache path
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

        # Don't build cache, just check what file would be used
        result = config.get_settings_file_for_symlink(
            "claude", base_settings_path, tmp_path
        )
        assert result == base_settings_path
