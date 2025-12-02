"""Shared agent implementation for agent-agnostic configurations."""

from functools import cached_property
from pathlib import Path

from ai_rules.agents.base import Agent


class SharedAgent(Agent):
    """Agent for shared configurations that both Claude Code and Goose respect."""

    @property
    def name(self) -> str:
        return "Shared"

    @property
    def agent_id(self) -> str:
        return "shared"

    @property
    def config_file_name(self) -> str:
        return ""

    @property
    def config_file_format(self) -> str:
        return ""

    @cached_property
    def symlinks(self) -> list[tuple[Path, Path]]:
        """Cached list of shared symlinks for agent-agnostic configurations."""
        result = []

        result.append((Path("~/AGENTS.md"), self.config_dir / "AGENTS.md"))

        return result
