"""Bootstrap module for system-wide installation and auto-update functionality.

This module provides utilities for:
- Installing tools via uv (PyPI-based)
- Checking for and applying updates from PyPI
- Managing auto-update configuration

Designed to be self-contained and easily extractable for use in other projects.
"""

from .config import (
    AutoUpdateConfig,
    clear_pending_update,
    get_config_dir,
    get_config_path,
    get_pending_update_path,
    load_auto_update_config,
    load_pending_update,
    save_auto_update_config,
    save_pending_update,
    should_check_now,
)
from .installer import (
    UV_NOT_FOUND_ERROR,
    get_tool_config_dir,
    install_tool,
    is_uv_available,
    uninstall_tool,
)
from .updater import UpdateInfo, check_pypi_updates, perform_pypi_update
from .version import get_package_version, is_newer, parse_version

__all__ = [
    "get_package_version",
    "is_newer",
    "parse_version",
    "UV_NOT_FOUND_ERROR",
    "get_tool_config_dir",
    "install_tool",
    "is_uv_available",
    "uninstall_tool",
    "UpdateInfo",
    "check_pypi_updates",
    "perform_pypi_update",
    "AutoUpdateConfig",
    "clear_pending_update",
    "get_config_dir",
    "get_config_path",
    "get_pending_update_path",
    "load_auto_update_config",
    "load_pending_update",
    "save_auto_update_config",
    "save_pending_update",
    "should_check_now",
]
