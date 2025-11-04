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
