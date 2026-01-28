"""Claude Code extensions (agents, commands, hooks) status management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai_rules.utils import is_managed_target


@dataclass
class ExtensionItem:
    """Status of a single Claude extension (agent, command, skill, or hook)."""

    name: str
    target_path: Path
    actual_source: Path | None
    expected_source: Path | None
    is_symlink: bool
    is_managed: bool
    is_installed: bool
    is_broken: bool


@dataclass
class ExtensionTypeStatus:
    """Status of one extension type (agents, commands, skills, or hooks)."""

    managed_installed: dict[str, ExtensionItem] = field(default_factory=dict)
    managed_pending: dict[str, ExtensionItem] = field(default_factory=dict)
    managed_wrong_target: dict[str, ExtensionItem] = field(default_factory=dict)
    unmanaged: dict[str, ExtensionItem] = field(default_factory=dict)


@dataclass
class ClaudeExtensionStatus:
    """Complete status of Claude Code extensions (agents, commands, hooks only)."""

    agents: ExtensionTypeStatus = field(default_factory=ExtensionTypeStatus)
    commands: ExtensionTypeStatus = field(default_factory=ExtensionTypeStatus)
    hooks: ExtensionTypeStatus = field(default_factory=ExtensionTypeStatus)


class ClaudeExtensionManager:
    """Manages Claude Code extensions (agents, commands, skills, hooks)."""

    USER_DIRS = {
        "agents": Path("~/.claude/agents"),
        "commands": Path("~/.claude/commands"),
        "hooks": Path("~/.claude/hooks"),
    }

    PATTERNS = {
        "agents": "*.md",
        "commands": "*.md",
        "hooks": "*.py",
    }

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir

    def _get_managed_extensions(self, ext_type: str) -> dict[str, Path]:
        """Get all managed extensions of a type from config_dir."""
        source_dir = self.config_dir / "claude" / ext_type
        if not source_dir.exists():
            return {}

        result = {}
        pattern = self.PATTERNS[ext_type]
        for item in sorted(source_dir.glob(pattern)):
            result[item.stem] = item
        return result

    def _scan_installed_extensions(
        self, ext_type: str
    ) -> dict[str, tuple[Path, Path | None, bool]]:
        """Scan user directory for installed extensions.

        Returns:
            dict mapping name -> (target_path, symlink_source_or_none, is_broken)
        """
        user_dir = self.USER_DIRS[ext_type].expanduser()
        if not user_dir.exists():
            return {}

        result = {}
        pattern = self.PATTERNS[ext_type]
        for item in sorted(user_dir.glob(pattern)):
            name = item.stem

            if item.is_symlink():
                try:
                    source = item.resolve()
                    is_broken = not source.exists()
                except (OSError, RuntimeError):
                    source = None
                    is_broken = True
                result[name] = (item, source, is_broken)
            else:
                result[name] = (item, None, False)

        return result

    def get_orphaned_symlinks(
        self,
        user_dir: Path,
        pattern: str,
        is_directory: bool = False,
    ) -> dict[str, Path]:
        """Get symlinks that point to ai-rules but source no longer exists.

        Works for any symlink-based config type (commands, agents, skills, etc.)

        Args:
            user_dir: Directory containing user symlinks (e.g., ~/.claude/commands)
            pattern: Glob pattern (e.g., "*.md", "*" for directories)
            is_directory: True if expecting directory symlinks (skills)

        Returns:
            dict mapping name -> symlink path for orphaned items
        """
        user_dir = user_dir.expanduser()
        if not user_dir.exists():
            return {}

        orphaned = {}
        for item in user_dir.glob(pattern):
            if not item.is_symlink():
                continue

            if is_directory and not item.is_dir():
                continue
            if not is_directory and item.is_dir():
                continue

            try:
                target = item.resolve()
                if is_managed_target(target, self.config_dir) and not target.exists():
                    orphaned[item.stem if not is_directory else item.name] = item
            except (OSError, RuntimeError):
                try:
                    raw_target = str(item.readlink())
                    if "ai_rules/config" in raw_target or "ai-rules" in raw_target:
                        orphaned[item.stem if not is_directory else item.name] = item
                except (OSError, RuntimeError):
                    pass

        return orphaned

    def get_all_orphaned(self) -> dict[str, dict[str, Path]]:
        """Get all orphaned symlinks across all extension types."""
        return {
            "commands": self.get_orphaned_symlinks(Path("~/.claude/commands"), "*.md"),
            "agents": self.get_orphaned_symlinks(Path("~/.claude/agents"), "*.md"),
        }

    def _get_configured_hooks(self, settings: dict[str, Any]) -> set[str]:
        """Get set of hook filenames that have configurations in settings.

        Scans settings['hooks'] for any command that references a file in ~/.claude/hooks/.

        Args:
            settings: Merged settings dict containing hooks configuration

        Returns:
            Set of hook filenames (e.g., {'subagentStop.py', 'skillRouter.py'})
        """
        import re

        configured = set()
        hooks_config = settings.get("hooks", {})

        for event_handlers in hooks_config.values():
            for handler in event_handlers:
                for hook in handler.get("hooks", []):
                    if hook.get("type") == "command":
                        command = hook.get("command", "")
                        if (
                            "~/.claude/hooks/" in command
                            or "/.claude/hooks/" in command
                        ):
                            match = re.search(
                                r"[~/.]*/\.claude/hooks/(\w+\.py)", command
                            )
                            if match:
                                configured.add(match.group(1))

        return configured

    def get_orphaned_hooks(self, settings: dict[str, Any]) -> dict[str, Path]:
        """Get hooks that are installed but have no configuration OR source missing.

        Args:
            settings: Merged settings dict to check for hook configurations

        Returns:
            dict mapping hook name -> installed path for orphaned hooks
        """
        orphaned = self.get_orphaned_symlinks(Path("~/.claude/hooks"), "*.py")

        configured_hooks = self._get_configured_hooks(settings)
        user_hooks_dir = Path("~/.claude/hooks").expanduser()
        if user_hooks_dir.exists():
            for hook_file in user_hooks_dir.glob("*.py"):
                if hook_file.is_symlink() and hook_file.name not in configured_hooks:
                    try:
                        target = hook_file.resolve()
                        if is_managed_target(target, self.config_dir):
                            orphaned[hook_file.stem] = hook_file
                    except (OSError, RuntimeError):
                        pass

        return orphaned

    def get_status(self) -> ClaudeExtensionStatus:
        """Get comprehensive status of Claude extensions (agents, commands, hooks)."""
        status = ClaudeExtensionStatus()

        for ext_type in ["agents", "commands", "hooks"]:
            type_status = getattr(status, ext_type)
            managed_sources = self._get_managed_extensions(ext_type)
            installed = self._scan_installed_extensions(ext_type)

            for name, expected_source in managed_sources.items():
                if name in installed:
                    target_path, actual_source, is_broken = installed[name]

                    if is_broken:
                        type_status.managed_wrong_target[name] = ExtensionItem(
                            name=name,
                            target_path=target_path,
                            actual_source=None,
                            expected_source=expected_source,
                            is_symlink=True,
                            is_managed=True,
                            is_installed=False,
                            is_broken=True,
                        )
                    elif actual_source and actual_source == expected_source.resolve():
                        type_status.managed_installed[name] = ExtensionItem(
                            name=name,
                            target_path=target_path,
                            actual_source=actual_source,
                            expected_source=expected_source,
                            is_symlink=True,
                            is_managed=True,
                            is_installed=True,
                            is_broken=False,
                        )
                    else:
                        type_status.managed_wrong_target[name] = ExtensionItem(
                            name=name,
                            target_path=target_path,
                            actual_source=actual_source,
                            expected_source=expected_source,
                            is_symlink=actual_source is not None,
                            is_managed=True,
                            is_installed=False,
                            is_broken=False,
                        )
                else:
                    if ext_type == "hooks":
                        filename = f"{name}.py"
                    else:
                        filename = f"{name}.md"

                    user_path = self.USER_DIRS[ext_type].expanduser() / filename
                    type_status.managed_pending[name] = ExtensionItem(
                        name=name,
                        target_path=user_path,
                        actual_source=None,
                        expected_source=expected_source,
                        is_symlink=False,
                        is_managed=True,
                        is_installed=False,
                        is_broken=False,
                    )

            for name, (target_path, actual_source, is_broken) in installed.items():
                if name not in managed_sources:
                    type_status.unmanaged[name] = ExtensionItem(
                        name=name,
                        target_path=target_path,
                        actual_source=actual_source,
                        expected_source=None,
                        is_symlink=actual_source is not None,
                        is_managed=False,
                        is_installed=False,
                        is_broken=is_broken,
                    )

        return status
