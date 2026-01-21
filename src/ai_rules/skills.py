"""Shared skills management for AI agents."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SkillMetadata:
    """Parsed SKILL.md metadata."""

    name: str
    description: str
    body: str = ""


@dataclass
class SkillItem:
    """Status of a single skill."""

    name: str
    target_path: Path
    actual_source: Path | None
    expected_source: Path | None
    is_symlink: bool
    is_managed: bool
    is_synced: bool
    is_broken: bool
    metadata: SkillMetadata | None = None


@dataclass
class SkillStatus:
    """Status of skills for an agent."""

    managed_synced: dict[str, SkillItem] = field(default_factory=dict)
    managed_pending: dict[str, SkillItem] = field(default_factory=dict)
    managed_wrong_target: dict[str, SkillItem] = field(default_factory=dict)
    unmanaged: dict[str, SkillItem] = field(default_factory=dict)


class SkillManager:
    """Manages skills for any AI agent."""

    def __init__(self, config_dir: Path, agent_id: str, user_skills_dir: Path):
        """Initialize skill manager.

        Args:
            config_dir: ai-rules config directory
            agent_id: Agent identifier (e.g., 'claude', 'goose')
            user_skills_dir: Where skills are installed (e.g., ~/.claude/skills/)
        """
        self.config_dir = config_dir
        self.agent_id = agent_id
        self.user_skills_dir = user_skills_dir.expanduser()

    @staticmethod
    def parse_skill_md(skill_dir: Path) -> SkillMetadata | None:
        """Parse SKILL.md file and extract metadata.

        Args:
            skill_dir: Path to skill directory containing SKILL.md

        Returns:
            SkillMetadata or None if parsing fails
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        content = skill_file.read_text()

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    return SkillMetadata(
                        name=frontmatter.get("name", skill_dir.name),
                        description=frontmatter.get("description", ""),
                        body=body,
                    )
                except yaml.YAMLError:
                    pass

        return SkillMetadata(name=skill_dir.name, description="", body=content)

    def _get_managed_skills(self) -> dict[str, Path]:
        """Get all managed skills from config_dir."""
        source_dir = self.config_dir / self.agent_id / "skills"
        if not source_dir.exists():
            return {}

        result = {}
        for item in sorted(source_dir.glob("*")):
            if item.is_dir():
                result[item.name] = item
        return result

    def _scan_installed_skills(self) -> dict[str, tuple[Path, Path | None, bool]]:
        """Scan user directory for installed skills.

        Returns:
            dict mapping name -> (target_path, symlink_source_or_none, is_broken)
        """
        if not self.user_skills_dir.exists():
            return {}

        result = {}
        for item in sorted(self.user_skills_dir.glob("*")):
            if not item.is_dir() and not item.is_symlink():
                continue

            name = item.name

            if item.is_symlink():
                try:
                    source = item.resolve()
                    is_broken = not source.exists()
                except (OSError, RuntimeError):
                    source = None
                    is_broken = True
                result[name] = (item, source, is_broken)
            else:
                result[name] = (item, None, False)

        return result

    def get_status(self) -> SkillStatus:
        """Get comprehensive status of skills."""
        status = SkillStatus()
        managed_sources = self._get_managed_skills()
        installed = self._scan_installed_skills()

        for name, expected_source in managed_sources.items():
            metadata = self.parse_skill_md(expected_source)

            if name in installed:
                target_path, actual_source, is_broken = installed[name]

                if is_broken:
                    status.managed_wrong_target[name] = SkillItem(
                        name=name,
                        target_path=target_path,
                        actual_source=None,
                        expected_source=expected_source,
                        is_symlink=True,
                        is_managed=True,
                        is_synced=False,
                        is_broken=True,
                        metadata=metadata,
                    )
                elif actual_source and actual_source == expected_source.resolve():
                    status.managed_synced[name] = SkillItem(
                        name=name,
                        target_path=target_path,
                        actual_source=actual_source,
                        expected_source=expected_source,
                        is_symlink=True,
                        is_managed=True,
                        is_synced=True,
                        is_broken=False,
                        metadata=metadata,
                    )
                else:
                    status.managed_wrong_target[name] = SkillItem(
                        name=name,
                        target_path=target_path,
                        actual_source=actual_source,
                        expected_source=expected_source,
                        is_symlink=actual_source is not None,
                        is_managed=True,
                        is_synced=False,
                        is_broken=False,
                        metadata=metadata,
                    )
            else:
                user_path = self.user_skills_dir / name
                status.managed_pending[name] = SkillItem(
                    name=name,
                    target_path=user_path,
                    actual_source=None,
                    expected_source=expected_source,
                    is_symlink=False,
                    is_managed=True,
                    is_synced=False,
                    is_broken=False,
                    metadata=metadata,
                )

        for name, (target_path, actual_source, is_broken) in installed.items():
            if name not in managed_sources:
                metadata = None
                if target_path.is_dir():
                    metadata = self.parse_skill_md(target_path)

                status.unmanaged[name] = SkillItem(
                    name=name,
                    target_path=target_path,
                    actual_source=actual_source,
                    expected_source=None,
                    is_symlink=actual_source is not None,
                    is_managed=False,
                    is_synced=False,
                    is_broken=is_broken,
                    metadata=metadata,
                )

        return status
