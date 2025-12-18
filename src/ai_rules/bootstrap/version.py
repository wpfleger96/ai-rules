"""Version utilities for package management."""

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
