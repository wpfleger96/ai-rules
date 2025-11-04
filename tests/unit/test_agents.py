from pathlib import Path

import pytest

from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.config import Config


@pytest.mark.unit
@pytest.mark.agents
class TestClaudeAgent:
    """Test Claude agent symlink discovery and filtering."""

    def test_discovers_all_symlinks(self, test_repo):
        agent = ClaudeAgent(test_repo, Config(exclude_symlinks=[]))

        symlinks = agent.get_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/.CLAUDE.md" in targets
        assert "~/.claude/settings.json" in targets
        assert "~/.claude/agents/test-agent.md" in targets
        assert "~/.claude/commands/test-command.md" in targets

    def test_dynamic_discovery_of_multiple_agents(self, test_repo):
        agents_dir = test_repo / "config" / "claude" / "agents"
        (agents_dir / "another-agent.md").write_text("# Another Agent")
        (agents_dir / "third-agent.md").write_text("# Third Agent")

        agent = ClaudeAgent(test_repo, Config(exclude_symlinks=[]))
        symlinks = agent.get_symlinks()

        agent_targets = [
            str(target) for target, _ in symlinks if "/agents/" in str(target)
        ]
        assert len(agent_targets) == 3
        assert "~/.claude/agents/test-agent.md" in agent_targets
        assert "~/.claude/agents/another-agent.md" in agent_targets
        assert "~/.claude/agents/third-agent.md" in agent_targets

    def test_dynamic_discovery_of_multiple_commands(self, test_repo):
        commands_dir = test_repo / "config" / "claude" / "commands"
        (commands_dir / "another-command.md").write_text("# Another Command")

        agent = ClaudeAgent(test_repo, Config(exclude_symlinks=[]))
        symlinks = agent.get_symlinks()

        command_targets = [
            str(target) for target, _ in symlinks if "/commands/" in str(target)
        ]
        assert len(command_targets) == 2
        assert "~/.claude/commands/test-command.md" in command_targets
        assert "~/.claude/commands/another-command.md" in command_targets

    def test_handles_missing_agents_directory(self, tmp_path):
        repo_root = tmp_path / "test-repo"
        repo_root.mkdir()
        config_dir = repo_root / "config"
        config_dir.mkdir()
        (config_dir / "AGENTS.md").write_text("# Test")
        claude_dir = config_dir / "claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text("{}")

        agent = ClaudeAgent(repo_root, Config(exclude_symlinks=[]))
        symlinks = agent.get_symlinks()

        agent_targets = [
            str(target) for target, _ in symlinks if "/agents/" in str(target)
        ]
        assert len(agent_targets) == 0

    def test_handles_missing_commands_directory(self, tmp_path):
        repo_root = tmp_path / "test-repo"
        repo_root.mkdir()
        config_dir = repo_root / "config"
        config_dir.mkdir()
        (config_dir / "AGENTS.md").write_text("# Test")
        claude_dir = config_dir / "claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text("{}")

        agent = ClaudeAgent(repo_root, Config(exclude_symlinks=[]))
        symlinks = agent.get_symlinks()

        command_targets = [
            str(target) for target, _ in symlinks if "/commands/" in str(target)
        ]
        assert len(command_targets) == 0

    def test_excludes_filtered_symlinks(self, test_repo):
        config = Config(
            exclude_symlinks=[
                "~/.claude/settings.json",
                "~/.claude/agents/test-agent.md",
            ]
        )
        agent = ClaudeAgent(test_repo, config)

        symlinks = agent.get_filtered_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/.claude/settings.json" not in targets
        assert "~/.claude/agents/test-agent.md" not in targets
        assert "~/.CLAUDE.md" in targets
        assert "~/.claude/commands/test-command.md" in targets

    def test_all_sources_point_to_existing_files(self, test_repo):
        agent = ClaudeAgent(test_repo, Config(exclude_symlinks=[]))

        symlinks = agent.get_symlinks()

        for _, source in symlinks:
            assert source.exists(), f"Source file does not exist: {source}"


@pytest.mark.unit
@pytest.mark.agents
class TestGooseAgent:
    """Test Goose agent symlink discovery and filtering."""

    def test_discovers_all_symlinks(self, test_repo):
        agent = GooseAgent(test_repo, Config(exclude_symlinks=[]))

        symlinks = agent.get_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/.config/goose/.goosehints" in targets
        assert "~/.config/goose/config.yaml" in targets
        assert len(targets) == 2

    def test_excludes_filtered_symlinks(self, test_repo):
        config = Config(exclude_symlinks=["~/.config/goose/config.yaml"])
        agent = GooseAgent(test_repo, config)

        symlinks = agent.get_filtered_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/.config/goose/config.yaml" not in targets
        assert "~/.config/goose/.goosehints" in targets

    def test_all_sources_point_to_existing_files(self, test_repo):
        agent = GooseAgent(test_repo, Config(exclude_symlinks=[]))

        symlinks = agent.get_symlinks()

        for _, source in symlinks:
            assert source.exists(), f"Source file does not exist: {source}"


@pytest.mark.unit
@pytest.mark.agents
class TestAgentProperties:
    """Test agent identity properties."""

    def test_claude_agent_properties(self, test_repo):
        agent = ClaudeAgent(test_repo, Config(exclude_symlinks=[]))

        assert agent.name == "Claude Code"
        assert agent.agent_id == "claude"

    def test_goose_agent_properties(self, test_repo):
        agent = GooseAgent(test_repo, Config(exclude_symlinks=[]))

        assert agent.name == "Goose"
        assert agent.agent_id == "goose"
