"""Claude Code agent implementation."""

from functools import cached_property
from pathlib import Path

from ai_rules.agents.base import Agent
from ai_rules.mcp import MCPManager, MCPStatus, OperationResult


class ClaudeAgent(Agent):
    """Agent for Claude Code configuration."""

    DEPRECATED_SYMLINKS: list[Path] = [
        Path("~/CLAUDE.md"),
    ]

    @property
    def name(self) -> str:
        return "Claude Code"

    @property
    def agent_id(self) -> str:
        return "claude"

    @property
    def config_file_name(self) -> str:
        return "settings.json"

    @property
    def config_file_format(self) -> str:
        return "json"

    @cached_property
    def symlinks(self) -> list[tuple[Path, Path]]:
        """Cached list of all Claude Code symlinks including dynamic agents/commands."""
        result = []

        result.append(
            (Path("~/.claude/CLAUDE.md"), self.config_dir / "claude" / "CLAUDE.md")
        )

        settings_file = self.config_dir / "claude" / "settings.json"
        if settings_file.exists():
            target_file = self.config.get_settings_file_for_symlink(
                "claude", settings_file
            )
            result.append((Path("~/.claude/settings.json"), target_file))

        agents_dir = self.config_dir / "claude" / "agents"
        if agents_dir.exists():
            for agent_file in sorted(agents_dir.glob("*.md")):
                result.append(
                    (
                        Path(f"~/.claude/agents/{agent_file.name}"),
                        agent_file,
                    )
                )

        commands_dir = self.config_dir / "claude" / "commands"
        if commands_dir.exists():
            for command_file in sorted(commands_dir.glob("*.md")):
                result.append(
                    (
                        Path(f"~/.claude/commands/{command_file.name}"),
                        command_file,
                    )
                )

        skills_dir = self.config_dir / "claude" / "skills"
        if skills_dir.exists():
            for skill_folder in sorted(skills_dir.glob("*")):
                if skill_folder.is_dir():
                    result.append(
                        (
                            Path(f"~/.claude/skills/{skill_folder.name}"),
                            skill_folder,
                        )
                    )

        hooks_dir = self.config_dir / "claude" / "hooks"
        if hooks_dir.exists():
            for hook_file in sorted(hooks_dir.glob("*.py")):
                result.append(
                    (
                        Path(f"~/.claude/hooks/{hook_file.name}"),
                        hook_file,
                    )
                )

        return result

    def get_deprecated_symlinks(self) -> list[Path]:
        """Return deprecated symlink locations for cleanup."""
        return self.DEPRECATED_SYMLINKS

    def install_mcps(
        self, force: bool = False, dry_run: bool = False
    ) -> tuple[OperationResult, str, list[str]]:
        """Install managed MCPs into ~/.claude.json.

        Args:
            force: Skip confirmation prompts
            dry_run: Don't actually modify files

        Returns:
            Tuple of (result, message, conflicts_list)
        """
        manager = MCPManager()
        return manager.install_mcps(self.config_dir, self.config, force, dry_run)

    def uninstall_mcps(
        self, force: bool = False, dry_run: bool = False
    ) -> tuple[OperationResult, str]:
        """Uninstall managed MCPs from ~/.claude.json.

        Args:
            force: Skip confirmation prompts
            dry_run: Don't actually modify files

        Returns:
            Tuple of (result, message)
        """
        manager = MCPManager()
        return manager.uninstall_mcps(force, dry_run)

    def get_mcp_status(self) -> MCPStatus:
        """Get status of managed and unmanaged MCPs.

        Returns:
            MCPStatus object with categorized MCPs
        """
        manager = MCPManager()
        return manager.get_status(self.config_dir, self.config)
