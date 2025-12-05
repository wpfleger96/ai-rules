"""Tool installation utilities."""

import os
import re
import shutil
import subprocess
import sys

from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

UV_NOT_FOUND_ERROR = "uv not found in PATH. Install from https://docs.astral.sh/uv/"


def _validate_package_name(package_name: str) -> bool:
    """Validate package name matches PyPI naming convention (PEP 508)."""
    return bool(re.match(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$", package_name))


def get_tool_config_dir(package_name: str = "ai-agent-rules") -> Path:
    """Get config directory for a uv tool installation.

    Computes the expected path where uv tool install places the package:
    $XDG_DATA_HOME/uv/tools/{package}/lib/python{version}/site-packages/ai_rules/config/

    Args:
        package_name: Name of the uv tool package

    Returns:
        Path to the config directory in the uv tools location
    """

    data_home = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"

    return (
        Path(data_home)
        / "uv"
        / "tools"
        / package_name
        / "lib"
        / python_version
        / "site-packages"
        / "ai_rules"
        / "config"
    )


def get_tool_source(package_name: str) -> str | None:
    """Detect how a uv tool was installed (PyPI vs local file).

    Args:
        package_name: Name of the uv tool package

    Returns:
        "pypi" if installed from PyPI (no path key in requirements)
        "local" if installed from local file (has path key)
        None if tool not installed or receipt file not found
    """
    data_home = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    receipt_path = Path(data_home) / "uv" / "tools" / package_name / "uv-receipt.toml"

    if not receipt_path.exists():
        return None

    try:
        with open(receipt_path, "rb") as f:
            receipt = tomllib.load(f)

        requirements = receipt.get("tool", {}).get("requirements", [])
        if not requirements:
            return None

        # Check first requirement for path key (indicates local install)
        first_req = requirements[0]
        if isinstance(first_req, dict) and "path" in first_req:
            return "local"

        return "pypi"

    except (OSError, tomllib.TOMLDecodeError, KeyError, IndexError):
        return None


def is_command_available(command: str) -> bool:
    """Check if a command is available in PATH.

    Args:
        command: Command name to check

    Returns:
        True if command is available, False otherwise
    """
    return shutil.which(command) is not None


def install_tool(
    package_name: str = "ai-agent-rules",
    force: bool = False,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Install package as a uv tool from PyPI.

    Args:
        package_name: Name of package to install
        force: Force reinstall if already installed
        dry_run: Show what would be done without executing

    Returns:
        Tuple of (success, message)
    """
    if not _validate_package_name(package_name):
        return False, f"Invalid package name: {package_name}"

    if not is_command_available("uv"):
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


def uninstall_tool(package_name: str = "ai-agent-rules") -> tuple[bool, str]:
    """Uninstall package from uv tools.

    Args:
        package_name: Name of package to uninstall

    Returns:
        Tuple of (success, message)
    """
    if not _validate_package_name(package_name):
        return False, f"Invalid package name: {package_name}"

    if not is_command_available("uv"):
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


def get_tool_version(tool_name: str) -> str | None:
    """Get installed version of a uv tool by parsing `uv tool list`.

    Args:
        tool_name: Name of the tool package (e.g., "claude-code-statusline")

    Returns:
        Version string (e.g., "0.7.1") or None if not installed
    """
    if not _validate_package_name(tool_name):
        return None

    if not is_command_available("uv"):
        return None

    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return None

        for line in result.stdout.splitlines():
            if line.startswith(tool_name):
                match = re.search(r"v?(\d+\.\d+\.\d+)", line)
                if match:
                    return match.group(1)

        return None

    except (subprocess.TimeoutExpired, Exception):
        return None


def ensure_statusline_installed(dry_run: bool = False) -> str:
    """Install claude-code-statusline if not already present. Fails open.

    Args:
        dry_run: If True, skip installation

    Returns:
        Status: "already_installed", "installed", "failed", or "skipped"
    """
    if is_command_available("claude-statusline"):
        return "already_installed"

    if dry_run:
        return "skipped"

    try:
        success, _ = install_tool("claude-code-statusline", force=False, dry_run=False)
        return "installed" if success else "failed"
    except Exception:
        return "failed"
