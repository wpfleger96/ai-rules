"""Configuration loading and management."""

import copy
import json
import re
import shutil

from fnmatch import fnmatch
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ai_rules.utils import deep_merge

__all__ = [
    "Config",
    "AGENT_CONFIG_METADATA",
    "parse_setting_path",
    "navigate_path",
    "validate_override_path",
]

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


def parse_setting_path(path: str) -> list[str | int]:
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


def navigate_path(data: Any, path_components: list[str | int]) -> tuple[Any, bool, str]:
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
                return (
                    None,
                    False,
                    f"Key '{component}' not found at '{path_so_far}'",
                )

            current = current[component]

    return (current, True, "")


def _format_path(components: list[str | int]) -> str:
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
    agent: str, setting: str, config_dir: Path
) -> tuple[bool, str, str, list[str]]:
    """Validate an override path against base settings.

    Args:
        agent: Agent name (e.g., 'claude', 'goose')
        setting: Setting path (e.g., 'hooks.SubagentStop[0].command')
        config_dir: Config directory path

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

    settings_file = config_dir / agent / config_file
    if not settings_file.exists():
        return (
            False,
            f"No base settings file found for agent '{agent}' at {settings_file}",
            "",
            [],
        )

    try:
        with open(settings_file) as f:
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

    error_msg = f"Path '{setting}' not found in base config."
    if suggestions:
        error_msg += f" Did you mean one of: {', '.join(suggestions[:5])}?"

    return (False, error_msg, "", suggestions)


class Config:
    """Configuration for ai-rules tool."""

    def __init__(
        self,
        exclude_symlinks: list[str] | None = None,
        settings_overrides: dict[str, dict[str, Any]] | None = None,
        mcp_overrides: dict[str, dict[str, Any]] | None = None,
        profile_name: str | None = None,
    ):
        self.exclude_symlinks = set(exclude_symlinks or [])
        self.settings_overrides = settings_overrides or {}
        self.mcp_overrides = mcp_overrides or {}
        self.profile_name = profile_name

    @classmethod
    def load(cls, profile: str | None = None) -> "Config":
        """Load configuration from profile and ~/.ai-rules-config.yaml.

        Merge order (lowest to highest priority):
        1. Profile overrides (if profile specified, defaults to active profile or "default")
        2. Local overrides from ~/.ai-rules-config.yaml

        Args:
            profile: Optional profile name to load (default: active profile or "default")

        Returns:
            Config instance with merged overrides
        """
        if profile is None:
            from ai_rules.state import get_active_profile

            profile = get_active_profile() or "default"
        return cls._load_cached(profile)

    @classmethod
    @lru_cache(maxsize=8)
    def _load_cached(cls, profile_name: str) -> "Config":
        """Internal cached loader keyed by profile name."""
        from ai_rules.profiles import ProfileLoader, ProfileNotFoundError

        loader = ProfileLoader()

        try:
            profile_data = loader.load_profile(profile_name)
        except ProfileNotFoundError:
            raise

        exclude_symlinks = list(profile_data.exclude_symlinks)
        settings_overrides = copy.deepcopy(profile_data.settings_overrides)
        mcp_overrides = copy.deepcopy(profile_data.mcp_overrides)

        user_config_path = Path.home() / ".ai-rules-config.yaml"
        if user_config_path.exists():
            with open(user_config_path) as f:
                user_data = yaml.safe_load(f) or {}

            user_excludes = user_data.get("exclude_symlinks", [])
            exclude_symlinks = list(set(exclude_symlinks) | set(user_excludes))

            user_settings = user_data.get("settings_overrides", {})
            settings_overrides = deep_merge(settings_overrides, user_settings)

            user_mcp = user_data.get("mcp_overrides", {})
            mcp_overrides = deep_merge(mcp_overrides, user_mcp)

        return cls(
            exclude_symlinks=exclude_symlinks,
            settings_overrides=settings_overrides,
            mcp_overrides=mcp_overrides,
            profile_name=profile_name,
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

    @staticmethod
    def get_cache_dir() -> Path:
        """Get the cache directory for merged settings."""
        cache_dir = Path.home() / ".ai-rules" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def merge_settings(
        self, agent: str, base_settings: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge base settings with overrides for a specific agent.

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings: Base settings dictionary from repo

        Returns:
            Merged settings dictionary with overrides applied
        """
        if agent not in self.settings_overrides:
            return base_settings

        return deep_merge(base_settings, self.settings_overrides[agent])

    def get_merged_settings_path(self, agent: str) -> Path | None:
        """Get the path to cached merged settings for an agent.

        Returns None if agent has no overrides (should use base file directly).

        Args:
            agent: Agent name (e.g., 'claude', 'goose')

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
        self, agent: str, base_settings_path: Path
    ) -> Path:
        """Get the appropriate settings file to use for symlinking.

        Returns cached merged settings if overrides exist and cache is valid,
        otherwise returns the base settings file.

        This method does NOT build the cache - use build_merged_settings for that.

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base settings file

        Returns:
            Path to settings file to use (either cached or base)
        """
        if agent not in self.settings_overrides:
            return base_settings_path

        cache_path = self.get_merged_settings_path(agent)
        if cache_path and cache_path.exists():
            return cache_path

        return base_settings_path

    def is_cache_stale(self, agent: str, base_settings_path: Path) -> bool:
        """Check if cached merged settings are stale.

        Cache is considered stale if:
        - Cache file doesn't exist
        - Base settings file is newer than cache
        - User config is newer than cache (overrides changed)

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base settings file

        Returns:
            True if cache needs rebuilding, False otherwise
        """
        if agent not in self.settings_overrides:
            return False

        cache_path = self.get_merged_settings_path(agent)
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

        if self.profile_name and self.profile_name != "default":
            from ai_rules.profiles import ProfileLoader

            loader = ProfileLoader()
            profile_path = loader._profiles_dir / f"{self.profile_name}.yaml"
            if profile_path.exists() and profile_path.stat().st_mtime > cache_mtime:
                return True

        return False

    def get_cache_diff(self, agent: str, base_settings_path: Path) -> str | None:
        """Get a unified diff between cached and expected merged settings.

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base settings in repo

        Returns:
            Formatted diff string with Rich markup, or None if no diff/cache doesn't exist
        """
        import difflib

        if agent not in self.settings_overrides:
            return None

        cache_path = self.get_merged_settings_path(agent)
        if not cache_path or not cache_path.exists():
            return None

        agent_config = AGENT_CONFIG_METADATA.get(agent)
        if not agent_config:
            return None

        config_format = agent_config["format"]

        try:
            with open(cache_path) as f:
                if config_format == "json":
                    cached_settings = json.load(f)
                elif config_format == "yaml":
                    cached_settings = yaml.safe_load(f) or {}
                else:
                    return None
        except (json.JSONDecodeError, yaml.YAMLError, OSError):
            return None

        if not base_settings_path.exists():
            base_settings = {}
        else:
            try:
                with open(base_settings_path) as f:
                    if config_format == "json":
                        base_settings = json.load(f)
                    elif config_format == "yaml":
                        base_settings = yaml.safe_load(f) or {}
                    else:
                        return None
            except (json.JSONDecodeError, yaml.YAMLError, OSError):
                return None

        expected_settings = self.merge_settings(agent, base_settings)

        if cached_settings == expected_settings:
            return None

        if config_format == "json":
            cached_text = json.dumps(cached_settings, indent=2)
            expected_text = json.dumps(expected_settings, indent=2)
        elif config_format == "yaml":
            cached_text = yaml.dump(
                cached_settings, default_flow_style=False, sort_keys=False
            )
            expected_text = yaml.dump(
                expected_settings, default_flow_style=False, sort_keys=False
            )
        else:
            return None

        cached_lines = cached_text.splitlines(keepends=True)
        expected_lines = expected_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            cached_lines,
            expected_lines,
            fromfile="Cached (current)",
            tofile="Expected (merged)",
            lineterm="",
        )

        diff_lines = []
        for line in diff:
            line = line.rstrip("\n")
            if (
                line.startswith("---")
                or line.startswith("+++")
                or line.startswith("@@")
            ):
                diff_lines.append(f"[dim]    {line}[/dim]")
            elif line.startswith("+"):
                diff_lines.append(f"[green]    {line}[/green]")
            elif line.startswith("-"):
                diff_lines.append(f"[red]    {line}[/red]")
            else:
                diff_lines.append(f"[dim]    {line}[/dim]")

        if not diff_lines:
            return None

        return "\n".join(diff_lines)

    def build_merged_settings(
        self,
        agent: str,
        base_settings_path: Path,
        force_rebuild: bool = False,
    ) -> Path | None:
        """Build merged settings file in cache if overrides exist.

        Only rebuilds cache if:
        - force_rebuild is True, OR
        - Cache doesn't exist or is stale

        Args:
            agent: Agent name (e.g., 'claude', 'goose')
            base_settings_path: Path to base config file
            force_rebuild: Force rebuild even if cache exists and is fresh

        Returns:
            Path to merged settings file, or None if no overrides exist
        """
        if agent not in self.settings_overrides:
            return None

        cache_path = self.get_merged_settings_path(agent)

        if not force_rebuild and cache_path and cache_path.exists():
            if not self.is_cache_stale(agent, base_settings_path):
                return cache_path

        agent_config = AGENT_CONFIG_METADATA.get(agent)
        if not agent_config:
            return None

        config_format = agent_config["format"]

        if not base_settings_path.exists():
            base_settings = {}
        else:
            with open(base_settings_path) as f:
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

    @staticmethod
    def load_user_config() -> dict[str, Any]:
        """Load user config file with defaults.

        Returns:
            Dictionary with user config data, or empty dict with version if file doesn't exist
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"

        if user_config_path.exists():
            with open(user_config_path) as f:
                return yaml.safe_load(f) or {"version": 1}
        return {"version": 1}

    @staticmethod
    def save_user_config(data: dict[str, Any]) -> None:
        """Save user config file with consistent formatting.

        Args:
            data: Configuration dictionary to save
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def cleanup_orphaned_cache(self) -> list[str]:
        """Remove cache files for agents that no longer have overrides.

        Returns:
            List of agent IDs whose caches were removed
        """
        removed: list[str] = []
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
