"""Goose agent implementation."""

from pathlib import Path
from typing import List, Tuple
from ai_rules.agents.base import Agent


class GooseAgent(Agent):
    """Agent for Goose configuration."""

    @property
    def name(self) -> str:
        return "Goose"

    @property
    def agent_id(self) -> str:
        return "goose"

    def get_symlinks(self) -> List[Tuple[Path, Path]]:
        """Get all Goose symlinks."""
        symlinks = []

        symlinks.append(
            (Path("~/.config/goose/.goosehints"), self.config_dir / "AGENTS.md")
        )

        config_file = self.config_dir / "goose" / "config.yaml"
        if config_file.exists():
            symlinks.append(
                (Path("~/.config/goose/config.yaml"), config_file)
            )

        return symlinks
