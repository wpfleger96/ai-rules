"""Update checking and application utilities."""

import json
import re
import subprocess
import urllib.request

from dataclasses import dataclass
from pathlib import Path

from .detection import UV_NOT_FOUND_ERROR, InstallationInfo, is_uv_available
from .installer import install_tool
from .version import is_newer


def _get_default_branch(repo_path: Path) -> str:
    """Detect the default branch for a git repository.

    Args:
        repo_path: Path to git repository

    Returns:
        Branch name (e.g., "main", "master"), defaults to "main" on error
    """
    try:
        # Try to get the current branch name
        result = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

        # Fallback: get remote HEAD symbolic ref
        result = subprocess.run(
            ["git", "-C", str(repo_path), "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Output is like "refs/remotes/origin/main"
            ref = result.stdout.strip()
            if ref.startswith("refs/remotes/origin/"):
                return ref.replace("refs/remotes/origin/", "")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Default fallback
    return "main"


@dataclass
class UpdateInfo:
    """Information about available updates."""

    has_update: bool
    current_version: str
    latest_version: str
    source: str  # "git" or "pypi"


def check_git_updates(repo_path: Path) -> UpdateInfo:
    """Check if git repo has remote updates.

    Args:
        repo_path: Path to git repository

    Returns:
        UpdateInfo with update status
    """
    try:
        # Detect default branch
        default_branch = _get_default_branch(repo_path)

        # Fetch latest from remote
        subprocess.run(
            ["git", "-C", str(repo_path), "fetch", "origin"],
            capture_output=True,
            timeout=10,
            check=True,
        )

        # Get current commit
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        current_commit = result.stdout.strip()

        # Get remote HEAD commit
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", f"origin/{default_branch}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        remote_commit = result.stdout.strip()

        has_update = current_commit != remote_commit

        # Try to get version tags for display
        current_version = current_commit[:7]
        latest_version = remote_commit[:7]

        # Try to get semantic version from tags
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                current_version = result.stdout.strip()

            if has_update:
                result = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo_path),
                        "describe",
                        "--tags",
                        "--abbrev=0",
                        f"origin/{default_branch}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    latest_version = result.stdout.strip()
        except subprocess.TimeoutExpired:
            pass

        return UpdateInfo(
            has_update=has_update,
            current_version=current_version,
            latest_version=latest_version,
            source="git",
        )

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        # Return no update on error
        return UpdateInfo(
            has_update=False,
            current_version="unknown",
            latest_version="unknown",
            source="git",
        )


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


def perform_git_update(repo_path: Path) -> tuple[bool, str]:
    """Pull latest changes from git remote.

    Args:
        repo_path: Path to git repository

    Returns:
        Tuple of (success, message)
    """
    try:
        # Detect default branch
        default_branch = _get_default_branch(repo_path)

        result = subprocess.run(
            ["git", "-C", str(repo_path), "pull", "origin", default_branch],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, "Git pull successful"

        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = "Git pull failed with no error message"

        return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Git pull timed out after 30 seconds"
    except Exception as e:
        return False, f"Unexpected error: {e}"


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


def perform_update(info: InstallationInfo) -> tuple[bool, str]:
    """Perform update based on installation source.

    Args:
        info: Installation information from get_installation_info()

    Returns:
        Tuple of (success, message)
    """
    if info.source in ("git", "editable") and info.repo_path:
        # For git installs, pull and reinstall
        success, message = perform_git_update(info.repo_path)
        if not success:
            return False, message

        # Reinstall with --force
        success, message = install_tool(info, force=True)
        return success, message

    if info.source == "pypi":
        # For PyPI installs, use uv tool upgrade
        return perform_pypi_update(info.package_name)

    # Unknown installation source
    return False, f"Unknown installation source: {info.source}"
