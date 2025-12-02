"""Base agent class."""

from abc import ABC, abstractmethod
from pathlib import Path

from ai_rules.config import Config


class Agent(ABC):
    """Base class for AI agent configuration managers."""

    def __init__(self, config_dir: Path, config: Config):
        self.config_dir = config_dir
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
    def get_symlinks(self) -> list[tuple[Path, Path]]:
        """Get list of (target_path, source_path) tuples for symlinks.

        Returns:
            List of tuples where:
            - target_path: Where symlink should be created (e.g., ~/.CLAUDE.md)
            - source_path: What symlink should point to (e.g., repo/config/AGENTS.md)
        """
        pass

    def get_filtered_symlinks(self) -> list[tuple[Path, Path]]:
        """Get symlinks filtered by config exclusions."""
        all_symlinks = self.get_symlinks()
        return [
            (target, source)
            for target, source in all_symlinks
            if not self.config.is_excluded(str(target))
        ]

    def get_deprecated_symlinks(self) -> list[Path]:
        """Get list of deprecated symlink paths that should be cleaned up.

        Returns:
            List of paths that were previously used but are now deprecated.
            These will be removed during install if they point to our config files.
        """
        return []
