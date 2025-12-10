"""Cursor editor agent implementation."""

import sys

from functools import cached_property
from pathlib import Path

from ai_rules.agents.base import Agent


def _get_cursor_target_prefix() -> str:
    """Get platform-specific Cursor config path with ~ prefix.

    Returns:
        Path string with ~ prefix for the current platform:
        - macOS: ~/Library/Application Support/Cursor/User
        - Windows: ~/AppData/Roaming/Cursor/User
        - Linux/WSL: ~/.config/Cursor/User
    """
    if sys.platform == "darwin":
        return "~/Library/Application Support/Cursor/User"
    elif sys.platform == "win32":
        return "~/AppData/Roaming/Cursor/User"
    else:  # Linux/WSL
        return "~/.config/Cursor/User"


class CursorAgent(Agent):
    """Agent for Cursor editor configuration."""

    @property
    def name(self) -> str:
        return "Cursor"

    @property
    def agent_id(self) -> str:
        return "cursor"

    @property
    def config_file_name(self) -> str:
        return "settings.json"

    @property
    def config_file_format(self) -> str:
        return "json"

    @cached_property
    def symlinks(self) -> list[tuple[Path, Path]]:
        """Cached list of all Cursor symlinks.

        Settings file uses cache-based approach with override merging.
        Keybindings file uses direct symlink (array structure, no merging).
        """
        result = []
        prefix = _get_cursor_target_prefix()

        # Settings file - use cache if overrides exist
        settings_file = self.config_dir / "cursor" / "settings.json"
        if settings_file.exists():
            target_file = self.config.get_settings_file_for_symlink(
                "cursor", settings_file
            )
            result.append((Path(f"{prefix}/settings.json"), target_file))

        # Keybindings file - direct symlink (no override merging for arrays)
        keybindings_file = self.config_dir / "cursor" / "keybindings.json"
        if keybindings_file.exists():
            result.append((Path(f"{prefix}/keybindings.json"), keybindings_file))

        return result
