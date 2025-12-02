"""Auto-update configuration management."""

import json
import logging

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from .updater import UpdateInfo

logger = logging.getLogger(__name__)


@dataclass
class AutoUpdateConfig:
    """Configuration for automatic update checks."""

    enabled: bool = True
    frequency: str = "weekly"  # daily, weekly, never
    last_check: str | None = None  # ISO format timestamp
    notify_only: bool = False


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

        return AutoUpdateConfig(
            enabled=data.get("enabled", True),
            frequency=data.get("frequency", "weekly"),
            last_check=data.get("last_check"),
            notify_only=data.get("notify_only", False),
        )
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


def get_pending_update_path(package_name: str = "ai-rules") -> Path:
    """Get path to pending update cache file.

    Args:
        package_name: Name of the package

    Returns:
        Path to pending_update.json
    """
    return get_config_dir(package_name) / "pending_update.json"


def load_pending_update(package_name: str = "ai-rules") -> UpdateInfo | None:
    """Load cached update info from previous background check.

    Args:
        package_name: Name of the package

    Returns:
        UpdateInfo if available, None otherwise
    """
    pending_path = get_pending_update_path(package_name)

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


def save_pending_update(info: UpdateInfo, package_name: str = "ai-rules") -> None:
    """Save update info for next session.

    Args:
        info: Update information to save
        package_name: Name of the package
    """
    pending_path = get_pending_update_path(package_name)

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


def clear_pending_update(package_name: str = "ai-rules") -> None:
    """Clear pending update after user action.

    Args:
        package_name: Name of the package
    """
    pending_path = get_pending_update_path(package_name)

    try:
        pending_path.unlink(missing_ok=True)
    except OSError as e:
        logger.debug(f"Failed to delete pending update at {pending_path}: {e}")
