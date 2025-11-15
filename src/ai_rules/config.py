"""Configuration loading and management."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import copy
import json
import yaml
from fnmatch import fnmatch


class ProjectConfig:
    """Configuration for a single project."""

    def __init__(
        self, name: str, path: str, exclude_symlinks: Optional[List[str]] = None
    ):
        self.name = name
        self.path = Path(path).expanduser().resolve()
        self.exclude_symlinks = set(exclude_symlinks or [])

    def is_excluded(self, symlink_target: str) -> bool:
        """Check if a symlink target is excluded for this project.

        Supports both exact paths and glob patterns (e.g., ~/.claude/*.json).
        """
        normalized = Path(symlink_target).expanduser().as_posix()
        for excl in self.exclude_symlinks:
            # Try exact match first (faster)
            excl_normalized = Path(excl).expanduser().as_posix()
            if normalized == excl_normalized:
                return True
            # Try glob pattern matching
            if fnmatch(normalized, excl_normalized):
                return True
        return False


class Config:
    """Configuration for ai-rules tool."""

    def __init__(
        self,
        exclude_symlinks: Optional[List[str]] = None,
        projects: Optional[Dict[str, ProjectConfig]] = None,
        settings_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.exclude_symlinks = set(exclude_symlinks or [])
        self.projects = projects or {}
        self.settings_overrides = settings_overrides or {}

    @classmethod
    def load(cls, repo_root: Path) -> "Config":
        """Load configuration from available config files.

        Checks in order:
        1. ~/.ai-rules-config.yaml (user-specific) - for projects, user exclusions, and settings overrides
        2. <repo_root>/.ai-rules-config.yaml (repo default) - for global exclusions
        3. Empty config if neither exists

        Note: Projects and settings_overrides are only loaded from user config, not repo config.
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"
        repo_config_path = repo_root / ".ai-rules-config.yaml"

        exclude_symlinks = []
        projects = {}
        settings_overrides = {}

        # Load user config (can contain projects, exclusions, and settings overrides)
        if user_config_path.exists():
            with open(user_config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                exclude_symlinks.extend(data.get("exclude_symlinks", []))

                # Load project configurations
                projects_data = data.get("projects", {})
                for project_name, project_data in projects_data.items():
                    if isinstance(project_data, dict):
                        project_path = project_data.get("path")
                        project_exclusions = project_data.get("exclude_symlinks", [])

                        if not project_path:
                            raise ValueError(
                                f"Project '{project_name}' is missing 'path' field"
                            )

                        projects[project_name] = ProjectConfig(
                            name=project_name,
                            path=project_path,
                            exclude_symlinks=project_exclusions,
                        )

                # Load settings overrides
                settings_overrides = data.get("settings_overrides", {})

        # Load repo config (only for global exclusions, not projects or overrides)
        if repo_config_path.exists():
            with open(repo_config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                exclude_symlinks.extend(data.get("exclude_symlinks", []))

        return cls(
            exclude_symlinks=exclude_symlinks,
            projects=projects,
            settings_overrides=settings_overrides,
        )

    def is_excluded(self, symlink_target: str) -> bool:
        """Check if a symlink target is globally excluded.

        Supports both exact paths and glob patterns (e.g., ~/.claude/*.json).
        """
        normalized = Path(symlink_target).expanduser().as_posix()
        for excl in self.exclude_symlinks:
            # Try exact match first (faster)
            excl_normalized = Path(excl).expanduser().as_posix()
            if normalized == excl_normalized:
                return True
            # Try glob pattern matching
            if fnmatch(normalized, excl_normalized):
                return True
        return False

    def is_project_excluded(self, project_name: str, symlink_target: str) -> bool:
        """Check if a symlink target is excluded for a specific project.

        Combines global exclusions and project-specific exclusions.
        """
        # Check global exclusions
        if self.is_excluded(symlink_target):
            return True

        # Check project-specific exclusions
        project = self.projects.get(project_name)
        if project:
            return project.is_excluded(symlink_target)

        return False

    @staticmethod
    def get_cache_dir() -> Path:
        """Get the cache directory for merged settings."""
        cache_dir = Path.home() / ".ai-rules" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override values taking precedence.

        Uses deep copy to prevent mutation of the base dictionary.
        """
        result = copy.deepcopy(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def merge_settings(
        self, agent: str, base_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge base settings with overrides for a specific agent.

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings: Base settings dictionary from repo

        Returns:
            Merged settings dictionary with overrides applied
        """
        if agent not in self.settings_overrides:
            return base_settings

        return self._deep_merge(base_settings, self.settings_overrides[agent])

    def get_merged_settings_path(self, agent: str, repo_root: Path) -> Optional[Path]:
        """Get the path to cached merged settings for an agent.

        Returns None if agent has no overrides (should use repo file directly).

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            repo_root: Repository root path

        Returns:
            Path to cached merged settings file, or None if no overrides exist
        """
        if agent not in self.settings_overrides:
            return None

        cache_dir = self.get_cache_dir() / agent
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "settings.json"

    def get_settings_file_for_symlink(
        self, agent: str, base_settings_path: Path, repo_root: Path
    ) -> Path:
        """Get the appropriate settings file to use for symlinking.

        Returns cached merged settings if overrides exist and cache is valid,
        otherwise returns the base settings file.

        This method does NOT build the cache - use build_merged_settings for that.

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base settings.json in repo
            repo_root: Repository root path

        Returns:
            Path to settings file to use (either cached or base)
        """
        if agent not in self.settings_overrides:
            return base_settings_path

        cache_path = self.get_merged_settings_path(agent, repo_root)
        if cache_path and cache_path.exists():
            # Use cached version if it exists
            return cache_path

        # No cache exists, use base file
        # Note: Cache will be built during install operations
        return base_settings_path

    def is_cache_stale(
        self, agent: str, base_settings_path: Path, repo_root: Path
    ) -> bool:
        """Check if cached merged settings are stale.

        Cache is considered stale if:
        - Cache file doesn't exist
        - Base settings file is newer than cache
        - User config is newer than cache (overrides changed)

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base settings.json in repo
            repo_root: Repository root path

        Returns:
            True if cache needs rebuilding, False otherwise
        """
        if agent not in self.settings_overrides:
            return False

        cache_path = self.get_merged_settings_path(agent, repo_root)
        if not cache_path or not cache_path.exists():
            return True

        cache_mtime = cache_path.stat().st_mtime

        # Check if base settings are newer
        if base_settings_path.exists():
            if base_settings_path.stat().st_mtime > cache_mtime:
                return True

        # Check if user config is newer (overrides may have changed)
        user_config_path = Path.home() / ".ai-rules-config.yaml"
        if user_config_path.exists():
            if user_config_path.stat().st_mtime > cache_mtime:
                return True

        return False

    def build_merged_settings(
        self,
        agent: str,
        base_settings_path: Path,
        repo_root: Path,
        force_rebuild: bool = False,
    ) -> Optional[Path]:
        """Build merged settings file in cache if overrides exist.

        Only rebuilds cache if:
        - force_rebuild is True, OR
        - Cache doesn't exist or is stale

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base settings.json in repo
            repo_root: Repository root path
            force_rebuild: Force rebuild even if cache exists and is fresh

        Returns:
            Path to merged settings file, or None if no overrides exist
        """
        if agent not in self.settings_overrides:
            return None

        cache_path = self.get_merged_settings_path(agent, repo_root)

        # Skip rebuild if cache is fresh and not forced
        if not force_rebuild and cache_path and cache_path.exists():
            if not self.is_cache_stale(agent, base_settings_path, repo_root):
                return cache_path

        # Read base settings
        if not base_settings_path.exists():
            # No base settings, just create from overrides
            base_settings = {}
        else:
            with open(base_settings_path, "r") as f:
                base_settings = json.load(f)

        # Merge with overrides
        merged = self.merge_settings(agent, base_settings)

        # Write to cache
        if cache_path:
            with open(cache_path, "w") as f:
                json.dump(merged, f, indent=2)

        return cache_path

    def validate_projects(self) -> List[str]:
        """Validate all project configurations.

        Returns list of error messages for invalid projects.
        """
        errors = []
        for project_name, project in self.projects.items():
            if not project.path.exists():
                errors.append(
                    f"Project '{project_name}' path does not exist: {project.path}"
                )
            elif not project.path.is_dir():
                errors.append(
                    f"Project '{project_name}' path is not a directory: {project.path}"
                )

        return errors
