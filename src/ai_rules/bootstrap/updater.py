"""Update checking and application utilities."""

import json
import re
import subprocess
import urllib.request

from dataclasses import dataclass

from .installer import UV_NOT_FOUND_ERROR, is_uv_available
from .version import is_newer


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


def perform_pypi_update(package_name: str) -> tuple[bool, str]:
    """Upgrade via uv tool upgrade.

    Args:
        package_name: Name of package to upgrade

    Returns:
        Tuple of (success, message)
    """
    if not is_uv_available():
        return False, UV_NOT_FOUND_ERROR

    try:
        result = subprocess.run(
            ["uv", "tool", "upgrade", package_name],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, "Upgrade successful"

        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = "Upgrade failed with no error message"

        return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Upgrade timed out after 60 seconds"
    except Exception as e:
        return False, f"Unexpected error: {e}"
