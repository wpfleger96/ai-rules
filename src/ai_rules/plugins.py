"""Claude Code plugin management."""

import json
import subprocess

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class OperationResult(Enum):
    SUCCESS = "success"
    ALREADY_INSTALLED = "already_installed"
    NOT_FOUND = "not_found"
    ERROR = "error"
    DRY_RUN = "dry_run"


@dataclass
class PluginStatus:
    """Status of plugin synchronization."""

    installed: dict[str, dict[str, Any]] = field(default_factory=dict)
    pending: list[dict[str, str]] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    marketplaces_missing: list[dict[str, str]] = field(default_factory=list)
    marketplaces_present: list[str] = field(default_factory=list)


@dataclass
class MarketplaceConfig:
    name: str
    source: str


@dataclass
class PluginConfig:
    name: str
    marketplace: str

    @property
    def key(self) -> str:
        """Return the plugin key in name@marketplace format."""
        return f"{self.name}@{self.marketplace}"


class PluginManager:
    """Manages Claude Code plugins via CLI."""

    INSTALLED_PLUGINS_PATH = (
        Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    )
    KNOWN_MARKETPLACES_PATH = (
        Path.home() / ".claude" / "plugins" / "known_marketplaces.json"
    )
    CLI_TIMEOUT = 30

    def is_cli_available(self) -> bool:
        """Check if claude CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=self.CLI_TIMEOUT,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def load_installed_plugins(self) -> dict[str, Any]:
        """Load currently installed plugins from ~/.claude/plugins/installed_plugins.json."""
        if not self.INSTALLED_PLUGINS_PATH.exists():
            return {"version": 2, "plugins": {}}

        try:
            with open(self.INSTALLED_PLUGINS_PATH) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (OSError, json.JSONDecodeError):
            return {"version": 2, "plugins": {}}

    def load_known_marketplaces(self) -> list[str]:
        """Load known marketplaces from ~/.claude/plugins/known_marketplaces.json."""
        if not self.KNOWN_MARKETPLACES_PATH.exists():
            return []

        try:
            with open(self.KNOWN_MARKETPLACES_PATH) as f:
                data = json.load(f)
                return list(data.keys())
        except (OSError, json.JSONDecodeError):
            return []

    def add_marketplace(
        self, source: str, dry_run: bool = False
    ) -> tuple[OperationResult, str]:
        """Add a marketplace via CLI: claude plugin marketplace add <source>."""
        if dry_run:
            return (OperationResult.DRY_RUN, f"Would add marketplace: {source}")

        if not self.is_cli_available():
            return (OperationResult.ERROR, "claude CLI not found")

        try:
            result = subprocess.run(
                ["claude", "plugin", "marketplace", "add", source],
                capture_output=True,
                text=True,
                timeout=self.CLI_TIMEOUT,
            )

            if result.returncode == 0:
                return (OperationResult.SUCCESS, f"Added marketplace from {source}")
            else:
                return (
                    OperationResult.ERROR,
                    result.stderr.strip() or result.stdout.strip(),
                )
        except subprocess.TimeoutExpired:
            return (OperationResult.ERROR, f"Timeout adding marketplace {source}")
        except Exception as e:
            return (OperationResult.ERROR, f"Error adding marketplace: {e}")

    def install_plugin(
        self, name: str, marketplace: str, dry_run: bool = False
    ) -> tuple[OperationResult, str]:
        """Install a plugin via CLI: claude plugin install <name>@<marketplace>."""
        plugin_spec = f"{name}@{marketplace}"

        if dry_run:
            return (OperationResult.DRY_RUN, f"Would install {plugin_spec}")

        if not self.is_cli_available():
            return (OperationResult.ERROR, "claude CLI not found")

        try:
            result = subprocess.run(
                ["claude", "plugin", "install", plugin_spec],
                capture_output=True,
                text=True,
                timeout=self.CLI_TIMEOUT,
            )

            if result.returncode == 0:
                return (OperationResult.SUCCESS, f"Installed {plugin_spec}")
            elif (
                "already installed" in result.stderr.lower()
                or "already installed" in result.stdout.lower()
            ):
                return (OperationResult.ALREADY_INSTALLED, f"{name} already installed")
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return (OperationResult.ERROR, error_msg)
        except subprocess.TimeoutExpired:
            return (OperationResult.ERROR, f"Timeout installing {plugin_spec}")
        except Exception as e:
            return (OperationResult.ERROR, f"Error installing {plugin_spec}: {e}")

    def get_status(
        self,
        desired_plugins: list[PluginConfig],
        desired_marketplaces: list[MarketplaceConfig],
    ) -> PluginStatus:
        """Compare desired state with installed state."""
        status = PluginStatus()

        installed_data = self.load_installed_plugins()
        installed_plugins = installed_data.get("plugins", {})

        known_marketplaces = self.load_known_marketplaces()
        status.marketplaces_present = known_marketplaces

        for marketplace in desired_marketplaces:
            if marketplace.name not in known_marketplaces:
                status.marketplaces_missing.append(
                    {"name": marketplace.name, "source": marketplace.source}
                )

        desired_keys = {p.key for p in desired_plugins}
        installed_keys = set(installed_plugins.keys())

        for key, details in installed_plugins.items():
            status.installed[key] = details

        status.extra = list(installed_keys - desired_keys)

        for plugin in desired_plugins:
            plugin_key = plugin.key
            if plugin_key not in installed_keys:
                status.pending.append(
                    {"name": plugin.name, "marketplace": plugin.marketplace}
                )

        return status

    def sync_plugins(
        self,
        desired_plugins: list[PluginConfig],
        desired_marketplaces: list[MarketplaceConfig],
        dry_run: bool = False,
    ) -> tuple[OperationResult, str, list[str]]:
        """
        Sync plugins to match desired state.

        Returns:
            Tuple of (result, message, warnings)
        """
        warnings = []

        if not self.is_cli_available():
            return (
                OperationResult.ERROR,
                "claude CLI not found - cannot sync plugins",
                [],
            )

        known_marketplaces = self.load_known_marketplaces()
        for marketplace in desired_marketplaces:
            if marketplace.name not in known_marketplaces:
                result, msg = self.add_marketplace(marketplace.source, dry_run)
                if result == OperationResult.ERROR:
                    warnings.append(
                        f"Failed to add marketplace {marketplace.name}: {msg}"
                    )

        installed_data = self.load_installed_plugins()
        installed_plugins = installed_data.get("plugins", {})
        installed_keys = set(installed_plugins.keys())
        desired_keys = {p.key for p in desired_plugins}

        for extra in installed_keys - desired_keys:
            warnings.append(f"Plugin '{extra}' is installed but not in profile config")

        installed_count = 0
        for plugin in desired_plugins:
            plugin_key = plugin.key
            if plugin_key not in installed_keys:
                result, msg = self.install_plugin(
                    plugin.name, plugin.marketplace, dry_run
                )
                if result == OperationResult.SUCCESS:
                    installed_count += 1
                elif result == OperationResult.ALREADY_INSTALLED:
                    pass
                elif result == OperationResult.ERROR:
                    warnings.append(f"Failed to install {plugin.name}: {msg}")

        if dry_run:
            return (OperationResult.DRY_RUN, "Dry run completed", warnings)

        if installed_count == 0 and len(desired_plugins) > 0:
            return (
                OperationResult.ALREADY_INSTALLED,
                "All plugins already installed",
                warnings,
            )

        return (
            OperationResult.SUCCESS,
            f"Installed {installed_count} plugin(s)",
            warnings,
        )
