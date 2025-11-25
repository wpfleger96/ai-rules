"""Configuration loading and management."""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import copy
import json
import re
import shutil
import yaml
from fnmatch import fnmatch

AGENT_CONFIG_METADATA = {
    "claude": {
        "config_file": "settings.json",
        "format": "json",
    },
    "goose": {
        "config_file": "config.yaml",
        "format": "yaml",
    },
}


def parse_setting_path(path: str) -> List[Union[str, int]]:
    """Parse a setting path with array indices into components.

    Examples:
        'model' -> ['model']
        'hooks.SubagentStop[0].command' -> ['hooks', 'SubagentStop', 0, 'command']
        'env.SOME_VAR' -> ['env', 'SOME_VAR']
        'hooks.SubagentStop[0].hooks[0].command' -> ['hooks', 'SubagentStop', 0, 'hooks', 0, 'command']

    Args:
        path: Setting path string with optional array indices

    Returns:
        List of path components (str for keys, int for array indices)

    Raises:
        ValueError: If array indices are invalid or path is malformed
    """
    if not path:
        raise ValueError("Path cannot be empty")

    components = []
    parts = path.split(".")

    for part in parts:
        if "[" in part:
            match = re.match(r"^([^\[]+)(\[\d+\])+$", part)
            if not match:
                raise ValueError(
                    f"Invalid array notation in '{part}'. Use format: key[0] or key[0][1]"
                )

            key = match.group(1)
            components.append(key)

            indices = re.findall(r"\[(\d+)\]", part)
            for idx in indices:
                components.append(int(idx))
        else:
            components.append(part)

    return components


def navigate_path(
    data: Any, path_components: List[Union[str, int]]
) -> Tuple[Any, bool, str]:
    """Navigate a data structure using path components.

    Args:
        data: Data structure to navigate (dict, list, or primitive)
        path_components: List of path components (str for keys, int for indices)

    Returns:
        Tuple of (value_at_path, success, error_message)
        - If success: (value, True, '')
        - If failure: (None, False, 'error description')
    """
    current = data

    for i, component in enumerate(path_components):
        if isinstance(component, int):
            if not isinstance(current, list):
                path_so_far = _format_path(path_components[:i])
                return (
                    None,
                    False,
                    f"Expected array at '{path_so_far}' but found {type(current).__name__}",
                )

            if component >= len(current):
                path_so_far = _format_path(path_components[:i])
                return (
                    None,
                    False,
                    f"Array index {component} out of range at '{path_so_far}' (length: {len(current)})",
                )

            current = current[component]
        else:
            if not isinstance(current, dict):
                path_so_far = _format_path(path_components[:i])
                return (
                    None,
                    False,
                    f"Expected object at '{path_so_far}' but found {type(current).__name__}",
                )

            if component not in current:
                path_so_far = _format_path(path_components[: i + 1])
                list(current.keys()) if isinstance(current, dict) else []
                return (
                    None,
                    False,
                    f"Key '{component}' not found at '{path_so_far}'",
                )

            current = current[component]

    return (current, True, "")


def _format_path(components: List[Union[str, int]]) -> str:
    """Format path components back into a string representation.

    Args:
        components: List of path components

    Returns:
        Formatted path string
    """
    if not components:
        return ""

    result = []
    i = 0
    while i < len(components):
        component = components[i]
        if isinstance(component, str):
            result.append(component)
            i += 1
        else:
            if result:
                result[-1] += f"[{component}]"
            i += 1

    return ".".join(result)


def validate_override_path(
    agent: str, setting: str, repo_root: Path
) -> Tuple[bool, str, str, List[str]]:
    """Validate an override path against base settings.

    Args:
        agent: Agent name (e.g., 'claude', 'goose')
        setting: Setting path (e.g., 'hooks.SubagentStop[0].command')
        repo_root: Repository root path

    Returns:
        Tuple of (is_valid, error_message, warning_message, suggestions)
        - If valid: (True, '', '', [])
        - If invalid (hard error): (False, 'error message', '', ['suggestion1', 'suggestion2'])
        - If valid with warning: (True, '', 'warning message', ['suggestion1', 'suggestion2'])
    """
    valid_agents = list(AGENT_CONFIG_METADATA.keys())
    if agent not in valid_agents:
        return (
            False,
            f"Unknown agent '{agent}'",
            "",
            valid_agents,
        )

    agent_config = AGENT_CONFIG_METADATA[agent]
    config_file = agent_config["config_file"]
    config_format = agent_config["format"]

    settings_file = repo_root / "config" / agent / config_file
    if not settings_file.exists():
        return (
            False,
            f"No base settings file found for agent '{agent}' at {settings_file}",
            "",
            [],
        )

    try:
        with open(settings_file, "r") as f:
            if config_format == "json":
                base_settings = json.load(f)
            elif config_format == "yaml":
                base_settings = yaml.safe_load(f)
            else:
                return (False, f"Unsupported config format: {config_format}", "", [])
    except (json.JSONDecodeError, yaml.YAMLError, OSError) as e:
        return (False, f"Failed to load base settings: {e}", "", [])

    try:
        path_components = parse_setting_path(setting)
    except ValueError as e:
        return (False, str(e), "", [])

    value, success, error_msg = navigate_path(base_settings, path_components)

    if success:
        return (True, "", "", [])

    suggestions = []
    if "not found" in error_msg.lower():
        for i in range(len(path_components) - 1, -1, -1):
            partial_path = path_components[:i]
            partial_value, partial_success, _ = navigate_path(
                base_settings, partial_path
            )
            if partial_success and isinstance(partial_value, dict):
                suggestions = list(partial_value.keys())
                break

    warning_msg = f"Path '{setting}' not found in base config. Setting will be added as a new key."
    if suggestions:
        warning_msg += f" Did you mean one of: {', '.join(suggestions[:5])}?"

    return (True, "", warning_msg, suggestions)


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
            excl_normalized = Path(excl).expanduser().as_posix()
            if normalized == excl_normalized:
                return True
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
        mcp_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.exclude_symlinks = set(exclude_symlinks or [])
        self.projects = projects or {}
        self.settings_overrides = settings_overrides or {}
        self.mcp_overrides = mcp_overrides or {}

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
        mcp_overrides = {}

        if user_config_path.exists():
            with open(user_config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                exclude_symlinks.extend(data.get("exclude_symlinks", []))

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

                settings_overrides = data.get("settings_overrides", {})
                mcp_overrides = data.get("mcp_overrides", {})

        if repo_config_path.exists():
            with open(repo_config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                exclude_symlinks.extend(data.get("exclude_symlinks", []))

        return cls(
            exclude_symlinks=exclude_symlinks,
            projects=projects,
            settings_overrides=settings_overrides,
            mcp_overrides=mcp_overrides,
        )

    def is_excluded(self, symlink_target: str) -> bool:
        """Check if a symlink target is globally excluded.

        Supports both exact paths and glob patterns (e.g., ~/.claude/*.json).
        """
        normalized = Path(symlink_target).expanduser().as_posix()
        for excl in self.exclude_symlinks:
            excl_normalized = Path(excl).expanduser().as_posix()
            if normalized == excl_normalized:
                return True
            if fnmatch(normalized, excl_normalized):
                return True
        return False

    def is_project_excluded(self, project_name: str, symlink_target: str) -> bool:
        """Check if a symlink target is excluded for a specific project.

        Combines global exclusions and project-specific exclusions.
        """
        if self.is_excluded(symlink_target):
            return True

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

        Supports merging nested dictionaries and arrays. Arrays are merged element-by-element,
        with dict elements being recursively merged.

        Uses deep copy to prevent mutation of the base dictionary.
        """
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key not in result:
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                merged_array = copy.deepcopy(result[key])
                for i, item in enumerate(value):
                    if i < len(merged_array):
                        if isinstance(merged_array[i], dict) and isinstance(item, dict):
                            merged_array[i] = Config._deep_merge(merged_array[i], item)
                        else:
                            merged_array[i] = item
                    else:
                        merged_array.append(item)
                result[key] = merged_array
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

        agent_config = AGENT_CONFIG_METADATA.get(agent)
        if not agent_config:
            return None

        cache_dir = self.get_cache_dir() / agent
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / agent_config["config_file"]

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
            return cache_path

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

        if base_settings_path.exists():
            if base_settings_path.stat().st_mtime > cache_mtime:
                return True

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
            base_settings_path: Path to base config file in repo
            repo_root: Repository root path
            force_rebuild: Force rebuild even if cache exists and is fresh

        Returns:
            Path to merged settings file, or None if no overrides exist
        """
        if agent not in self.settings_overrides:
            return None

        cache_path = self.get_merged_settings_path(agent, repo_root)

        if not force_rebuild and cache_path and cache_path.exists():
            if not self.is_cache_stale(agent, base_settings_path, repo_root):
                return cache_path

        agent_config = AGENT_CONFIG_METADATA.get(agent)
        if not agent_config:
            return None

        config_format = agent_config["format"]

        if not base_settings_path.exists():
            base_settings = {}
        else:
            with open(base_settings_path, "r") as f:
                if config_format == "json":
                    base_settings = json.load(f)
                elif config_format == "yaml":
                    base_settings = yaml.safe_load(f) or {}
                else:
                    return None

        merged = self.merge_settings(agent, base_settings)
        if cache_path:
            with open(cache_path, "w") as f:
                if config_format == "json":
                    json.dump(merged, f, indent=2)
                elif config_format == "yaml":
                    yaml.safe_dump(merged, f, default_flow_style=False, sort_keys=False)

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

    @staticmethod
    def load_user_config() -> Dict[str, Any]:
        """Load user config file with defaults.

        Returns:
            Dictionary with user config data, or empty dict with version if file doesn't exist
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"

        if user_config_path.exists():
            with open(user_config_path, "r") as f:
                return yaml.safe_load(f) or {"version": 1}
        return {"version": 1}

    @staticmethod
    def save_user_config(data: Dict[str, Any]) -> None:
        """Save user config file with consistent formatting.

        Args:
            data: Configuration dictionary to save
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def cleanup_orphaned_cache(self, repo_root: Path) -> List[str]:
        """Remove cache files for agents that no longer have overrides.

        Args:
            repo_root: Repository root path

        Returns:
            List of agent IDs whose caches were removed
        """
        removed = []
        cache_dir = self.get_cache_dir()
        if not cache_dir.exists():
            return removed

        for agent_dir in cache_dir.iterdir():
            if agent_dir.is_dir():
                agent_id = agent_dir.name
                if agent_id not in self.settings_overrides:
                    shutil.rmtree(agent_dir)
                    removed.append(agent_id)

        return removed
