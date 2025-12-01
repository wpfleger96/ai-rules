"""Version utilities for package management."""

from importlib.metadata import version as get_version

from packaging.version import InvalidVersion, Version


def parse_version(version_str: str) -> Version:
    """Parse version string, handling 'v' prefix.

    Args:
        version_str: Version string (e.g., "1.2.3" or "v1.2.3")

    Returns:
        Parsed Version object

    Raises:
        InvalidVersion: If version string is malformed
    """
    clean = version_str.lstrip("v")
    return Version(clean)


def is_newer(latest: str, current: str) -> bool:
    """Check if latest version is newer than current.

    Args:
        latest: Latest version string
        current: Current version string

    Returns:
        True if latest is newer, False otherwise
    """
    try:
        return parse_version(latest) > parse_version(current)
    except InvalidVersion:
        return False


def get_package_version(package_name: str) -> str:
    """Get installed version of a package.

    Args:
        package_name: Name of the package (e.g., "ai-rules")

    Returns:
        Version string (e.g., "0.3.0")

    Raises:
        PackageNotFoundError: If package is not installed
    """
    return get_version(package_name)
