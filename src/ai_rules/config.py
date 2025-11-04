"""Configuration loading and management."""

from pathlib import Path
from typing import List, Optional
import yaml


class Config:
    """Configuration for ai-rules tool."""

    def __init__(self, exclude_symlinks: Optional[List[str]] = None):
        self.exclude_symlinks = set(exclude_symlinks or [])

    @classmethod
    def load(cls, repo_root: Path) -> "Config":
        """Load configuration from available config files.

        Checks in order:
        1. ~/.ai-rules-config.yaml (user-specific)
        2. <repo_root>/.ai-rules-config.yaml (repo default)
        3. Empty config if neither exists
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"
        repo_config_path = repo_root / ".ai-rules-config.yaml"

        exclude_symlinks = []

        for config_path in [user_config_path, repo_config_path]:
            if config_path.exists():
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f) or {}
                    exclude_symlinks.extend(data.get("exclude_symlinks", []))

        return cls(exclude_symlinks=exclude_symlinks)

    def is_excluded(self, symlink_target: str) -> bool:
        """Check if a symlink target is excluded."""
        normalized = Path(symlink_target).expanduser().as_posix()
        return any(
            normalized == Path(excl).expanduser().as_posix()
            for excl in self.exclude_symlinks
        )
