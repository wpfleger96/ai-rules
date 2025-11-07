from pathlib import Path

import pytest

from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.config import Config
from ai_rules.symlinks import create_symlink


@pytest.mark.integration
class TestInstallFlow:
    """Test end-to-end installation workflow."""

    def test_complete_install_creates_all_symlinks(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        goose = GooseAgent(test_repo, config)

        for agent in [claude, goose]:
            for target, source in agent.get_symlinks():
                target_path = Path(str(target).replace("~", str(mock_home)))
                create_symlink(target_path, source, dry_run=False, force=False)

        claude_md = mock_home / "CLAUDE.md"
        assert claude_md.is_symlink()
        assert claude_md.resolve() == (test_repo / "config" / "AGENTS.md").resolve()

        claude_settings = mock_home / ".claude" / "settings.json"
        assert claude_settings.is_symlink()

        claude_agent = mock_home / ".claude" / "agents" / "test-agent.md"
        assert claude_agent.is_symlink()

        claude_command = mock_home / ".claude" / "commands" / "test-command.md"
        assert claude_command.is_symlink()

        goose_hints = mock_home / ".config" / "goose" / ".goosehints"
        assert goose_hints.is_symlink()
        assert goose_hints.resolve() == (test_repo / "config" / "AGENTS.md").resolve()

        goose_config = mock_home / ".config" / "goose" / "config.yaml"
        assert goose_config.is_symlink()

    def test_install_creates_backups_for_existing_files(self, test_repo, mock_home):
        existing_file = mock_home / "CLAUDE.md"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.write_text("existing content")

        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        target, source = claude.get_symlinks()[0]
        target_path = Path(str(target).replace("~", str(mock_home)))

        create_symlink(target_path, source, force=True, dry_run=False)

        assert target_path.is_symlink()
        backup_files = list(mock_home.glob("CLAUDE.md.ai-rules-backup.*"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == "existing content"

    def test_dry_run_reports_changes_without_modifying_filesystem(
        self, test_repo, mock_home
    ):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)

        results = []
        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            result, message = create_symlink(
                target_path, source, dry_run=True, force=False
            )
            results.append((result, target_path))

        for result, target_path in results:
            assert not target_path.exists()

    def test_excluded_symlinks_are_skipped(self, test_repo, mock_home):
        config = Config(
            exclude_symlinks=[
                "~/.claude/settings.json",
                "~/.config/goose/config.yaml",
            ]
        )
        claude = ClaudeAgent(test_repo, config)
        goose = GooseAgent(test_repo, config)

        for agent in [claude, goose]:
            for target, source in agent.get_filtered_symlinks():
                target_path = Path(str(target).replace("~", str(mock_home)))
                create_symlink(target_path, source, dry_run=False, force=False)

        assert (mock_home / "CLAUDE.md").exists()
        assert not (mock_home / ".claude" / "settings.json").exists()
        assert (mock_home / ".config" / "goose" / ".goosehints").exists()
        assert not (mock_home / ".config" / "goose" / "config.yaml").exists()

    def test_install_with_multiple_agent_files(self, test_repo, mock_home):
        agents_dir = test_repo / "config" / "claude" / "agents"
        (agents_dir / "agent1.md").write_text("# Agent 1")
        (agents_dir / "agent2.md").write_text("# Agent 2")
        (agents_dir / "agent3.md").write_text("# Agent 3")

        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)

        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            create_symlink(target_path, source, dry_run=False, force=False)

        agent_dir = mock_home / ".claude" / "agents"
        agent_files = list(agent_dir.glob("*.md"))
        assert len(agent_files) == 4
        assert all(f.is_symlink() for f in agent_files)

    def test_install_updates_wrong_symlinks(self, test_repo, mock_home):
        wrong_source = test_repo / "wrong.txt"
        wrong_source.write_text("wrong content")

        target_path = mock_home / "CLAUDE.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(wrong_source)

        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        target, source = claude.get_symlinks()[0]
        target_path = Path(str(target).replace("~", str(mock_home)))

        result, message = create_symlink(target_path, source, force=True, dry_run=False)

        assert target_path.is_symlink()
        assert target_path.resolve() == (test_repo / "config" / "AGENTS.md").resolve()

    def test_install_leaves_correct_symlinks_unchanged(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        target, source = claude.get_symlinks()[0]
        target_path = Path(str(target).replace("~", str(mock_home)))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(source)

        original_mtime = target_path.lstat().st_mtime

        result, message = create_symlink(
            target_path, source, force=False, dry_run=False
        )

        new_mtime = target_path.lstat().st_mtime
        assert result.name == "ALREADY_CORRECT"
        assert original_mtime == new_mtime
