"""Bootstrap module for system-wide installation and auto-update functionality.

This module provides utilities for:
- Detecting installation source (git, PyPI, editable)
- Installing tools via uv
- Checking for and applying updates
- Managing auto-update configuration

Designed to be self-contained and easily extractable for use in other projects.
"""

# Version utilities
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

# Detection utilities
from .detection import (
    UV_NOT_FOUND_ERROR,
    InstallationInfo,
    find_git_repo,
    get_existing_tool_info,
    get_installation_info,
    get_uv_tool_dir,
    is_editable_install,
    is_tool_installed,
    is_uv_available,
)

# Installation utilities
from .installer import install_from_pypi, install_tool, uninstall_tool

# Update utilities
from .updater import (
    UpdateInfo,
    check_git_updates,
    check_pypi_updates,
    perform_git_update,
    perform_pypi_update,
    perform_update,
)
from .version import get_package_version, is_newer, parse_version

__all__ = [
    # Version
    "get_package_version",
    "is_newer",
    "parse_version",
    # Detection
    "UV_NOT_FOUND_ERROR",
    "InstallationInfo",
    "find_git_repo",
    "get_existing_tool_info",
    "get_installation_info",
    "get_uv_tool_dir",
    "is_editable_install",
    "is_tool_installed",
    "is_uv_available",
    # Installation
    "install_from_pypi",
    "install_tool",
    "uninstall_tool",
    # Updates
    "UpdateInfo",
    "check_git_updates",
    "check_pypi_updates",
    "perform_git_update",
    "perform_pypi_update",
    "perform_update",
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
