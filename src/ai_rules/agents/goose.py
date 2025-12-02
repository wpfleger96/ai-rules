"""Goose agent implementation."""

from pathlib import Path

from ai_rules.agents.base import Agent


class GooseAgent(Agent):
    """Agent for Goose configuration."""

    @property
    def name(self) -> str:
        return "Goose"

    @property
    def agent_id(self) -> str:
        return "goose"

    @property
    def config_file_name(self) -> str:
        return "config.yaml"

    @property
    def config_file_format(self) -> str:
        return "yaml"

    def get_symlinks(self) -> list[tuple[Path, Path]]:
        """Get all Goose symlinks."""
        symlinks = []

        symlinks.append(
            (Path("~/.config/goose/.goosehints"), self.config_dir / "AGENTS.md")
        )

        config_file = self.config_dir / "goose" / "config.yaml"
        if config_file.exists():
            target_file = self.config.get_settings_file_for_symlink(
                "goose", config_file, self.repo_root
            )
            symlinks.append((Path("~/.config/goose/config.yaml"), target_file))

        return symlinks
