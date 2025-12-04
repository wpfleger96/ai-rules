"""Update checking and application utilities."""

import json
import re
import subprocess
import urllib.request

from collections.abc import Callable
from dataclasses import dataclass

from .installer import (
    UV_NOT_FOUND_ERROR,
    get_tool_source,
    get_tool_version,
    is_command_available,
)
from .version import get_package_version, is_newer


@dataclass
class UpdateInfo:
    """Information about available updates."""

    has_update: bool
    current_version: str
    latest_version: str
    source: str  # "pypi"


def check_pypi_updates(package_name: str, current_version: str) -> UpdateInfo:
    """Check PyPI for newer version.

    Args:
        package_name: Package name on PyPI
        current_version: Currently installed version

    Returns:
        UpdateInfo with update status
    """
    # Validate package name (PEP 508 compliant)
    if not re.match(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$", package_name):
        return UpdateInfo(
            has_update=False,
            current_version=current_version,
            latest_version=current_version,
            source="pypi",
        )

    try:
        url = f"https://pypi.org/pypi/{package_name}/json"

        req = urllib.request.Request(url)
        req.add_header("User-Agent", f"{package_name}/{current_version}")

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        latest_version = data["info"]["version"]
        has_update = is_newer(latest_version, current_version)

        return UpdateInfo(
            has_update=has_update,
            current_version=current_version,
            latest_version=latest_version,
            source="pypi",
        )

    except (urllib.error.URLError, json.JSONDecodeError, KeyError, Exception):
        # Return no update on error
        return UpdateInfo(
            has_update=False,
            current_version=current_version,
            latest_version=current_version,
            source="pypi",
        )


def perform_pypi_update(package_name: str) -> tuple[bool, str, bool]:
    """Upgrade via uv tool upgrade.

    Args:
        package_name: Name of package to upgrade

    Returns:
        Tuple of (success, message, was_upgraded)
        - success: Whether command succeeded
        - message: Human-readable status message
        - was_upgraded: True if package was actually upgraded (not already up-to-date)
    """
    if not is_command_available("uv"):
        return False, UV_NOT_FOUND_ERROR, False

    source = get_tool_source(package_name)

    if source == "local":
        cmd = ["uv", "tool", "install", package_name, "--force"]
    else:
        cmd = ["uv", "tool", "upgrade", package_name]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            output = result.stdout + result.stderr

            upgrade_patterns = [
                r"Upgraded .+ from .+ to .+",
                r"Installed .+ \d+\.\d+",
                r"Successfully installed",
            ]

            already_up_to_date_patterns = [
                r"Nothing to upgrade",
                r"already.*installed",
                r"already.*up.*to.*date",
            ]

            was_upgraded = False
            if any(
                re.search(pattern, output, re.IGNORECASE)
                for pattern in upgrade_patterns
            ):
                was_upgraded = True
            elif any(
                re.search(pattern, output, re.IGNORECASE)
                for pattern in already_up_to_date_patterns
            ):
                was_upgraded = False
            else:
                was_upgraded = True

            return True, "Upgrade successful", was_upgraded

        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = "Upgrade failed with no error message"

        return False, error_msg, False

    except subprocess.TimeoutExpired:
        return False, "Upgrade timed out after 60 seconds", False
    except Exception as e:
        return False, f"Unexpected error: {e}", False


@dataclass
class ToolSpec:
    """Specification for an updatable tool."""

    tool_id: str
    package_name: str
    display_name: str
    get_version: Callable[[], str | None]
    is_installed: Callable[[], bool]


UPDATABLE_TOOLS: list[ToolSpec] = [
    ToolSpec(
        tool_id="ai-rules",
        package_name="ai-agent-rules",
        display_name="ai-rules",
        get_version=lambda: get_package_version("ai-agent-rules"),
        is_installed=lambda: True,  # Always installed (it's us)
    ),
    ToolSpec(
        tool_id="statusline",
        package_name="claude-code-statusline",
        display_name="statusline",
        get_version=lambda: get_tool_version("claude-code-statusline"),
        is_installed=lambda: is_command_available("claude-statusline"),
    ),
]


def check_tool_updates(tool: ToolSpec) -> UpdateInfo | None:
    """Check for updates for any tool.

    Args:
        tool: Tool specification

    Returns:
        UpdateInfo if tool is installed and update check succeeds, None otherwise
    """
    if not tool.is_installed():
        return None

    current = tool.get_version()
    if current is None:
        return None

    return check_pypi_updates(tool.package_name, current)


def get_tool_by_id(tool_id: str) -> ToolSpec | None:
    """Look up tool spec by ID.

    Args:
        tool_id: Tool identifier (e.g., "ai-rules", "statusline")

    Returns:
        ToolSpec if found, None otherwise
    """
    return next((t for t in UPDATABLE_TOOLS if t.tool_id == tool_id), None)
