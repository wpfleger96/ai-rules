"""Shared agent implementation for agent-agnostic configurations."""

from pathlib import Path
from typing import List, Tuple
from ai_rules.agents.base import Agent
from ai_rules.config import ProjectConfig


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

    def get_symlinks(self) -> List[Tuple[Path, Path]]:
        """Get shared symlinks for agent-agnostic configurations."""
        symlinks = []

        symlinks.append((Path("~/AGENTS.md"), self.config_dir / "AGENTS.md"))

        return symlinks

    def get_project_symlinks(self, project: ProjectConfig) -> List[Tuple[Path, Path]]:
        """Get shared symlinks for a specific project.

        Creates symlink at <project>/AGENTS.md pointing to config/projects/<name>/AGENTS.md
        """
        symlinks = []

        project_agents_file = self.config_dir / "projects" / project.name / "AGENTS.md"
        if project_agents_file.exists():
            target = project.path / "AGENTS.md"
            symlinks.append((target, project_agents_file))

        return symlinks
