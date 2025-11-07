"""Claude Code agent implementation."""

from pathlib import Path
from typing import List, Tuple
from ai_rules.agents.base import Agent


class ClaudeAgent(Agent):
    """Agent for Claude Code configuration."""

    @property
    def name(self) -> str:
        return "Claude Code"

    @property
    def agent_id(self) -> str:
        return "claude"

    def get_symlinks(self) -> List[Tuple[Path, Path]]:
        """Get all Claude Code symlinks including dynamic agents/commands."""
        symlinks = []

        symlinks.append((Path("~/CLAUDE.md"), self.config_dir / "AGENTS.md"))

        settings_file = self.config_dir / "claude" / "settings.json"
        if settings_file.exists():
            symlinks.append((Path("~/.claude/settings.json"), settings_file))

        agents_dir = self.config_dir / "claude" / "agents"
        if agents_dir.exists():
            for agent_file in sorted(agents_dir.glob("*.md")):
                symlinks.append(
                    (
                        Path(f"~/.claude/agents/{agent_file.name}"),
                        agent_file,
                    )
                )

        commands_dir = self.config_dir / "claude" / "commands"
        if commands_dir.exists():
            for command_file in sorted(commands_dir.glob("*.md")):
                symlinks.append(
                    (
                        Path(f"~/.claude/commands/{command_file.name}"),
                        command_file,
                    )
                )

        return symlinks
