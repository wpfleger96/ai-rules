"""Base agent class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from ai_rules.config import Config


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

    @abstractmethod
    def get_symlinks(self) -> List[Tuple[Path, Path]]:
        """Get list of (target_path, source_path) tuples for symlinks.

        Returns:
            List of tuples where:
            - target_path: Where symlink should be created (e.g., ~/CLAUDE.md)
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
