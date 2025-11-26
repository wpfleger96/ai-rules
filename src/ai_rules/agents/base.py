"""Base agent class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple

from ai_rules.config import Config, ProjectConfig


class Agent(ABC):
    """Base class for AI agent configuration managers."""

    def __init__(self, repo_root: Path, config: Config):
        self.repo_root = repo_root
        self.config_dir = repo_root / "config"
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the agent."""
        pass

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Short identifier for the agent (e.g., 'claude', 'goose')."""
        pass

    @property
    @abstractmethod
    def config_file_name(self) -> str:
        """Config file name for the agent (e.g., 'settings.json', 'config.yaml')."""
        pass

    @property
    @abstractmethod
    def config_file_format(self) -> str:
        """Config file format ('json' or 'yaml')."""
        pass

    @abstractmethod
    def get_symlinks(self) -> List[Tuple[Path, Path]]:
        """Get list of (target_path, source_path) tuples for symlinks.

        Returns:
            List of tuples where:
            - target_path: Where symlink should be created (e.g., ~/.CLAUDE.md)
            - source_path: What symlink should point to (e.g., repo/config/AGENTS.md)
        """
        pass

    def get_filtered_symlinks(self) -> List[Tuple[Path, Path]]:
        """Get symlinks filtered by config exclusions."""
        all_symlinks = self.get_symlinks()
        return [
            (target, source)
            for target, source in all_symlinks
            if not self.config.is_excluded(str(target))
        ]

    def get_deprecated_symlinks(self) -> List[Path]:
        """Get list of deprecated symlink paths that should be cleaned up.

        Returns:
            List of paths that were previously used but are now deprecated.
            These will be removed during install if they point to our config files.
        """
        return []

    @abstractmethod
    def get_project_symlinks(self, project: ProjectConfig) -> List[Tuple[Path, Path]]:
        """Get list of (target_path, source_path) tuples for project-level symlinks.

        Args:
            project: Project configuration

        Returns:
            List of tuples where:
            - target_path: Where symlink should be created in the project (e.g., <project>/CLAUDE.md)
            - source_path: What symlink should point to (e.g., repo/config/projects/<name>/AGENTS.md)
        """
        pass

    def get_all_project_symlinks(self) -> Dict[str, List[Tuple[Path, Path]]]:
        """Get all project symlinks grouped by project name, filtered by exclusions.

        Returns:
            Dictionary mapping project names to lists of (target_path, source_path) tuples
        """
        result = {}
        for project_name, project in self.config.projects.items():
            symlinks = self.get_project_symlinks(project)
            filtered_symlinks = [
                (target, source)
                for target, source in symlinks
                if not self.config.is_project_excluded(project_name, str(target))
            ]
            if filtered_symlinks:
                result[project_name] = filtered_symlinks
        return result
