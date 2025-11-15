import pytest

from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.agents.shared import SharedAgent
from ai_rules.config import Config, ProjectConfig


@pytest.mark.unit
@pytest.mark.agents
class TestClaudeAgent:
    """Test Claude agent symlink discovery and filtering."""

    def test_discovers_all_symlinks(self, test_repo):
        agent = ClaudeAgent(test_repo, Config(exclude_symlinks=[]))

        symlinks = agent.get_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/CLAUDE.md" in targets
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
        assert "~/CLAUDE.md" in targets
        assert "~/.claude/commands/test-command.md" in targets


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


@pytest.mark.unit
@pytest.mark.agents
class TestSharedAgent:
    """Test Shared agent symlink discovery and filtering."""

    def test_discovers_all_symlinks(self, test_repo):
        agent = SharedAgent(test_repo, Config(exclude_symlinks=[]))

        symlinks = agent.get_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/AGENTS.md" in targets
        assert len(targets) == 1

    def test_excludes_filtered_symlinks(self, test_repo):
        config = Config(exclude_symlinks=["~/AGENTS.md"])
        agent = SharedAgent(test_repo, config)

        symlinks = agent.get_filtered_symlinks()

        targets = [str(target) for target, _ in symlinks]
        assert "~/AGENTS.md" not in targets
        assert len(targets) == 0

    def test_project_symlinks(self, test_repo, tmp_path):
        config = Config()
        agent = SharedAgent(test_repo, config)

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        project = ProjectConfig(name="test-project", path=project_dir)

        project_agents_file = (
            test_repo / "config" / "projects" / "test-project" / "AGENTS.md"
        )
        project_agents_file.parent.mkdir(parents=True, exist_ok=True)
        project_agents_file.write_text("# Project-specific rules")

        symlinks = agent.get_project_symlinks(project)

        targets = [str(target) for target, _ in symlinks]
        assert len(targets) == 1
        assert str(project_dir / "AGENTS.md") in targets

    def test_project_symlinks_when_file_missing(self, test_repo, tmp_path):
        config = Config()
        agent = SharedAgent(test_repo, config)

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        project = ProjectConfig(name="test-project", path=project_dir)

        symlinks = agent.get_project_symlinks(project)

        assert len(symlinks) == 0
