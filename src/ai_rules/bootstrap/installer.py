"""Tool installation utilities."""

import subprocess

from .detection import UV_NOT_FOUND_ERROR, InstallationInfo, is_uv_available


def install_tool(
    info: InstallationInfo,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Install package as a uv tool.

    Args:
        info: Installation information from get_installation_info()
        force: Force reinstall if already installed
        dry_run: Show what would be done without executing

    Returns:
        Tuple of (success, message)
    """
    if not is_uv_available():
        return False, UV_NOT_FOUND_ERROR

    # Build command based on installation source
    if info.source in ("git", "editable") or info.repo_path:
        # For git repos and editable installs, use editable flag
        install_path = str(info.repo_path or info.package_path)
        cmd = ["uv", "tool", "install", "-e", install_path]
    else:
        # For PyPI installs, use package name
        cmd = ["uv", "tool", "install", info.package_name]

    if force:
        # Insert --force after 'install' subcommand
        cmd.insert(3, "--force")

    if dry_run:
        return True, f"Would run: {' '.join(cmd)}"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, "Installation successful"

        # Extract meaningful error from stderr
        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = "Installation failed with no error message"

        return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Installation timed out after 60 seconds"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def uninstall_tool(package_name: str = "ai-rules") -> tuple[bool, str]:
    """Uninstall package from uv tools.

    Args:
        package_name: Name of package to uninstall

    Returns:
        Tuple of (success, message)
    """
    if not is_uv_available():
        return False, UV_NOT_FOUND_ERROR

    cmd = ["uv", "tool", "uninstall", package_name]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, "Uninstallation successful"

        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = "Uninstallation failed with no error message"

        return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Uninstallation timed out after 30 seconds"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def install_from_pypi(
    package_name: str = "ai-rules",
    force: bool = False,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Install package from PyPI (non-editable).

    Used for migration from git to PyPI install, or fresh PyPI installs.

    Args:
        package_name: Name of package to install
        force: Force reinstall if already installed
        dry_run: Show what would be done without executing

    Returns:
        Tuple of (success, message)
    """
    if not is_uv_available():
        return False, UV_NOT_FOUND_ERROR

    cmd = ["uv", "tool", "install", package_name]
    if force:
        cmd.insert(3, "--force")

    if dry_run:
        return True, f"Would run: {' '.join(cmd)}"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, "Installation successful"

        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = "Installation failed with no error message"

        return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Installation timed out after 60 seconds"
    except Exception as e:
        return False, f"Unexpected error: {e}"
