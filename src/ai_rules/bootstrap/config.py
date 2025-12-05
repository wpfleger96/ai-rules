"""Auto-update configuration management."""

import dataclasses
import json
import logging
import re

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from .updater import UpdateInfo

logger = logging.getLogger(__name__)


def _validate_tool_id(tool_id: str) -> bool:
    """Validate tool_id contains only safe characters."""
    return bool(re.match(r"^[a-z0-9][a-z0-9_-]*$", tool_id))


@dataclass
class AutoUpdateConfig:
    """Configuration for automatic update checks."""

    enabled: bool = True
    frequency: str = "daily"  # daily, weekly, never
    last_check: str | None = None  # ISO format timestamp
    notify_only: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutoUpdateConfig":
        """Create from dict, using dataclass defaults for missing keys."""
        fields = {f.name for f in dataclasses.fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in fields}
        return cls(**kwargs)


def get_config_dir(package_name: str = "ai-rules") -> Path:
    """Get the config directory for the package.

    Args:
        package_name: Name of the package

    Returns:
        Path to config directory (e.g., ~/.ai-rules/)
    """
    config_dir = Path.home() / f".{package_name}"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path(package_name: str = "ai-rules") -> Path:
    """Get path to bootstrap config file.

    Args:
        package_name: Name of the package

    Returns:
        Path to update_config.yaml
    """
    return get_config_dir(package_name) / "update_config.yaml"


def load_auto_update_config(package_name: str = "ai-rules") -> AutoUpdateConfig:
    """Load auto-update configuration.

    Args:
        package_name: Name of the package

    Returns:
        AutoUpdateConfig with loaded or default values
    """
    config_path = get_config_path(package_name)

    if not config_path.exists():
        return AutoUpdateConfig()

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return AutoUpdateConfig.from_dict(data)
    except (yaml.YAMLError, OSError):
        return AutoUpdateConfig()


def save_auto_update_config(
    config: AutoUpdateConfig, package_name: str = "ai-rules"
) -> None:
    """Save auto-update configuration.

    Args:
        config: Configuration to save
        package_name: Name of the package
    """
    config_path = get_config_path(package_name)

    try:
        with open(config_path, "w") as f:
            yaml.dump(asdict(config), f, default_flow_style=False, sort_keys=False)
    except OSError as e:
        logger.debug(f"Failed to save config to {config_path}: {e}")


def should_check_now(config: AutoUpdateConfig) -> bool:
    """Determine if update check is due based on frequency.

    Args:
        config: Auto-update configuration

    Returns:
        True if check should be performed, False otherwise
    """
    if not config.enabled:
        return False

    if config.frequency == "never":
        return False

    if not config.last_check:
        return True

    try:
        last_check = datetime.fromisoformat(config.last_check)
        now = datetime.now()

        if config.frequency == "daily":
            return now - last_check > timedelta(days=1)
        elif config.frequency == "weekly":
            return now - last_check > timedelta(days=7)

    except (ValueError, TypeError):
        return True

    return False


def get_pending_update_path(tool_id: str = "ai-rules") -> Path:
    """Get path to pending update cache file for a specific tool.

    Args:
        tool_id: Tool identifier (e.g., "ai-rules", "statusline")

    Returns:
        Path to pending update JSON file

    Raises:
        ValueError: If tool_id contains invalid characters
    """
    if not _validate_tool_id(tool_id):
        raise ValueError(f"Invalid tool_id: {tool_id}")

    if tool_id == "ai-rules":
        filename = "pending_update.json"
    else:
        filename = f"pending_{tool_id}_update.json"

    return get_config_dir("ai-rules") / filename


def load_pending_update(tool_id: str = "ai-rules") -> UpdateInfo | None:
    """Load cached update info from previous background check.

    Args:
        tool_id: Tool identifier (e.g., "ai-rules", "statusline")

    Returns:
        UpdateInfo if available, None otherwise
    """
    if not _validate_tool_id(tool_id):
        return None

    pending_path = get_pending_update_path(tool_id)

    if not pending_path.exists():
        return None

    try:
        with open(pending_path) as f:
            data = json.load(f)

        return UpdateInfo(
            has_update=data.get("has_update", False),
            current_version=data["current_version"],
            latest_version=data["latest_version"],
            source=data["source"],
        )
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def save_pending_update(info: UpdateInfo, tool_id: str = "ai-rules") -> None:
    """Save update info for next session.

    Args:
        info: Update information to save
        tool_id: Tool identifier (e.g., "ai-rules", "statusline")
    """
    if not _validate_tool_id(tool_id):
        return

    pending_path = get_pending_update_path(tool_id)

    try:
        data = {
            "has_update": info.has_update,
            "current_version": info.current_version,
            "latest_version": info.latest_version,
            "source": info.source,
            "checked_at": datetime.now().isoformat(),
        }

        with open(pending_path, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        logger.debug(f"Failed to save pending update to {pending_path}: {e}")


def clear_pending_update(tool_id: str = "ai-rules") -> None:
    """Clear pending update after user action.

    Args:
        tool_id: Tool identifier (e.g., "ai-rules", "statusline")
    """
    if not _validate_tool_id(tool_id):
        return

    pending_path = get_pending_update_path(tool_id)

    try:
        pending_path.unlink(missing_ok=True)
    except OSError as e:
        logger.debug(f"Failed to delete pending update at {pending_path}: {e}")


def load_all_pending_updates() -> dict[str, UpdateInfo]:
    """Load pending updates for all tools.

    Returns:
        Dictionary mapping tool_id to UpdateInfo for tools with pending updates
    """
    from .updater import UPDATABLE_TOOLS

    result = {}
    for tool in UPDATABLE_TOOLS:
        pending = load_pending_update(tool.tool_id)
        if pending and pending.has_update:
            result[tool.tool_id] = pending

    return result


def clear_all_pending_updates() -> None:
    """Clear pending updates for all tools."""
    from .updater import UPDATABLE_TOOLS

    for tool in UPDATABLE_TOOLS:
        clear_pending_update(tool.tool_id)
