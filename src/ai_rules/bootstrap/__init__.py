"""Bootstrap module for system-wide installation and auto-update functionality.

This module provides utilities for:
- Installing tools via uv (PyPI-based)
- Checking for and applying updates from PyPI
- Managing auto-update configuration

Designed to be self-contained and easily extractable for use in other projects.
"""

# Configuration utilities
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

# Installation utilities
from .installer import UV_NOT_FOUND_ERROR, install_tool, is_uv_available, uninstall_tool

# Update utilities
from .updater import UpdateInfo, check_pypi_updates, perform_pypi_update

# Version utilities
from .version import get_package_version, is_newer, parse_version

__all__ = [
    # Version
    "get_package_version",
    "is_newer",
    "parse_version",
    # Installation
    "UV_NOT_FOUND_ERROR",
    "install_tool",
    "is_uv_available",
    "uninstall_tool",
    # Updates
    "UpdateInfo",
    "check_pypi_updates",
    "perform_pypi_update",
    # Configuration
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
