"""Goose agent implementation."""

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from ai_rules.agents.base import Agent

if TYPE_CHECKING:
    from ai_rules.skills import SkillStatus


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

    @cached_property
    def symlinks(self) -> list[tuple[Path, Path]]:
        """Cached list of all Goose symlinks."""
        result = []

        result.append(
            (
                Path("~/.config/goose/.goosehints"),
                self.config_dir / "goose" / ".goosehints",
            )
        )

        config_file = self.config_dir / "goose" / "config.yaml"
        if config_file.exists():
            target_file = self.config.get_settings_file_for_symlink(
                "goose", config_file
            )
            result.append((Path("~/.config/goose/config.yaml"), target_file))

        skills_dir = self.config_dir / "goose" / "skills"
        if skills_dir.exists():
            for skill_folder in sorted(skills_dir.glob("*")):
                if skill_folder.is_dir():
                    result.append(
                        (
                            Path(f"~/.config/goose/skills/{skill_folder.name}"),
                            skill_folder,
                        )
                    )

        return result

    def get_skill_status(self) -> "SkillStatus":
        """Get status of Goose skills.

        Returns:
            SkillStatus object with categorized skills
        """
        from ai_rules.skills import SkillManager

        manager = SkillManager(
            config_dir=self.config_dir,
            agent_id="goose",
            user_skills_dir=Path("~/.config/goose/skills"),
        )
        return manager.get_status()
