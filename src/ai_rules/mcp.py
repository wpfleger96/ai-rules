"""MCP server management."""

import copy
import json
import shutil
import tempfile

from datetime import datetime
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any, cast

from .config import Config
from .utils import deep_merge


class OperationResult(Enum):
    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    ALREADY_SYNCED = "already_synced"
    NOT_FOUND = "not_found"
    ERROR = "error"


class MCPStatus:
    def __init__(self) -> None:
        self.managed_mcps: dict[str, dict[str, Any]] = {}
        self.unmanaged_mcps: dict[str, dict[str, Any]] = {}
        self.pending_mcps: dict[str, dict[str, Any]] = {}
        self.stale_mcps: dict[str, dict[str, Any]] = {}
        self.synced: dict[str, bool] = {}
        self.has_overrides: dict[str, bool] = {}


MANAGED_BY_KEY = "_managedBy"
MANAGED_BY_VALUE = "ai-rules"


class MCPManager:
    BACKUP_SUFFIX = "ai-rules-backup"

    @property
    def CLAUDE_JSON(self) -> Path:
        return Path.home() / ".claude.json"

    def load_managed_mcps(self, config_dir: Path, config: Config) -> dict[str, Any]:
        """Load managed MCP definitions and apply user overrides.

        Args:
            config_dir: Config directory path
            config: Config instance with user overrides

        Returns:
            Dictionary of MCP name -> MCP config (with overrides applied)
        """
        mcps_file = config_dir / "claude" / "mcps.json"
        if not mcps_file.exists():
            return {}

        with open(mcps_file) as f:
            base_mcps = json.load(f)

        mcp_overrides = config.mcp_overrides if hasattr(config, "mcp_overrides") else {}

        merged_mcps = {}
        for name, _mcp_config in {**base_mcps, **mcp_overrides}.items():
            if name in base_mcps and name in mcp_overrides:
                merged_mcps[name] = deep_merge(base_mcps[name], mcp_overrides[name])
            elif name in base_mcps:
                merged_mcps[name] = copy.deepcopy(base_mcps[name])
            else:
                merged_mcps[name] = copy.deepcopy(mcp_overrides[name])

        return merged_mcps

    @cached_property
    def claude_json(self) -> dict[str, Any]:
        """Cached ~/.claude.json file contents.

        Returns:
            Dictionary containing Claude Code config
        """
        if not self.CLAUDE_JSON.exists():
            return {}

        with open(self.CLAUDE_JSON) as f:
            return cast(dict[str, Any], json.load(f))

    def invalidate_cache(self) -> None:
        """Clear cached claude_json after writes to ensure fresh reads."""
        if "claude_json" in self.__dict__:
            del self.__dict__["claude_json"]

    def save_claude_json(self, data: dict[str, Any]) -> None:
        """Save ~/.claude.json file atomically.

        Args:
            data: Dictionary to save
        """
        self.CLAUDE_JSON.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=self.CLAUDE_JSON.parent, prefix=f".{self.CLAUDE_JSON.name}."
        )
        try:
            with open(fd, "w") as f:
                json.dump(data, f, indent=2)

            if self.CLAUDE_JSON.exists():
                shutil.copystat(self.CLAUDE_JSON, temp_path)

            shutil.move(temp_path, self.CLAUDE_JSON)

            # Invalidate cache after write
            self.invalidate_cache()
        except Exception:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

    def create_backup(self) -> Path | None:
        """Create a timestamped backup of ~/.claude.json.

        Returns:
            Path to backup file, or None if source doesn't exist
        """
        if not self.CLAUDE_JSON.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.CLAUDE_JSON.with_suffix(
            f"{self.CLAUDE_JSON.suffix}.{self.BACKUP_SUFFIX}.{timestamp}"
        )
        shutil.copy2(self.CLAUDE_JSON, backup_path)
        return backup_path

    def detect_conflicts(
        self, expected: dict[str, Any], installed: dict[str, Any]
    ) -> list[str]:
        """Detect MCPs that have been modified locally.

        Args:
            expected: Expected MCP configs from repo
            installed: Currently installed MCP configs

        Returns:
            List of MCP names that differ
        """
        conflicts = []
        for name, expected_config in expected.items():
            if name in installed:
                expected_without_marker = {
                    k: v for k, v in expected_config.items() if k != MANAGED_BY_KEY
                }
                installed_without_marker = {
                    k: v for k, v in installed[name].items() if k != MANAGED_BY_KEY
                }
                if expected_without_marker != installed_without_marker:
                    conflicts.append(name)
        return conflicts

    def format_diff(
        self, name: str, expected: dict[str, Any], installed: dict[str, Any]
    ) -> str:
        """Format a diff between expected and installed MCP config.

        Args:
            name: MCP name
            expected: Expected config
            installed: Installed config

        Returns:
            Formatted diff string
        """
        import difflib

        expected_json = json.dumps(expected, indent=2)
        installed_json = json.dumps(installed, indent=2)

        expected_lines = expected_json.splitlines(keepends=True)
        installed_lines = installed_json.splitlines(keepends=True)

        diff = difflib.unified_diff(
            expected_lines,
            installed_lines,
            fromfile="Expected (repo)",
            tofile="Installed (local)",
            lineterm="",
        )

        return f"MCP '{name}' has been modified locally:\n" + "".join(diff)

    def install_mcps(
        self,
        config_dir: Path,
        config: Config,
        force: bool = False,
        dry_run: bool = False,
    ) -> tuple[OperationResult, str, list[str]]:
        """Install managed MCPs into ~/.claude.json.

        Auto-removes MCPs that were previously tracked but are no longer in current config.

        Args:
            config_dir: Config directory path
            config: Config instance with user overrides
            force: Skip confirmation prompts
            dry_run: Don't actually modify files

        Returns:
            Tuple of (result, message, conflicts_list)
        """
        managed_mcps = self.load_managed_mcps(config_dir, config)

        for _name, mcp_config in managed_mcps.items():
            mcp_config[MANAGED_BY_KEY] = MANAGED_BY_VALUE

        claude_data = self.claude_json
        current_mcps = claude_data.get("mcpServers", {})

        tracked_mcps = {
            name
            for name, cfg in current_mcps.items()
            if cfg.get(MANAGED_BY_KEY) == MANAGED_BY_VALUE
        }
        removed_mcps = tracked_mcps - set(managed_mcps.keys())

        if not managed_mcps and not removed_mcps:
            return (
                OperationResult.NOT_FOUND,
                "No MCPs to install or remove",
                [],
            )

        conflicts = self.detect_conflicts(managed_mcps, current_mcps)

        if conflicts and not force:
            return (
                OperationResult.ERROR,
                "Conflicts detected (use --force to override)",
                conflicts,
            )

        if dry_run:
            msg = f"Would update {len(managed_mcps)} MCPs, remove {len(removed_mcps)}"
            return (OperationResult.UPDATED, msg, conflicts)

        if not managed_mcps and not removed_mcps:
            new_tracking = set(managed_mcps.keys())
            if tracked_mcps == new_tracking:
                return (OperationResult.ALREADY_SYNCED, "MCPs are already synced", [])

        backup_path = self.create_backup() if (managed_mcps or removed_mcps) else None

        for name in removed_mcps:
            current_mcps.pop(name, None)

        claude_data.setdefault("mcpServers", {})
        claude_data["mcpServers"].update(managed_mcps)

        self.save_claude_json(claude_data)

        parts = []
        if managed_mcps:
            parts.append(f"installed {len(managed_mcps)}")
        if removed_mcps:
            parts.append(f"removed {len(removed_mcps)}")
        msg = f"MCPs {', '.join(parts)}"
        if backup_path:
            msg += f" (backup: {backup_path})"

        return (OperationResult.UPDATED, msg, [])

    def uninstall_mcps(
        self, force: bool = False, dry_run: bool = False
    ) -> tuple[OperationResult, str]:
        """Uninstall managed MCPs from ~/.claude.json.

        Args:
            force: Skip confirmation prompts
            dry_run: Don't actually modify files

        Returns:
            Tuple of (result, message)
        """
        claude_data = self.claude_json
        if not claude_data or "mcpServers" not in claude_data:
            return (OperationResult.NOT_FOUND, "No MCPs found in ~/.claude.json")

        current_mcps = claude_data["mcpServers"]
        tracked_mcps = {
            name
            for name, cfg in current_mcps.items()
            if cfg.get(MANAGED_BY_KEY) == MANAGED_BY_VALUE
        }

        if not tracked_mcps:
            return (OperationResult.NOT_FOUND, "No tracked MCPs found")

        if dry_run:
            return (
                OperationResult.REMOVED,
                f"Would remove {len(tracked_mcps)} MCPs (dry run)",
            )

        backup_path = self.create_backup()

        for name in tracked_mcps:
            current_mcps.pop(name, None)

        self.save_claude_json(claude_data)

        backup_msg = f" (backup: {backup_path})" if backup_path else ""
        return (
            OperationResult.REMOVED,
            f"Removed {len(tracked_mcps)} MCPs{backup_msg}",
        )

    def get_status(self, config_dir: Path, config: Config) -> MCPStatus:
        """Get status of managed and unmanaged MCPs.

        Args:
            config_dir: Config directory path
            config: Config instance

        Returns:
            MCPStatus object with categorized MCPs
        """
        self.invalidate_cache()

        status = MCPStatus()
        managed_mcps = self.load_managed_mcps(config_dir, config)

        for _name, mcp_config in managed_mcps.items():
            mcp_config[MANAGED_BY_KEY] = MANAGED_BY_VALUE

        claude_data = self.claude_json
        installed_mcps = claude_data.get("mcpServers", {})

        mcp_overrides = config.mcp_overrides if hasattr(config, "mcp_overrides") else {}

        for name, mcp_config in installed_mcps.items():
            if mcp_config.get(MANAGED_BY_KEY) == MANAGED_BY_VALUE:
                if name in managed_mcps:
                    status.managed_mcps[name] = mcp_config
                    expected_config = managed_mcps.get(name, {})
                    expected_without_marker = {
                        k: v for k, v in expected_config.items() if k != MANAGED_BY_KEY
                    }
                    installed_without_marker = {
                        k: v for k, v in mcp_config.items() if k != MANAGED_BY_KEY
                    }
                    status.synced[name] = (
                        expected_without_marker == installed_without_marker
                    )
                    status.has_overrides[name] = name in mcp_overrides
                else:
                    status.stale_mcps[name] = mcp_config
            else:
                status.unmanaged_mcps[name] = mcp_config

        for name, mcp_config in managed_mcps.items():
            if name not in installed_mcps:
                status.pending_mcps[name] = mcp_config
                status.has_overrides[name] = name in mcp_overrides

        return status
