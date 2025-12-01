"""Installation detection utilities."""

import json
import shutil
import subprocess

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

# Error message for missing uv tool
UV_NOT_FOUND_ERROR = "uv not found in PATH. Install from https://docs.astral.sh/uv/"


@dataclass
class InstallationInfo:
    """Information about how a package is installed."""

    source: str  # "git", "pypi", "editable", "unknown"
    package_path: Path  # Where the package is installed
    repo_path: Path | None  # Git repo root if applicable
    is_editable: bool
    package_name: str


def find_git_repo(path: Path) -> Path | None:
    """Find git repo root by walking up from path.

    Args:
        path: Starting path to search from

    Returns:
        Path to git repo root, or None if not in a git repo
    """
    current = path.resolve()

    # Walk up directory tree
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent

    return None


def is_editable_install(package_name: str) -> tuple[bool, Path | None]:
    """Check if package is installed in editable mode.

    Args:
        package_name: Name of package to check

    Returns:
        Tuple of (is_editable, editable_path)
    """
    try:
        dist = distribution(package_name)

        # Check for direct_url.json (PEP 610) which indicates editable install
        if dist.read_text("direct_url.json"):
            direct_url_file = dist._path / "direct_url.json"  # type: ignore
            if direct_url_file.exists():
                data = json.loads(direct_url_file.read_text())
                if data.get("dir_info", {}).get("editable", False):
                    url = data.get("url", "")
                    if url.startswith("file://"):
                        return True, Path(url[7:])

        # Fallback: check if location contains .egg-link or __editable__
        location_simple = dist.locate_file("")
        if location_simple:
            location = Path(str(location_simple))
            if (location.parent / f"{package_name}.egg-link").exists():
                return True, location
            # Check for __editable__ module
            for item in location.iterdir():
                if item.name.startswith("__editable__") and item.suffix == ".py":
                    return True, location

    except (PackageNotFoundError, OSError, json.JSONDecodeError):
        pass

    return False, None


def get_installation_info(package_name: str = "ai-rules") -> InstallationInfo:
    """Detect installation source and location.

    Args:
        package_name: Name of package to detect

    Returns:
        InstallationInfo with detected details

    Raises:
        PackageNotFoundError: If package is not installed
    """
    dist = distribution(package_name)
    package_path_simple = dist.locate_file("")

    if not package_path_simple:
        raise PackageNotFoundError(f"Could not locate {package_name}")

    package_path = Path(str(package_path_simple)).resolve()

    # Check for editable install
    is_edit, edit_path = is_editable_install(package_name)

    # Find git repo
    search_path = edit_path if edit_path else package_path
    repo_path = find_git_repo(search_path)

    # Determine source
    if is_edit:
        source = "editable"
    elif repo_path:
        source = "git"
    else:
        source = "pypi"

    return InstallationInfo(
        source=source,
        package_path=package_path,
        repo_path=repo_path,
        is_editable=is_edit,
        package_name=package_name,
    )


def is_tool_installed(command_name: str = "ai-rules") -> bool:
    """Check if command is available in PATH (installed via uv tool).

    Args:
        command_name: Command name to check (e.g., "ai-rules")

    Returns:
        True if command is in PATH, False otherwise
    """
    return shutil.which(command_name) is not None


def is_uv_available() -> bool:
    """Check if uv is available in PATH.

    Returns:
        True if uv is available, False otherwise
    """
    return shutil.which("uv") is not None


def get_uv_tool_dir() -> Path | None:
    """Get the directory where uv installs tools.

    Returns:
        Path to uv tool directory, or None if not found
    """
    try:
        result = subprocess.run(
            ["uv", "tool", "dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def get_existing_tool_info(command_name: str = "ai-rules") -> InstallationInfo | None:
    """Get installation info for an existing uv tool installation.

    This checks how a tool that's already installed via 'uv tool install'
    was configured (editable vs regular, git vs PyPI).

    Args:
        command_name: Command name to check (e.g., "ai-rules")

    Returns:
        InstallationInfo if tool is installed via uv, None otherwise
    """
    if not is_uv_available():
        return None

    try:
        # Get list of installed tools with paths
        result = subprocess.run(
            ["uv", "tool", "list", "--show-paths"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return None

        # Parse output to find our tool
        # Format is like:
        # ai-rules v0.3.0
        #     - ai-rules (/home/user/.local/share/uv/tools/ai-rules/bin/ai-rules)
        lines = result.stdout.strip().split("\n")
        tool_found = False
        venv_path = None

        for i, line in enumerate(lines):
            # Check if this line is the tool header
            if line.startswith(command_name):
                tool_found = True
                # Next line should have the path
                if i + 1 < len(lines):
                    path_line = lines[i + 1].strip()
                    if "(" in path_line and ")" in path_line:
                        # Extract path from: - ai-rules (/path/to/tool/bin/ai-rules)
                        path_start = path_line.index("(") + 1
                        path_end = path_line.index(")")
                        tool_exe_path = Path(path_line[path_start:path_end])
                        # Venv is parent directories up from bin/ai-rules
                        venv_path = tool_exe_path.parent.parent
                break

        if not tool_found or not venv_path:
            return None

        # Now check if the package in this venv is editable
        # The venv structure is: ~/.local/share/uv/tools/ai-rules/
        # Python packages are in: lib/pythonX.Y/site-packages/
        site_packages = None
        lib_dir = venv_path / "lib"
        if lib_dir.exists():
            for python_dir in lib_dir.iterdir():
                if python_dir.name.startswith("python"):
                    potential_site = python_dir / "site-packages"
                    if potential_site.exists():
                        site_packages = potential_site
                        break

        if not site_packages:
            return None

        # Check for editable install markers
        package_name = command_name
        is_edit = False
        edit_path = None
        repo_path = None

        # Check for direct_url.json
        dist_info = None
        for item in site_packages.iterdir():
            if item.name.startswith(
                f"{package_name.replace('-', '_')}-"
            ) and item.name.endswith(".dist-info"):
                dist_info = item
                break

        if dist_info:
            direct_url_file = dist_info / "direct_url.json"
            if direct_url_file.exists():
                data = json.loads(direct_url_file.read_text())
                if data.get("dir_info", {}).get("editable", False):
                    is_edit = True
                    url = data.get("url", "")
                    if url.startswith("file://"):
                        edit_path = Path(url[7:])
                        repo_path = find_git_repo(edit_path)

        # Determine source
        if is_edit:
            source = "editable"
        elif repo_path:
            source = "git"
        else:
            source = "pypi"

        return InstallationInfo(
            source=source,
            package_path=site_packages,
            repo_path=repo_path,
            is_editable=is_edit,
            package_name=package_name,
        )

    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
        json.JSONDecodeError,
    ):
        return None
