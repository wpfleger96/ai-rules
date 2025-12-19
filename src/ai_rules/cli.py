"""Command-line interface for ai-rules."""

import logging
import os
import subprocess
import sys

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from importlib.resources import files as resource_files
from pathlib import Path
from typing import Any

import click

logger = logging.getLogger(__name__)

from click.shell_completion import CompletionItem
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from ai_rules.agents.base import Agent
from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.cursor import CursorAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.agents.shared import SharedAgent
from ai_rules.config import (
    AGENT_CONFIG_METADATA,
    Config,
    parse_setting_path,
    validate_override_path,
)
from ai_rules.profiles import Profile
from ai_rules.symlinks import (
    SymlinkResult,
    check_symlink,
    create_symlink,
    remove_symlink,
)

console = Console()

try:
    __version__ = get_version("ai-agent-rules")
except PackageNotFoundError:
    __version__ = "dev"

_NON_INTERACTIVE_FLAGS = frozenset({"--dry-run", "--help", "-h"})

GIT_SUBPROCESS_TIMEOUT = 5


def get_config_dir() -> Path:
    """Get the config directory.

    Works in both development mode (git repo) and installed mode (PyPI package).
    Uses importlib.resources which handles both cases automatically.
    """
    try:
        config_resource = resource_files("ai_rules") / "config"
        return Path(str(config_resource))
    except Exception:
        return Path(__file__).parent / "config"


def get_git_repo_root() -> Path:
    """Get the git repository root directory.

    This only works in development mode when the code is in a git repository.
    For installed packages, this will fail - use get_config_dir() instead.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass

    raise RuntimeError(
        "Not in a git repository. For config access, use get_config_dir() instead."
    )


def get_agents(config_dir: Path, config: Config) -> list[Agent]:
    """Get all agent instances.

    Args:
        config_dir: Path to the config directory (use get_config_dir())
        config: Configuration object

    Returns:
        List of all available agent instances
    """
    return [
        ClaudeAgent(config_dir, config),
        CursorAgent(config_dir, config),
        GooseAgent(config_dir, config),
        SharedAgent(config_dir, config),
    ]


def complete_agents(
    ctx: click.Context, param: click.Parameter, incomplete: str
) -> list[CompletionItem]:
    """Dynamically discover and complete agent names for --agents option."""
    config_dir = get_config_dir()
    config = Config.load()
    agents = get_agents(config_dir, config)
    agent_ids = [agent.agent_id for agent in agents]

    return [CompletionItem(aid) for aid in agent_ids if aid.startswith(incomplete)]


def complete_profiles(
    ctx: click.Context, param: click.Parameter, incomplete: str
) -> list[CompletionItem]:
    """Dynamically complete profile names for --profile option."""
    from ai_rules.profiles import ProfileLoader

    loader = ProfileLoader()
    profiles = loader.list_profiles()

    return [CompletionItem(p) for p in profiles if p.startswith(incomplete)]


def detect_old_config_symlinks() -> list[tuple[Path, Path]]:
    """Detect symlinks pointing to old config/ location.

    Returns list of (symlink_path, old_target) tuples for broken symlinks.
    This is used for migration from v0.4.1 to v0.5.0 when config moved
    from repo root to src/ai_rules/config/.

    Optimization: For versions >= 0.5.0, only check top-level symlinks
    to avoid expensive recursive directory scanning.
    """
    from packaging.version import Version

    old_patterns = [
        "/config/AGENTS.md",
        "/config/claude/",
        "/config/goose/",
        "/config/chat_agent_hints.md",
    ]

    broken_symlinks = []

    check_paths = [
        Path.home() / ".claude",
        Path.home() / ".config" / "goose",
        Path.home() / "AGENTS.md",
    ]

    try:
        use_fast_check = Version(__version__) >= Version("0.5.0")
    except Exception:
        use_fast_check = False

    for base_path in check_paths:
        if not base_path.exists():
            continue

        if base_path.is_symlink():
            try:
                target = os.readlink(str(base_path))
                if any(pattern in str(target) for pattern in old_patterns):
                    if not base_path.resolve().exists():
                        broken_symlinks.append((base_path, Path(target)))
            except (OSError, ValueError):
                pass

        if base_path.is_dir() and not use_fast_check:
            for item in base_path.rglob("*"):
                if item.is_symlink():
                    try:
                        target = os.readlink(str(item))
                        if any(pattern in str(target) for pattern in old_patterns):
                            if not item.resolve().exists():
                                broken_symlinks.append((item, Path(target)))
                    except (OSError, ValueError):
                        pass

    return broken_symlinks


def select_agents(all_agents: list[Agent], filter_string: str | None) -> list[Agent]:
    """Select agents based on filter string.

    Args:
        all_agents: List of all available agents
        filter_string: Comma-separated agent IDs (e.g., "claude,goose") or None for all

    Returns:
        List of selected agents

    Raises:
        SystemExit: If no agents match the filter
    """
    if not filter_string:
        return all_agents

    requested_ids = {a.strip() for a in filter_string.split(",") if a.strip()}
    selected = [agent for agent in all_agents if agent.agent_id in requested_ids]

    if not selected:
        invalid_ids = requested_ids - {a.agent_id for a in all_agents}
        available_ids = [a.agent_id for a in all_agents]
        console.print(
            f"[red]Error:[/red] Invalid agent ID(s): {', '.join(sorted(invalid_ids))}\n"
            f"[dim]Available agents: {', '.join(available_ids)}[/dim]"
        )
        sys.exit(1)

    return selected


def format_summary(
    dry_run: bool,
    created: int,
    updated: int,
    skipped: int,
    excluded: int = 0,
    errors: int = 0,
) -> None:
    """Format and print operation summary.

    Args:
        dry_run: Whether this was a dry run
        created: Number of symlinks created
        updated: Number of symlinks updated
        skipped: Number of symlinks skipped
        excluded: Number of symlinks excluded by config
        errors: Number of errors encountered
    """
    console.print()
    if dry_run:
        console.print(
            f"[bold]Summary:[/bold] Would create {created}, "
            f"update {updated}, skip {skipped}"
        )
    else:
        console.print(
            f"[bold]Summary:[/bold] Created {created}, "
            f"updated {updated}, skipped {skipped}"
        )

    if excluded > 0:
        console.print(f"  ({excluded} excluded by config)")

    if errors > 0:
        console.print(f"  [red]{errors} error(s)[/red]")


def _display_pending_symlink_changes(agents: list[Agent]) -> bool:
    """Display what symlink changes will be made.

    Returns:
        True if changes were found and displayed, False otherwise
    """
    from ai_rules.symlinks import check_symlink

    found_changes = False

    for agent in agents:
        agent_changes = []
        for target, source in agent.get_filtered_symlinks():
            target_path = target.expanduser()
            status_code, _ = check_symlink(target_path, source)

            if status_code == "correct":
                continue

            found_changes = True
            if status_code == "missing":
                agent_changes.append(("create", target_path, source))
            elif status_code in ["wrong_target", "broken", "not_symlink"]:
                agent_changes.append(("update", target_path, source))

        if agent_changes:
            console.print(f"\n[bold]{agent.name}[/bold]")
            for action, target, source in agent_changes:
                if action == "create":
                    console.print(f"  [green]+[/green] Create: {target} → {source}")
                else:
                    console.print(f"  [yellow]↻[/yellow] Update: {target} → {source}")

    return found_changes


def check_first_run(agents: list[Agent], force: bool) -> bool:
    """Check if this is the first run and prompt user if needed.

    Returns:
        True if should continue, False if should abort
    """
    existing_files = []

    for agent in agents:
        for target, _ in agent.get_filtered_symlinks():
            target_path = target.expanduser()
            if target_path.exists() and not target_path.is_symlink():
                existing_files.append((agent.name, target_path))

    if not existing_files:
        return True

    if force:
        return True

    console.print("\n[yellow]Warning:[/yellow] Found existing configuration files:\n")
    for agent_name, path in existing_files:
        console.print(f"  [{agent_name}] {path}")

    console.print(
        "\n[dim]These will be replaced with symlinks (originals will be backed up).[/dim]\n"
    )

    return Confirm.ask("Continue?", default=False)


def _background_update_check() -> None:
    """Run update check in background thread for all registered tools.

    This runs silently and saves results for display on next CLI invocation.
    """
    from datetime import datetime

    from ai_rules.bootstrap import (
        UPDATABLE_TOOLS,
        check_tool_updates,
        load_auto_update_config,
        save_auto_update_config,
        save_pending_update,
    )

    try:
        for tool in UPDATABLE_TOOLS:
            update_info = check_tool_updates(tool)
            if update_info and update_info.has_update:
                save_pending_update(update_info, tool.tool_id)

        config = load_auto_update_config()
        config.last_check = datetime.now().isoformat()
        save_auto_update_config(config)
    except Exception as e:
        logger.debug(f"Background update check failed: {e}")


def _is_interactive_context() -> bool:
    """Determine if we're in an interactive CLI context.

    Returns False when prompts should be suppressed:
    - Click is in resilient_parsing mode (--help, shell completion)
    - Non-interactive flags are present (--dry-run, --help, -h)
    - stdin/stdout are not TTYs (piped or scripted)
    """
    import sys

    try:
        ctx = click.get_current_context(silent=True)
        if ctx and ctx.resilient_parsing:
            return False
    except RuntimeError:
        pass

    if _NON_INTERACTIVE_FLAGS & set(sys.argv):
        return False

    return sys.stdin.isatty() and sys.stdout.isatty()


def _check_pending_updates() -> None:
    """Check for and display pending update notifications.

    Shows interactive prompt in normal TTY contexts, non-interactive message
    for --help, --dry-run, or non-TTY contexts.
    """
    from ai_rules.bootstrap import (
        clear_all_pending_updates,
        get_tool_by_id,
        load_all_pending_updates,
    )

    try:
        pending = load_all_pending_updates()
        if not pending:
            return

        updates = []
        for tid, info in pending.items():
            tool = get_tool_by_id(tid)
            if tool:
                updates.append(
                    f"{tool.display_name} {info.current_version} → {info.latest_version}"
                )

        if not updates:
            return

        update_label = "Update available" if len(updates) == 1 else "Updates available"
        console.print(f"\n[cyan]{update_label}:[/cyan] {', '.join(updates)}")

        if _is_interactive_context():
            prompt = "Install now?" if len(updates) == 1 else "Install all updates?"
            if Confirm.ask(prompt, default=False):
                ctx = click.get_current_context()
                ctx.invoke(
                    upgrade, check=False, force=False, skip_install=False, only=None
                )
            else:
                console.print("[dim]Run 'ai-rules upgrade' when ready[/dim]")
        else:
            console.print("[dim]Run 'ai-rules upgrade' to install[/dim]")

        clear_all_pending_updates()
    except Exception as e:
        logger.debug(f"Failed to check pending updates: {e}")


def version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Custom version callback that also checks for updates.

    Args:
        ctx: Click context
        param: Click parameter
        value: Whether --version flag was provided
    """
    if not value or ctx.resilient_parsing:
        return

    console.print(f"ai-rules, version {__version__}")

    try:
        from ai_rules.bootstrap import get_tool_version, is_command_available

        if is_command_available("claude-statusline"):
            statusline_version = get_tool_version("claude-code-statusline")
            if statusline_version:
                console.print(f"statusline, version {statusline_version}")
            else:
                console.print(
                    "statusline, version [dim](installed, version unknown)[/dim]"
                )
    except Exception as e:
        logger.debug(f"Failed to get statusline version: {e}")

    try:
        from ai_rules.bootstrap import check_tool_updates, get_tool_by_id

        tool = get_tool_by_id("ai-rules")
        if tool:
            update_info = check_tool_updates(tool, timeout=3)
            if update_info and update_info.has_update:
                console.print(
                    f"\n[cyan]Update available:[/cyan] {update_info.current_version} → {update_info.latest_version}"
                )
                console.print("[dim]Run 'ai-rules upgrade' to install[/dim]")
    except Exception as e:
        logger.debug(f"Failed to check for updates in version callback: {e}")

    ctx.exit()


@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=version_callback,
    expose_value=False,
    is_eager=True,
    help="Show version and check for updates",
)
def main() -> None:
    """AI Rules - Manage user-level AI agent configurations."""
    import threading

    from ai_rules.bootstrap import load_auto_update_config, should_check_now

    _check_pending_updates()

    try:
        import os

        if "PYTEST_CURRENT_TEST" not in os.environ:
            config = load_auto_update_config()
            if config.enabled and should_check_now(config):
                thread = threading.Thread(target=_background_update_check, daemon=True)
                thread.start()
    except Exception:
        pass


def cleanup_deprecated_symlinks(
    selected_agents: list[Agent], config_dir: Path, force: bool, dry_run: bool
) -> int:
    """Remove deprecated symlinks that point to our config files.

    Args:
        selected_agents: List of agents to check for deprecated symlinks
        config_dir: Path to the config directory (repo/config)
        force: Skip confirmation prompts
        dry_run: Don't actually remove symlinks

    Returns:
        Count of removed symlinks
    """
    removed_count = 0
    agents_md = config_dir / "AGENTS.md"

    for agent in selected_agents:
        deprecated_paths = agent.get_deprecated_symlinks()

        for deprecated_path in deprecated_paths:
            target = deprecated_path.expanduser()

            if not target.exists() and not target.is_symlink():
                continue

            if not target.is_symlink():
                continue

            try:
                resolved = target.resolve()
                if resolved != agents_md:
                    continue
            except (OSError, RuntimeError):
                continue

            if dry_run:
                console.print(
                    f"  [yellow]Would remove deprecated:[/yellow] {deprecated_path}"
                )
                removed_count += 1
            else:
                success, message = remove_symlink(target, force=True)
                if success:
                    console.print(
                        f"  [dim]Cleaned up deprecated symlink:[/dim] {deprecated_path}"
                    )
                    removed_count += 1

    return removed_count


def install_user_symlinks(
    selected_agents: list[Agent], force: bool, dry_run: bool
) -> dict[str, int]:
    """Install user-level symlinks for all selected agents.

    Returns dict with keys: created, updated, skipped, excluded, errors
    """
    console.print("[bold cyan]User-Level Configuration[/bold cyan]")

    if selected_agents:
        config_dir = selected_agents[0].config_dir
        cleanup_deprecated_symlinks(selected_agents, config_dir, force, dry_run)

    created = updated = skipped = excluded = errors = 0

    for agent in selected_agents:
        console.print(f"\n[bold]{agent.name}[/bold]")

        filtered_symlinks = agent.get_filtered_symlinks()
        excluded_count = len(agent.symlinks) - len(filtered_symlinks)

        if excluded_count > 0:
            console.print(
                f"  [dim]({excluded_count} symlink(s) excluded by config)[/dim]"
            )
            excluded += excluded_count

        for target, source in filtered_symlinks:
            effective_force = force or not dry_run
            result, message = create_symlink(target, source, effective_force, dry_run)

            if result == SymlinkResult.CREATED:
                console.print(f"  [green]✓[/green] {target} → {source}")
                created += 1
            elif result == SymlinkResult.ALREADY_CORRECT:
                console.print(f"  [dim]•[/dim] {target} [dim](already correct)[/dim]")
            elif result == SymlinkResult.UPDATED:
                console.print(f"  [yellow]↻[/yellow] {target} → {source}")
                updated += 1
            elif result == SymlinkResult.SKIPPED:
                console.print(f"  [yellow]○[/yellow] {target} [dim](skipped)[/dim]")
                skipped += 1
            elif result == SymlinkResult.ERROR:
                console.print(f"  [red]✗[/red] {target}: {message}")
                errors += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "excluded": excluded,
        "errors": errors,
    }


@main.command()
@click.option("--github", is_flag=True, help="Install from GitHub instead of PyPI")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
@click.option("--skip-symlinks", is_flag=True, help="Skip symlink installation step")
@click.option("--skip-completions", is_flag=True, help="Skip shell completion setup")
@click.option(
    "--profile",
    default=None,
    shell_complete=complete_profiles,
    help="Profile to use (default: 'default')",
)
@click.pass_context
def setup(
    ctx: click.Context,
    github: bool,
    force: bool,
    dry_run: bool,
    skip_symlinks: bool,
    skip_completions: bool,
    profile: str | None,
) -> None:
    """One-time setup: install symlinks and make ai-rules available system-wide.

    This is the recommended way to install ai-rules for first-time users.

    Example:
        uvx ai-agent-rules setup
    """
    from ai_rules.bootstrap import (
        ensure_statusline_installed,
        get_tool_config_dir,
        install_tool,
    )
    from ai_rules.bootstrap.updater import (
        check_tool_updates,
        get_tool_by_id,
        perform_tool_upgrade,
    )

    console.print("[bold cyan]Step 1/3: Install ai-rules system-wide[/bold cyan]")
    console.print("This allows you to run 'ai-rules' from any directory.\n")

    statusline_result, statusline_message = ensure_statusline_installed(
        dry_run=dry_run, from_github=github
    )
    if statusline_result == "installed":
        if dry_run and statusline_message:
            console.print(f"[dim]{statusline_message}[/dim]")
        else:
            console.print("[green]✓[/green] Installed claude-statusline")
    elif statusline_result == "upgraded":
        console.print(
            f"[green]✓[/green] Upgraded claude-statusline ({statusline_message})"
        )
    elif statusline_result == "upgrade_available":
        console.print(f"[dim]{statusline_message}[/dim]")
    elif statusline_result == "failed":
        console.print(
            "[yellow]⚠[/yellow] Failed to install claude-statusline (continuing anyway)"
        )

    ai_rules_tool = get_tool_by_id("ai-rules")
    tool_install_success = False

    if ai_rules_tool and ai_rules_tool.is_installed():
        from ai_rules.bootstrap import ToolSource, get_tool_source, uninstall_tool

        current_source = get_tool_source(ai_rules_tool.package_name)
        desired_source = ToolSource.GITHUB if github else ToolSource.PYPI
        needs_source_switch = current_source != desired_source

        if needs_source_switch:
            source_name = "GitHub" if github else "PyPI"
            if dry_run:
                console.print(
                    f"[dim]Would switch ai-rules from {current_source.name if current_source else 'unknown'} to {source_name}[/dim]"
                )
                tool_install_success = True
            else:
                if not force and not Confirm.ask(
                    f"Switch ai-rules to {source_name} install?", default=True
                ):
                    console.print("[yellow]Skipped source switch[/yellow]")
                    tool_install_success = True
                else:
                    uninstall_success, _ = uninstall_tool(ai_rules_tool.package_name)
                    if uninstall_success:
                        success, message = install_tool(
                            "ai-agent-rules", from_github=github, force=True
                        )
                        if success:
                            console.print(
                                f"[green]✓[/green] Switched to {source_name} install"
                            )
                            tool_install_success = True
                        else:
                            console.print(
                                f"[red]Error:[/red] Failed to install: {message}"
                            )
                    else:
                        console.print(
                            "[red]Error:[/red] Failed to uninstall current version"
                        )
        else:
            try:
                update_info = check_tool_updates(ai_rules_tool, timeout=10)
                if update_info and update_info.has_update:
                    if dry_run:
                        console.print(
                            f"[dim]Would upgrade ai-rules {update_info.current_version} → {update_info.latest_version}[/dim]"
                        )
                        tool_install_success = True
                    else:
                        if not force and not Confirm.ask(
                            f"Upgrade ai-rules {update_info.current_version} → {update_info.latest_version}?",
                            default=True,
                        ):
                            console.print("[yellow]Skipped ai-rules upgrade[/yellow]")
                            tool_install_success = True
                        else:
                            success, msg, _ = perform_tool_upgrade(ai_rules_tool)
                            if success:
                                console.print(
                                    f"[green]✓[/green] Upgraded ai-rules ({update_info.current_version} → {update_info.latest_version})"
                                )
                                tool_install_success = True
                            else:
                                console.print(
                                    "[red]Error:[/red] Failed to upgrade ai-rules"
                                )
                else:
                    tool_install_success = True
            except Exception:
                pass

    if not tool_install_success:
        if not force and not dry_run:
            if not Confirm.ask("Install ai-rules permanently?", default=True):
                console.print(
                    "\n[yellow]Skipped.[/yellow] You can still run via: uvx ai-rules <command>"
                )
                return

        try:
            success, message = install_tool(
                "ai-agent-rules", from_github=github, force=force, dry_run=dry_run
            )

            if dry_run:
                console.print(f"[dim]{message}[/dim]")
                tool_install_success = True
            elif success:
                console.print("[green]✓[/green] Tool installed successfully")
                tool_install_success = True
            else:
                console.print(f"\n[red]Error:[/red] {message}")
                console.print("\n[yellow]Manual installation:[/yellow]")
                console.print("  uv tool install ai-agent-rules")
                return
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
            return

    if not skip_symlinks:
        console.print(
            "[bold cyan]Step 2/3: Installing AI agent configuration symlinks[/bold cyan]\n"
        )

        config_dir_override = None
        if tool_install_success and not dry_run:
            try:
                tool_config_dir = get_tool_config_dir("ai-agent-rules")
                if tool_config_dir.exists():
                    config_dir_override = str(tool_config_dir)
                else:
                    console.print(
                        f"[yellow]Warning:[/yellow] Tool config not found at expected location: {tool_config_dir}"
                    )
                    console.print(
                        "[dim]Falling back to current config directory[/dim]\n"
                    )
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Could not determine tool config path: {e}"
                )
                console.print("[dim]Falling back to current config directory[/dim]\n")

        ctx.invoke(
            install,
            force=force,
            dry_run=dry_run,
            rebuild_cache=False,
            agents=None,
            skip_completions=True,
            profile=profile,
            config_dir_override=config_dir_override,
        )

    if not skip_completions:
        from ai_rules.completions import (
            detect_shell,
            find_config_file,
            get_supported_shells,
            install_completion,
            is_completion_installed,
        )

        console.print("\n[bold cyan]Step 3/3: Shell completion setup[/bold cyan]\n")

        shell = detect_shell()
        if shell:
            config_path = find_config_file(shell)
            if config_path and is_completion_installed(config_path):
                console.print(f"[green]✓[/green] {shell} completion already installed")
            elif (
                force
                or dry_run
                or Confirm.ask(f"Install {shell} tab completion?", default=True)
            ):
                success, msg = install_completion(shell, dry_run=dry_run)
                if success:
                    console.print(f"[green]✓[/green] {msg}")
                else:
                    console.print(f"[yellow]⚠[/yellow] {msg}")
        else:
            supported = ", ".join(get_supported_shells())
            console.print(
                f"[dim]Shell completion not available for your shell (only {supported} supported)[/dim]"
            )

    if dry_run:
        console.print("\n[dim]Dry run complete - no changes were made.[/dim]")
    else:
        console.print("\n[green]✓ Setup complete![/green]")
        console.print("You can now run [bold]ai-rules[/bold] from anywhere.")


@main.command()
@click.option("--force", is_flag=True, help="Skip all confirmations")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option(
    "--rebuild-cache",
    is_flag=True,
    help="Rebuild merged settings cache (use after changing overrides)",
)
@click.option(
    "--agents",
    help="Comma-separated list of agents to install (default: all)",
    shell_complete=complete_agents,
)
@click.option(
    "--skip-completions",
    is_flag=True,
    help="Skip shell completion installation",
)
@click.option(
    "--profile",
    default=None,
    shell_complete=complete_profiles,
    help="Profile to use (default: 'default' for backward compatibility)",
)
@click.option(
    "--config-dir",
    "config_dir_override",
    hidden=True,
    help="Override config directory (internal use)",
)
def install(
    force: bool,
    dry_run: bool,
    rebuild_cache: bool,
    agents: str | None,
    skip_completions: bool,
    profile: str | None,
    config_dir_override: str | None = None,
) -> None:
    """Install AI agent configs via symlinks."""
    from ai_rules.bootstrap import ensure_statusline_installed

    statusline_result, statusline_message = ensure_statusline_installed(dry_run=dry_run)
    if statusline_result == "installed":
        if dry_run and statusline_message:
            console.print(f"[dim]{statusline_message}[/dim]\n")
        else:
            console.print("[green]✓[/green] Installed claude-statusline\n")
    elif statusline_result == "failed":
        console.print(
            "[yellow]⚠[/yellow] Failed to install claude-statusline (continuing anyway)\n"
        )

    if config_dir_override:
        config_dir = Path(config_dir_override)
        if not config_dir.exists():
            console.print(f"[red]Error:[/red] Config directory not found: {config_dir}")
            sys.exit(1)
    else:
        config_dir = get_config_dir()

    from ai_rules.profiles import ProfileLoader, ProfileNotFoundError
    from ai_rules.state import get_active_profile, set_active_profile

    if profile is None:
        profile = get_active_profile() or "default"

    if profile and not force:
        try:
            loader = ProfileLoader()
            profile_obj = loader.load_profile(profile)
            user_config = Config.load_user_config()
            profile_conflicts = _detect_profile_override_conflicts(
                profile_obj, user_config
            )
            if profile_conflicts:
                _handle_profile_conflicts(profile_conflicts, profile, user_config)
        except ProfileNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    try:
        config = Config.load(profile=profile)
    except ProfileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if not dry_run:
        set_active_profile(profile)

    if profile and profile != "default":
        console.print(f"[dim]Using profile: {profile}[/dim]\n")

    if rebuild_cache and not dry_run:
        import shutil

        cache_dir = Config.get_cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            console.print("[dim]✓ Cleared settings cache[/dim]")

    if not dry_run:
        claude_settings = config_dir / "claude" / "settings.json"
        if claude_settings.exists():
            config.build_merged_settings(
                "claude", claude_settings, force_rebuild=rebuild_cache
            )

        cursor_settings = config_dir / "cursor" / "settings.json"
        if cursor_settings.exists():
            config.build_merged_settings(
                "cursor", cursor_settings, force_rebuild=rebuild_cache
            )

        goose_settings = config_dir / "goose" / "config.yaml"
        if goose_settings.exists():
            config.build_merged_settings(
                "goose", goose_settings, force_rebuild=rebuild_cache
            )

    all_agents = get_agents(config_dir, config)
    selected_agents = select_agents(all_agents, agents)

    if not dry_run:
        old_symlinks = detect_old_config_symlinks()
        if old_symlinks:
            console.print(
                "\n[yellow]Detected config migration from v0.4.1 → v0.5.0[/yellow]"
            )
            console.print(
                f"Found {len(old_symlinks)} symlink(s) pointing to old config location"
            )
            console.print(
                "[dim]Automatically migrating symlinks to new location...[/dim]\n"
            )

            for symlink_path, _old_target in old_symlinks:
                try:
                    symlink_path.unlink()
                    console.print(f"  [dim]✓ Removed old symlink: {symlink_path}[/dim]")
                except Exception as e:
                    console.print(
                        f"  [yellow]⚠ Could not remove {symlink_path}: {e}[/yellow]"
                    )

            console.print("\n[green]✓ Migration complete[/green]")
            console.print("[dim]New symlinks will be created below...[/dim]\n")

    if not dry_run and not force:
        has_changes = _display_pending_symlink_changes(selected_agents)

        if has_changes:
            console.print()
            if not Confirm.ask("Apply these changes?", default=True):
                console.print("[yellow]Installation cancelled[/yellow]")
                sys.exit(0)
        elif not has_changes:
            if not check_first_run(selected_agents, force):
                console.print("[yellow]Installation cancelled[/yellow]")
                sys.exit(0)
    elif not dry_run and force:
        pass

    if dry_run:
        console.print("[bold]Dry run mode - no changes will be made[/bold]\n")

    if not dry_run:
        orphaned = config.cleanup_orphaned_cache()
        if orphaned:
            console.print(
                f"[dim]✓ Cleaned up orphaned cache for: {', '.join(orphaned)}[/dim]"
            )

    user_results = install_user_symlinks(selected_agents, force, dry_run)

    claude_agent = next((a for a in selected_agents if a.agent_id == "claude"), None)
    if claude_agent and isinstance(claude_agent, ClaudeAgent):
        from ai_rules.mcp import MCPManager, OperationResult

        result, message, conflicts = claude_agent.install_mcps(
            force=force, dry_run=dry_run
        )

        if conflicts and not force:
            console.print("\n[bold yellow]MCP Conflicts Detected:[/bold yellow]")
            mgr = MCPManager()
            expected_mcps = mgr.load_managed_mcps(config_dir, config)
            claude_data = mgr.claude_json
            installed_mcps = claude_data.get("mcpServers", {})

            for conflict_name in conflicts:
                expected = expected_mcps.get(conflict_name, {})
                installed = installed_mcps.get(conflict_name, {})
                if expected and installed:
                    diff = mgr.format_diff(conflict_name, expected, installed)
                    console.print(f"\n{diff}\n")

            if not dry_run and not Confirm.ask(
                "Overwrite local changes?", default=False
            ):
                console.print("[yellow]Skipped MCP installation[/yellow]")
            else:
                result, message, _ = claude_agent.install_mcps(
                    force=True, dry_run=dry_run
                )
                console.print(f"[green]✓[/green] {message}")
        elif result == OperationResult.UPDATED:
            console.print(f"[green]✓[/green] {message}")
        elif result == OperationResult.ALREADY_SYNCED:
            console.print(f"[dim]○[/dim] {message}")
        elif result != OperationResult.NOT_FOUND:
            console.print(f"[yellow]⚠[/yellow] {message}")

    total_created = user_results["created"]
    total_updated = user_results["updated"]
    total_skipped = user_results["skipped"]
    total_excluded = user_results["excluded"]
    total_errors = user_results["errors"]
    if not dry_run:
        try:
            git_repo_root = get_git_repo_root()
            hooks_dir = git_repo_root / ".hooks"
            post_merge_hook = hooks_dir / "post-merge"
            git_dir = git_repo_root / ".git"

            if post_merge_hook.exists() and git_dir.is_dir():
                import subprocess

                try:
                    subprocess.run(
                        ["git", "config", "core.hooksPath", ".hooks"],
                        cwd=git_repo_root,
                        check=True,
                        capture_output=True,
                        timeout=GIT_SUBPROCESS_TIMEOUT,
                    )
                    console.print("\n[dim]✓ Configured git hooks[/dim]")
                except subprocess.CalledProcessError:
                    pass
        except RuntimeError:
            pass

    if not skip_completions:
        from ai_rules.completions import detect_shell, install_completion

        shell = detect_shell()
        if shell:
            success, msg = install_completion(shell, dry_run=dry_run)
            if success and not dry_run:
                console.print(f"\n[dim]✓ {msg}[/dim]")

    format_summary(
        dry_run,
        total_created,
        total_updated,
        total_skipped,
        total_excluded,
        total_errors,
    )

    if total_errors > 0:
        sys.exit(1)


def _display_symlink_status(
    status_code: str,
    target: Path,
    source: Path,
    message: str,
    agent_label: str | None = None,
) -> bool:
    """Display symlink status with consistent formatting.

    Args:
        status_code: Status code from check_symlink()
        target: Target path to display
        source: Source path (to check if it's a directory)
        message: Status message
        agent_label: Optional agent label for project-level display

    Returns:
        True if status is correct, False otherwise
    """
    target_str = str(target)
    if source.is_dir():
        target_str = target_str.rstrip("/") + "/"
    target_display = f"{agent_label} {target.name}" if agent_label else target_str

    if status_code == "correct":
        console.print(f"  [green]✓[/green] {target_display}")
        return True
    elif status_code == "missing":
        console.print(f"  [red]✗[/red] {target_display} [dim](not installed)[/dim]")
        return False
    elif status_code == "broken":
        console.print(f"  [red]✗[/red] {target_display} [dim](broken symlink)[/dim]")
        return False
    elif status_code == "wrong_target":
        console.print(f"  [yellow]⚠[/yellow] {target_display} [dim]({message})[/dim]")
        return False
    elif status_code == "not_symlink":
        console.print(
            f"  [yellow]⚠[/yellow] {target_display} [dim](not a symlink)[/dim]"
        )
        return False
    return True


@main.command()
@click.option(
    "--agents",
    help="Comma-separated list of agents to check (default: all)",
    shell_complete=complete_agents,
)
def status(agents: str | None) -> None:
    """Check status of AI agent symlinks."""
    from ai_rules.state import get_active_profile

    config_dir = get_config_dir()
    config = Config.load()
    all_agents = get_agents(config_dir, config)
    selected_agents = select_agents(all_agents, agents)

    console.print("[bold]AI Rules Status[/bold]\n")

    active_profile = get_active_profile()
    if active_profile:
        console.print(f"[dim]Profile: {active_profile}[/dim]\n")

    all_correct = True

    console.print("[bold cyan]User-Level Configuration[/bold cyan]\n")
    cache_stale = False
    for agent in selected_agents:
        console.print(f"[bold]{agent.name}:[/bold]")

        all_symlinks = agent.symlinks
        filtered_symlinks = agent.get_filtered_symlinks()
        excluded_symlinks = [
            (t, s) for t, s in all_symlinks if (t, s) not in filtered_symlinks
        ]

        for target, source in filtered_symlinks:
            status_code, message = check_symlink(target, source)
            is_correct = _display_symlink_status(status_code, target, source, message)
            if not is_correct:
                all_correct = False

        for target, _ in excluded_symlinks:
            console.print(f"  [dim]○[/dim] {target} [dim](excluded by config)[/dim]")
        agent_config = AGENT_CONFIG_METADATA.get(agent.agent_id)
        if agent_config and agent.agent_id in config.settings_overrides:
            base_settings_path = (
                config_dir / agent.agent_id / agent_config["config_file"]
            )
            if config.is_cache_stale(agent.agent_id, base_settings_path):
                console.print("  [yellow]⚠[/yellow] Cached settings are stale")
                diff_output = config.get_cache_diff(agent.agent_id, base_settings_path)
                if diff_output:
                    console.print(diff_output)
                all_correct = False
                cache_stale = True

        if isinstance(agent, ClaudeAgent):
            mcp_status = agent.get_mcp_status()
            if (
                mcp_status.managed_mcps
                or mcp_status.unmanaged_mcps
                or mcp_status.pending_mcps
                or mcp_status.stale_mcps
            ):
                console.print("  [bold]MCPs:[/bold]")
                for name in sorted(mcp_status.managed_mcps.keys()):
                    synced = mcp_status.synced.get(name, False)
                    has_override = mcp_status.has_overrides.get(name, False)
                    status_text = (
                        "[green]Synced[/green]"
                        if synced
                        else "[yellow]Outdated[/yellow]"
                    )
                    override_text = ", override" if has_override else ""
                    console.print(
                        f"    {name:<20} {status_text} [dim](managed{override_text})[/dim]"
                    )
                    if not synced:
                        all_correct = False
                for name in sorted(mcp_status.pending_mcps.keys()):
                    has_override = mcp_status.has_overrides.get(name, False)
                    override_text = ", override" if has_override else ""
                    console.print(
                        f"    {name:<20} [yellow]Not installed[/yellow] [dim](managed{override_text})[/dim]"
                    )
                    all_correct = False
                for name in sorted(mcp_status.stale_mcps.keys()):
                    console.print(
                        f"    {name:<20} [red]Should be removed[/red] [dim](no longer in config)[/dim]"
                    )
                    all_correct = False
                for name in sorted(mcp_status.unmanaged_mcps.keys()):
                    console.print(f"    {name:<20} [dim]Unmanaged[/dim]")

        console.print()

    console.print("[bold cyan]Git Hooks Configuration[/bold cyan]\n")
    try:
        git_repo_root = get_git_repo_root()
        hooks_dir = git_repo_root / ".hooks"
        post_merge_hook = hooks_dir / "post-merge"

        if post_merge_hook.exists() and (git_repo_root / ".git").is_dir():
            import subprocess

            try:
                result = subprocess.run(
                    ["git", "config", "--get", "core.hooksPath"],
                    cwd=git_repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                configured_path = result.stdout.strip()
                if configured_path == ".hooks":
                    console.print("  [green]✓[/green] Post-merge hook configured")
                else:
                    console.print(
                        "  [red]✗[/red] Post-merge hook not configured\n"
                        "    [dim]Run 'uv run ai-rules install' to enable automatic reminders[/dim]"
                    )
                    all_correct = False
            except Exception:
                console.print(
                    "  [red]✗[/red] Post-merge hook not configured\n"
                    "    [dim]Run 'uv run ai-rules install' to enable automatic reminders[/dim]"
                )
                all_correct = False
        else:
            console.print(
                "  [dim]○[/dim] Post-merge hook not available in this repository"
            )
    except RuntimeError:
        console.print(
            "  [dim]○[/dim] Not in a git repository - git hooks not applicable"
        )

    console.print()

    console.print("[bold cyan]Optional Tools[/bold cyan]\n")
    from ai_rules.bootstrap import is_command_available

    statusline_missing = False
    if is_command_available("claude-statusline"):
        console.print("  [green]✓[/green] claude-statusline installed")
    else:
        console.print("  [yellow]○[/yellow] claude-statusline not installed")
        statusline_missing = True

    console.print()

    console.print("[bold cyan]Shell Completions[/bold cyan]\n")
    from ai_rules.completions import (
        detect_shell,
        find_config_file,
        get_supported_shells,
        is_completion_installed,
    )

    shell = detect_shell()
    if shell:
        config_path = find_config_file(shell)
        if config_path and is_completion_installed(config_path):
            console.print(
                f"  [green]✓[/green] {shell} completion installed ({config_path})"
            )
        else:
            console.print(
                f"  [yellow]○[/yellow] {shell} completion not installed "
                "(run: ai-rules completions install)"
            )
    else:
        supported = ", ".join(get_supported_shells())
        console.print(
            f"  [dim]Shell completion not available for your shell (only {supported} supported)[/dim]"
        )

    console.print()

    if not all_correct:
        if cache_stale:
            console.print(
                "[yellow]💡 Run 'ai-rules install --rebuild-cache' to fix issues[/yellow]"
            )
        else:
            console.print("[yellow]💡 Run 'ai-rules install' to fix issues[/yellow]")
        sys.exit(1)
    elif statusline_missing:
        console.print("[green]All symlinks are correct![/green]")
        console.print(
            "[yellow]💡 Run 'ai-rules install' to install optional tools[/yellow]"
        )
    else:
        console.print("[green]All symlinks are correct![/green]")


@main.command()
@click.option("--force", is_flag=True, help="Skip confirmations")
@click.option(
    "--agents",
    help="Comma-separated list of agents to uninstall (default: all)",
    shell_complete=complete_agents,
)
def uninstall(force: bool, agents: str | None) -> None:
    """Remove AI agent symlinks."""
    config_dir = get_config_dir()
    config = Config.load()
    all_agents = get_agents(config_dir, config)
    selected_agents = select_agents(all_agents, agents)

    if not force:
        console.print("[yellow]Warning:[/yellow] This will remove symlinks for:\n")
        console.print("[bold]Agents:[/bold]")
        for agent in selected_agents:
            console.print(f"  • {agent.name}")
        console.print()
        if not Confirm.ask("Continue?", default=False):
            console.print("[yellow]Uninstall cancelled[/yellow]")
            sys.exit(0)

    total_removed = 0
    total_skipped = 0

    console.print("\n[bold cyan]User-Level Configuration[/bold cyan]")
    for agent in selected_agents:
        console.print(f"\n[bold]{agent.name}[/bold]")

        for target, _ in agent.get_filtered_symlinks():
            success, message = remove_symlink(target, force)

            if success:
                console.print(f"  [green]✓[/green] {target} removed")
                total_removed += 1
            elif "Does not exist" in message:
                console.print(f"  [dim]•[/dim] {target} [dim](not installed)[/dim]")
            else:
                console.print(f"  [yellow]○[/yellow] {target} [dim]({message})[/dim]")
                total_skipped += 1

        if isinstance(agent, ClaudeAgent):
            from ai_rules.mcp import OperationResult

            result, message = agent.uninstall_mcps(force=force, dry_run=False)
            if result == OperationResult.REMOVED:
                console.print(f"  [green]✓[/green] {message}")
            elif result == OperationResult.NOT_FOUND:
                console.print(f"  [dim]•[/dim] {message}")

    console.print(
        f"\n[bold]Summary:[/bold] Removed {total_removed}, skipped {total_skipped}"
    )


@main.command("list-agents")
def list_agents_cmd() -> None:
    """List available AI agents."""
    config_dir = get_config_dir()
    config = Config.load()
    agents = get_agents(config_dir, config)

    table = Table(title="Available AI Agents", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Symlinks", justify="right")
    table.add_column("Status")

    for agent in agents:
        all_symlinks = agent.symlinks
        filtered_symlinks = agent.get_filtered_symlinks()
        excluded_count = len(all_symlinks) - len(filtered_symlinks)

        installed = 0
        for target, source in filtered_symlinks:
            status_code, _ = check_symlink(target, source)
            if status_code == "correct":
                installed += 1

        total = len(filtered_symlinks)
        status = f"{installed}/{total} installed"
        if excluded_count > 0:
            status += f" ({excluded_count} excluded)"

        table.add_row(agent.agent_id, agent.name, str(total), status)

    console.print(table)


@main.command()
@click.option("--check", is_flag=True, help="Check for updates without installing")
@click.option("--force", is_flag=True, help="Force reinstall even if up to date")
@click.option(
    "--skip-install",
    is_flag=True,
    help="Skip running 'install --rebuild-cache' after upgrade",
)
@click.option(
    "--only",
    type=click.Choice(["ai-rules", "statusline"]),
    help="Only upgrade specific tool",
)
def upgrade(check: bool, force: bool, skip_install: bool, only: str | None) -> None:
    """Upgrade ai-rules and related tools to the latest versions from PyPI.

    Examples:
        ai-rules upgrade                    # Check and install all updates
        ai-rules upgrade --check            # Only check for updates
        ai-rules upgrade --only=statusline  # Only upgrade statusline tool
    """
    from ai_rules.bootstrap import (
        UPDATABLE_TOOLS,
        check_tool_updates,
        perform_tool_upgrade,
    )

    tools = [t for t in UPDATABLE_TOOLS if only is None or t.tool_id == only]
    tools = [t for t in tools if t.is_installed()]

    if not tools:
        if only:
            console.print(f"[yellow]⚠[/yellow] Tool '{only}' is not installed")
        else:
            console.print("[yellow]⚠[/yellow] No tools are installed")
        sys.exit(1)

    tool_updates = []
    for tool in tools:
        try:
            current = tool.get_version()
            if current:
                console.print(
                    f"[dim]{tool.display_name} current version: {current}[/dim]"
                )
        except Exception as e:
            console.print(
                f"[red]Error:[/red] Could not get {tool.display_name} version: {e}"
            )
            continue

        with console.status(f"Checking {tool.display_name} for updates..."):
            try:
                update_info = check_tool_updates(tool)
            except Exception as e:
                console.print(
                    f"[red]Error:[/red] Failed to check {tool.display_name} updates: {e}"
                )
                continue

        if update_info and (update_info.has_update or force):
            tool_updates.append((tool, update_info))
        elif update_info and not update_info.has_update:
            console.print(
                f"[green]✓[/green] {tool.display_name} is already up to date!"
            )

    console.print()

    if not tool_updates and not force:
        console.print("[green]✓[/green] All tools are up to date!")
        return

    for tool, update_info in tool_updates:
        if update_info.has_update:
            console.print(
                f"[cyan]Update available for {tool.display_name}:[/cyan] "
                f"{update_info.current_version} → {update_info.latest_version}"
            )

    if check:
        if tool_updates:
            console.print("\nRun [bold]ai-rules upgrade[/bold] to install")
        return

    if not force:
        if len(tool_updates) == 1:
            prompt = f"\nInstall {tool_updates[0][0].display_name} update?"
        else:
            prompt = f"\nInstall {len(tool_updates)} updates?"
        if not Confirm.ask(prompt, default=True):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    ai_rules_upgraded = False
    for tool, update_info in tool_updates:
        with console.status(f"Upgrading {tool.display_name}..."):
            try:
                success, msg, was_upgraded = perform_tool_upgrade(tool)
            except Exception as e:
                console.print(
                    f"\n[red]Error:[/red] {tool.display_name} upgrade failed: {e}"
                )
                continue

        if success:
            new_version = tool.get_version()
            if new_version == update_info.latest_version:
                console.print(
                    f"[green]✓[/green] {tool.display_name} upgraded to {new_version}"
                )
                if tool.tool_id == "ai-rules":
                    ai_rules_upgraded = True
            elif new_version == update_info.current_version:
                console.print(
                    f"[yellow]⚠[/yellow] {tool.display_name} upgrade reported success but version unchanged ({new_version})"
                )
            else:
                console.print(
                    f"[green]✓[/green] {tool.display_name} upgraded to {new_version}"
                )
                if tool.tool_id == "ai-rules":
                    ai_rules_upgraded = True
        else:
            console.print(
                f"[red]Error:[/red] {tool.display_name} upgrade failed: {msg}"
            )

    if ai_rules_upgraded and not skip_install:
        try:
            import subprocess

            try:
                repo_root = get_git_repo_root()
            except Exception:
                console.print(
                    "\n[dim]Not in ai-rules repository - skipping install[/dim]"
                )
                console.print(
                    "[dim]Run 'ai-rules install --rebuild-cache' from repo to update[/dim]"
                )
                console.print(
                    "[dim]Restart your terminal if the command doesn't work[/dim]"
                )
                return

            console.print("\n[dim]Running 'ai-rules install --rebuild-cache'...[/dim]")

            from ai_rules.state import get_active_profile

            current_profile = get_active_profile() or "default"

            result = subprocess.run(
                [
                    "ai-rules",
                    "install",
                    "--rebuild-cache",
                    "--profile",
                    current_profile,
                ],
                capture_output=False,
                text=True,
                cwd=str(repo_root),
                timeout=30,
            )

            if result.returncode == 0:
                console.print("[dim]✓ Install completed successfully[/dim]")
            else:
                console.print(
                    f"[yellow]⚠[/yellow] Install failed with exit code {result.returncode}"
                )
                console.print(
                    "[dim]Run 'ai-rules install --rebuild-cache' manually to retry[/dim]"
                )
        except subprocess.TimeoutExpired:
            console.print("[yellow]⚠[/yellow] Install timed out after 30 seconds")
            console.print(
                "[dim]Run 'ai-rules install --rebuild-cache' manually to retry[/dim]"
            )
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not run install: {e}")
            console.print("[dim]Run 'ai-rules install --rebuild-cache' manually[/dim]")

        console.print("[dim]Restart your terminal if the command doesn't work[/dim]")


@main.command()
def info() -> None:
    """Show installation method and version info for ai-rules tools.

    Displays how each tool was installed (PyPI, GitHub, or local development)
    along with current versions and update availability.
    """
    from rich.table import Table

    from ai_rules.bootstrap import (
        UPDATABLE_TOOLS,
        check_tool_updates,
        get_tool_source,
    )

    table = Table(title="AI Rules Installation Info", show_header=True)
    table.add_column("Tool", style="cyan")
    table.add_column("Source", style="bold")
    table.add_column("Version")
    table.add_column("Update")

    has_updates = False

    for tool in UPDATABLE_TOOLS:
        tool_name = tool.display_name

        if not tool.is_installed():
            table.add_row(tool_name, "-", "-", "[dim](not installed)[/dim]")
            continue

        source = get_tool_source(tool.package_name)
        source_display = source.name.lower() if source else "[dim]unknown[/dim]"

        version = tool.get_version()
        version_display = version if version else "[dim]unknown[/dim]"

        update_display = "-"
        try:
            update_info = check_tool_updates(tool, timeout=5)
            if update_info and update_info.has_update:
                update_display = f"[cyan]{update_info.latest_version} available[/cyan]"
                has_updates = True
        except Exception:
            update_display = "[dim](check failed)[/dim]"

        table.add_row(tool_name, source_display, version_display, update_display)

    console.print(table)

    if has_updates:
        console.print("\n[dim]Run 'ai-rules upgrade' to install updates.[/dim]")


@main.command()
@click.option(
    "--agents",
    help="Comma-separated list of agents to validate (default: all)",
    shell_complete=complete_agents,
)
def validate(agents: str | None) -> None:
    """Validate configuration and source files."""
    config_dir = get_config_dir()
    config = Config.load()
    all_agents = get_agents(config_dir, config)
    selected_agents = select_agents(all_agents, agents)

    console.print("[bold]Validating AI Rules Configuration[/bold]\n")

    all_valid = True
    total_checked = 0
    total_issues = 0

    for agent in selected_agents:
        console.print(f"[bold]{agent.name}:[/bold]")
        agent_issues = []

        for _target, source in agent.symlinks:
            total_checked += 1

            if not source.exists():
                agent_issues.append((source, "Source file does not exist"))
                all_valid = False
            elif not source.is_file():
                agent_issues.append((source, "Source is not a file"))
                all_valid = False
            else:
                console.print(f"  [green]✓[/green] {source.name}")

        excluded_symlinks = [
            (t, s)
            for t, s in agent.symlinks
            if (t, s) not in agent.get_filtered_symlinks()
        ]
        if excluded_symlinks:
            console.print(
                f"  [dim]({len(excluded_symlinks)} symlink(s) excluded by config)[/dim]"
            )

        for path, issue in agent_issues:
            console.print(f"  [red]✗[/red] {path}")
            console.print(f"    [dim]{issue}[/dim]")
            total_issues += 1

        console.print()

    console.print(f"[bold]Summary:[/bold] Checked {total_checked} source file(s)")

    if all_valid:
        console.print("[green]All source files are valid![/green]")
    else:
        console.print(f"[red]Found {total_issues} issue(s)[/red]")
        sys.exit(1)


@main.command()
@click.option(
    "--agents",
    help="Comma-separated list of agents to check (default: all)",
    shell_complete=complete_agents,
)
def diff(agents: str | None) -> None:
    """Show differences between repo configs and installed symlinks."""
    config_dir = get_config_dir()
    config = Config.load()
    all_agents = get_agents(config_dir, config)
    selected_agents = select_agents(all_agents, agents)

    console.print("[bold]Configuration Differences[/bold]\n")

    found_differences = False

    for agent in selected_agents:
        agent_has_diff = False
        agent_diffs = []

        for target, source in agent.get_filtered_symlinks():
            target_path = target.expanduser()
            status_code, message = check_symlink(target_path, source)

            if status_code == "missing":
                agent_diffs.append((target_path, source, "missing", "Not installed"))
                agent_has_diff = True
            elif status_code == "broken":
                agent_diffs.append((target_path, source, "broken", "Broken symlink"))
                agent_has_diff = True
            elif status_code == "wrong_target":
                try:
                    actual = target_path.resolve()
                    agent_diffs.append(
                        (target_path, source, "wrong", f"Points to {actual}")
                    )
                    agent_has_diff = True
                except (OSError, RuntimeError):
                    agent_diffs.append(
                        (target_path, source, "broken", "Broken symlink")
                    )
                    agent_has_diff = True
            elif status_code == "not_symlink":
                agent_diffs.append(
                    (target_path, source, "file", "Regular file (not symlink)")
                )
                agent_has_diff = True

        if agent_has_diff:
            console.print(f"[bold]{agent.name}:[/bold]")
            for path, expected_source, diff_type, desc in agent_diffs:
                if diff_type == "missing":
                    console.print(f"  [red]✗[/red] {path}")
                    console.print(f"    [dim]{desc}[/dim]")
                    console.print(f"    [dim]Expected: → {expected_source}[/dim]")
                elif diff_type == "broken":
                    console.print(f"  [red]✗[/red] {path}")
                    console.print(f"    [dim]{desc}[/dim]")
                elif diff_type == "wrong":
                    console.print(f"  [yellow]⚠[/yellow] {path}")
                    console.print(f"    [dim]{desc}[/dim]")
                    console.print(f"    [dim]Expected: → {expected_source}[/dim]")
                elif diff_type == "file":
                    console.print(f"  [yellow]⚠[/yellow] {path}")
                    console.print(f"    [dim]{desc}[/dim]")
                    console.print(f"    [dim]Expected: → {expected_source}[/dim]")
            console.print()
            found_differences = True

    if not found_differences:
        console.print("[green]No differences found - all symlinks are correct![/green]")
    else:
        console.print(
            "[yellow]💡 Run 'ai-rules install' to fix these differences[/yellow]"
        )


@main.group()
def exclude() -> None:
    """Manage exclusion patterns."""
    pass


@exclude.command("add")
@click.argument("pattern")
def exclude_add(pattern: str) -> None:
    """Add an exclusion pattern to user config.

    PATTERN can be an exact path or glob pattern (e.g., ~/.claude/*.json)
    """
    data = Config.load_user_config()

    if "exclude_symlinks" not in data:
        data["exclude_symlinks"] = []

    if pattern in data["exclude_symlinks"]:
        console.print(f"[yellow]Pattern already excluded:[/yellow] {pattern}")
        return

    data["exclude_symlinks"].append(pattern)
    Config.save_user_config(data)

    user_config_path = Path.home() / ".ai-rules-config.yaml"
    console.print(f"[green]✓[/green] Added exclusion pattern: {pattern}")
    console.print(f"[dim]Config updated: {user_config_path}[/dim]")


@exclude.command("remove")
@click.argument("pattern")
def exclude_remove(pattern: str) -> None:
    """Remove an exclusion pattern from user config."""
    user_config_path = Path.home() / ".ai-rules-config.yaml"

    if not user_config_path.exists():
        console.print("[red]No user config found[/red]")
        sys.exit(1)

    data = Config.load_user_config()

    if "exclude_symlinks" not in data or pattern not in data["exclude_symlinks"]:
        console.print(f"[yellow]Pattern not found:[/yellow] {pattern}")
        sys.exit(1)

    data["exclude_symlinks"].remove(pattern)
    Config.save_user_config(data)

    console.print(f"[green]✓[/green] Removed exclusion pattern: {pattern}")
    console.print(f"[dim]Config updated: {user_config_path}[/dim]")


@exclude.command("list")
def exclude_list() -> None:
    """List all exclusion patterns."""
    config = Config.load()

    if not config.exclude_symlinks:
        console.print("[dim]No exclusion patterns configured[/dim]")
        return

    console.print("[bold]Exclusion Patterns:[/bold]\n")

    for pattern in sorted(config.exclude_symlinks):
        console.print(f"  • {pattern} [dim](user)[/dim]")


@main.group()
def override() -> None:
    """Manage settings overrides."""
    pass


@override.command("set")
@click.argument("key")
@click.argument("value")
def override_set(key: str, value: str) -> None:
    """Set a settings override for an agent.

    KEY should be in format 'agent.setting' (e.g., 'claude.model')
    Supports array notation: 'claude.hooks.SubagentStop[0].hooks[0].command'
    VALUE will be parsed as JSON if possible, otherwise treated as string

    Array notation examples:
    - claude.hooks.SubagentStop[0].command
    - claude.hooks.SubagentStop[0].hooks[0].command
    - claude.items[0].nested[1].value

    Path validation:
    - Validates agent name (must be 'claude', 'goose', etc.)
    - Validates full path against base settings structure
    - Provides helpful suggestions when paths are invalid
    """
    user_config_path = Path.home() / ".ai-rules-config.yaml"
    config_dir = get_config_dir()

    parts = key.split(".", 1)
    if len(parts) != 2:
        console.print("[red]Error:[/red] Key must be in format 'agent.setting'")
        console.print(
            "[dim]Example: claude.model or claude.hooks.SubagentStop[0].command[/dim]"
        )
        sys.exit(1)

    agent, setting = parts

    is_valid, error_msg, warning_msg, suggestions = validate_override_path(
        agent, setting, config_dir
    )

    if not is_valid:
        console.print(f"[red]Error:[/red] {error_msg}")
        if suggestions:
            console.print(
                f"[dim]Available options: {', '.join(suggestions[:10])}[/dim]"
            )
        sys.exit(1)

    if warning_msg:
        console.print(f"[yellow]Warning:[/yellow] {warning_msg}")

    import json

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    data = Config.load_user_config()

    if "settings_overrides" not in data:
        data["settings_overrides"] = {}

    if agent not in data["settings_overrides"]:
        data["settings_overrides"][agent] = {}

    try:
        path_components = parse_setting_path(setting)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    current = data["settings_overrides"][agent]
    for i, component in enumerate(path_components[:-1]):
        if isinstance(component, int):
            if not isinstance(current, list):
                console.print(
                    f"[red]Error:[/red] Expected array at path component {i}, "
                    f"but found {type(current).__name__}"
                )
                sys.exit(1)

            while len(current) <= component:
                current.append({})

            current = current[component]
        else:
            if component not in current:
                next_component = (
                    path_components[i + 1] if i + 1 < len(path_components) else None
                )
                if isinstance(next_component, int):
                    current[component] = []
                else:
                    current[component] = {}

            current = current[component]

    final_component = path_components[-1]
    if isinstance(final_component, int):
        if not isinstance(current, list):
            console.print(
                f"[red]Error:[/red] Expected array for final component, "
                f"but found {type(current).__name__}"
            )
            sys.exit(1)

        while len(current) <= final_component:
            current.append(None)

        current[final_component] = parsed_value
    else:
        current[final_component] = parsed_value

    Config.save_user_config(data)

    console.print(f"[green]✓[/green] Set override: {agent}.{setting} = {parsed_value}")
    console.print(f"[dim]Config updated: {user_config_path}[/dim]")
    console.print(
        "\n[yellow]💡 Run 'ai-rules install --rebuild-cache' to apply changes[/yellow]"
    )


@override.command("unset")
@click.argument("key")
def override_unset(key: str) -> None:
    """Remove a settings override.

    KEY should be in format 'agent.setting' (e.g., 'claude.model')
    Supports nested keys like 'agent.nested.key'
    """
    user_config_path = Path.home() / ".ai-rules-config.yaml"

    if not user_config_path.exists():
        console.print("[red]No user config found[/red]")
        sys.exit(1)

    parts = key.split(".", 1)
    if len(parts) != 2:
        console.print("[red]Error:[/red] Key must be in format 'agent.setting'")
        sys.exit(1)

    agent, setting = parts

    data = Config.load_user_config()

    if "settings_overrides" not in data or agent not in data["settings_overrides"]:
        console.print(f"[yellow]Override not found:[/yellow] {key}")
        sys.exit(1)

    setting_parts = setting.split(".")
    current = data["settings_overrides"][agent]

    for part in setting_parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            console.print(f"[yellow]Override not found:[/yellow] {key}")
            sys.exit(1)
        current = current[part]

    final_key = setting_parts[-1]
    if not isinstance(current, dict) or final_key not in current:
        console.print(f"[yellow]Override not found:[/yellow] {key}")
        sys.exit(1)

    del current[final_key]

    current = data["settings_overrides"][agent]
    path = []

    for part in setting_parts[:-1]:
        path.append((current, part))
        current = current[part]

    for parent, key in reversed(path):
        if isinstance(parent[key], dict) and not parent[key]:
            del parent[key]
        else:
            break

    if not data["settings_overrides"][agent]:
        del data["settings_overrides"][agent]

    Config.save_user_config(data)

    console.print(f"[green]✓[/green] Removed override: {key}")
    console.print(f"[dim]Config updated: {user_config_path}[/dim]")
    console.print(
        "\n[yellow]💡 Run 'ai-rules install --rebuild-cache' to apply changes[/yellow]"
    )


@override.command("list")
def override_list() -> None:
    """List all settings overrides."""
    user_data = Config.load_user_config()
    user_overrides = user_data.get("settings_overrides", {})

    if not user_overrides:
        console.print("[dim]No settings overrides configured[/dim]")
        return

    console.print("[bold]Settings Overrides:[/bold]\n")

    for agent, overrides in sorted(user_overrides.items()):
        console.print(f"[bold]{agent}:[/bold]")
        for key, value in sorted(overrides.items()):
            console.print(f"  • {key}: {value}")
        console.print()


@main.group()
def config() -> None:
    """Manage ai-rules configuration."""
    pass


@config.command("show")
@click.option(
    "--merged", is_flag=True, help="Show merged settings with overrides applied"
)
@click.option("--agent", help="Show config for specific agent only")
def config_show(merged: bool, agent: str | None) -> None:
    """Show current configuration."""
    config_dir = get_config_dir()
    cfg = Config.load()
    user_config_path = Path.home() / ".ai-rules-config.yaml"

    if merged:
        console.print("[bold]Merged Settings:[/bold]\n")

        agents_to_show = [agent] if agent else ["claude", "goose"]

        for agent_name in agents_to_show:
            if agent_name not in cfg.settings_overrides:
                console.print(
                    f"[dim]{agent_name}: No overrides (using base settings)[/dim]\n"
                )
                continue

            console.print(f"[bold]{agent_name}:[/bold]")

            from ai_rules.config import AGENT_CONFIG_METADATA

            agent_config = AGENT_CONFIG_METADATA.get(agent_name)
            if not agent_config:
                console.print(f"  [red]✗[/red] Unknown agent: {agent_name}")
                console.print()
                continue

            base_path = config_dir / agent_name / agent_config["config_file"]
            if base_path.exists():
                with open(base_path) as f:
                    import json

                    import yaml

                    if agent_config["format"] == "json":
                        base_settings = json.load(f)
                    else:
                        base_settings = yaml.safe_load(f)

                merged_settings = cfg.merge_settings(agent_name, base_settings)

                overridden_keys = []
                for key in cfg.settings_overrides[agent_name]:
                    if key in base_settings:
                        old_val = base_settings[key]
                        new_val = merged_settings[key]
                        console.print(
                            f"  [yellow]↻[/yellow] {key}: {old_val} → {new_val}"
                        )
                        overridden_keys.append(key)
                    else:
                        console.print(
                            f"  [green]+[/green] {key}: {merged_settings[key]}"
                        )
                        overridden_keys.append(key)

                for key, value in merged_settings.items():
                    if key not in overridden_keys:
                        console.print(f"  [dim]•[/dim] {key}: {value}")
            else:
                console.print(
                    f"  [yellow]⚠[/yellow] No base settings found at {base_path}"
                )
                console.print(
                    f"  [dim]Overrides: {cfg.settings_overrides[agent_name]}[/dim]"
                )

            console.print()
    else:
        console.print("[bold]Configuration:[/bold]\n")

        if user_config_path.exists():
            with open(user_config_path) as f:
                content = f.read()
            console.print(f"[bold]User Config:[/bold] {user_config_path}")
            console.print(content)
        else:
            console.print(f"[dim]No user config at {user_config_path}[/dim]\n")


@config.command("edit")
def config_edit() -> None:
    """Edit user configuration file in $EDITOR."""
    import os
    import subprocess

    user_config_path = Path.home() / ".ai-rules-config.yaml"
    editor = os.environ.get("EDITOR", "vi")

    if not user_config_path.exists():
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(user_config_path, "w") as f:
            f.write("version: 1\n")

    try:
        subprocess.run([editor, str(user_config_path)], check=True)
        console.print(f"[green]✓[/green] Config edited: {user_config_path}")
    except subprocess.CalledProcessError:
        console.print("[red]Error opening editor[/red]")
        sys.exit(1)


def _get_common_exclusions() -> list[tuple[str, str, bool]]:
    """Get list of common exclusion patterns.

    Returns:
        List of (pattern, description, default) tuples
    """
    return [
        ("~/.claude/settings.json", "Claude Code settings", False),
        ("~/.config/goose/config.yaml", "Goose config", False),
        ("~/.config/goose/.goosehints", "Goose hints", True),
        ("~/AGENTS.md", "Shared agents file", False),
    ]


def _collect_exclusion_patterns() -> list[str]:
    """Collect exclusion patterns from user (Step 1).

    Returns:
        List of exclusion patterns
    """
    console.print("\n[bold]Step 1: Exclusion Patterns[/bold]")
    console.print("Do you want to exclude any files from being managed?\n")

    console.print("Common files to exclude:")
    selected_exclusions = []

    for pattern, description, default in _get_common_exclusions():
        default_str = "Y/n" if default else "y/N"
        response = console.input(f"  Exclude {description}? [{default_str}]: ").lower()
        should_exclude = (default and response != "n") or (
            not default and response == "y"
        )
        if should_exclude:
            selected_exclusions.append(pattern)
            console.print(f"    [green]✓[/green] Will exclude: {pattern}")

    console.print(
        "\n[dim]Enter custom exclusion patterns (glob patterns supported)[/dim]"
    )
    console.print("[dim]One per line, empty line to finish:[/dim]")
    while True:
        pattern = console.input("> ").strip()
        if not pattern:
            break
        selected_exclusions.append(pattern)
        console.print(f"  [green]✓[/green] Added: {pattern}")

    if selected_exclusions:
        console.print(
            f"\n[green]✓[/green] Configured {len(selected_exclusions)} exclusion pattern(s)"
        )

    return selected_exclusions


def _collect_settings_overrides() -> dict[str, dict[str, Any]]:
    """Collect settings overrides from user (Step 2).

    Returns:
        Dictionary of agent settings overrides
    """
    import json

    console.print("\n[bold]Step 2: Settings Overrides[/bold]")
    response = console.input(
        "Do you want to override any settings for this machine? [y/N]: "
    )

    if response.lower() != "y":
        return {}

    settings_overrides = {}

    while True:
        console.print("\nWhich agent's settings do you want to override?")
        console.print("  1) claude")
        console.print("  2) goose")
        console.print("  3) done")
        agent_choice = console.input("> ").strip()

        if agent_choice == "3" or not agent_choice:
            break

        agent_map = {"1": "claude", "2": "goose"}
        agent = agent_map.get(agent_choice)

        if not agent:
            console.print("[yellow]Invalid choice[/yellow]")
            continue

        console.print(f"\n[bold]{agent.title()} settings overrides:[/bold]")
        console.print("[dim]Enter key=value pairs (empty to finish):[/dim]")
        console.print("[dim]Example: model=claude-sonnet-4-5-20250929[/dim]\n")

        agent_overrides = {}
        while True:
            override = console.input("> ").strip()
            if not override:
                break

            if "=" not in override:
                console.print("[yellow]Invalid format. Use key=value[/yellow]")
                continue

            key, value = override.split("=", 1)
            key = key.strip()
            value = value.strip()

            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            agent_overrides[key] = parsed_value
            console.print(f"  [green]✓[/green] Added: {key} = {parsed_value}")

        if agent_overrides:
            settings_overrides[agent] = agent_overrides

    if settings_overrides:
        total_overrides = sum(len(v) for v in settings_overrides.values())
        console.print(
            f"\n[green]✓[/green] Configured {total_overrides} override(s) for {len(settings_overrides)} agent(s)"
        )

    return settings_overrides


def _display_configuration_summary(config_data: dict[str, Any]) -> None:
    """Display configuration summary before saving.

    Args:
        config_data: Configuration dictionary to display
    """
    console.print("\n[bold cyan]Configuration Summary:[/bold cyan]")
    console.print("=" * 50)

    if "exclude_symlinks" in config_data:
        console.print(
            f"\n[bold]Global Exclusions ({len(config_data['exclude_symlinks'])}):[/bold]"
        )
        for pattern in config_data["exclude_symlinks"]:
            console.print(f"  • {pattern}")

    if "settings_overrides" in config_data:
        console.print("\n[bold]Settings Overrides:[/bold]")
        for agent, overrides in config_data["settings_overrides"].items():
            console.print(f"  [bold]{agent}:[/bold]")
            for key, value in overrides.items():
                console.print(f"    • {key}: {value}")

    console.print("\n" + "=" * 50)


@config.command("init")
def config_init() -> None:
    """Interactive configuration wizard."""
    user_config_path = Path.home() / ".ai-rules-config.yaml"

    console.print("[bold cyan]Welcome to ai-rules configuration wizard![/bold cyan]\n")
    console.print("This will help you set up your .ai-rules-config.yaml file.")
    console.print(f"Config will be created at: [dim]{user_config_path}[/dim]\n")

    if user_config_path.exists():
        console.print("[yellow]⚠[/yellow] Config file already exists!")
        if not Confirm.ask("Overwrite existing config?", default=False):
            console.print("[dim]Cancelled[/dim]")
            return

    config_data: dict[str, Any] = {"version": 1}

    selected_exclusions = _collect_exclusion_patterns()
    if selected_exclusions:
        config_data["exclude_symlinks"] = selected_exclusions

    settings_overrides = _collect_settings_overrides()
    if settings_overrides:
        config_data["settings_overrides"] = settings_overrides

    _display_configuration_summary(config_data)

    if Confirm.ask("\nSave configuration?", default=True):
        Config.save_user_config(config_data)

        console.print(f"\n[green]✓[/green] Configuration saved to {user_config_path}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  • Run [cyan]ai-rules install[/cyan] to apply these settings")
        console.print("  • Run [cyan]ai-rules config show[/cyan] to view your config")
        console.print(
            "  • Run [cyan]ai-rules config show --merged[/cyan] to see merged settings"
        )
    else:
        console.print("[dim]Configuration not saved[/dim]")


@main.group()
def profile() -> None:
    """Manage configuration profiles."""
    pass


@profile.command("list")
def profile_list() -> None:
    """List available profiles."""
    from rich.table import Table

    from ai_rules.profiles import ProfileLoader

    loader = ProfileLoader()
    profiles = loader.list_profiles()

    table = Table(title="Available Profiles", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Extends")

    for name in profiles:
        try:
            info = loader.get_profile_info(name)
            desc = info.get("description", "")
            extends = info.get("extends") or "-"
            table.add_row(name, desc, extends)
        except Exception:
            table.add_row(name, "[dim]Error loading[/dim]", "-")

    console.print(table)


@profile.command("show")
@click.argument("name")
@click.option(
    "--resolved", is_flag=True, help="Show resolved profile with inheritance applied"
)
def profile_show(name: str, resolved: bool) -> None:
    """Show profile details."""
    from ai_rules.profiles import (
        CircularInheritanceError,
        ProfileLoader,
        ProfileNotFoundError,
    )

    loader = ProfileLoader()

    try:
        if resolved:
            profile = loader.load_profile(name)
            console.print(f"[bold]Profile: {profile.name}[/bold] (resolved)")
            console.print(f"[dim]Description:[/dim] {profile.description}")
            if profile.extends:
                console.print(f"[dim]Extends:[/dim] {profile.extends}")

            if profile.settings_overrides:
                console.print("\n[bold]Settings Overrides:[/bold]")
                for agent, overrides in sorted(profile.settings_overrides.items()):
                    console.print(f"  [cyan]{agent}:[/cyan]")
                    for key, value in sorted(overrides.items()):
                        console.print(f"    {key}: {value}")

            if profile.exclude_symlinks:
                console.print("\n[bold]Exclude Symlinks:[/bold]")
                for pattern in sorted(profile.exclude_symlinks):
                    console.print(f"  - {pattern}")

            if profile.mcp_overrides:
                console.print("\n[bold]MCP Overrides:[/bold]")
                for mcp, overrides in sorted(profile.mcp_overrides.items()):
                    console.print(f"  [cyan]{mcp}:[/cyan]")
                    for key, value in sorted(overrides.items()):
                        console.print(f"    {key}: {value}")
        else:
            import yaml

            info = loader.get_profile_info(name)
            console.print(f"[bold]Profile: {info.get('name', name)}[/bold]")
            console.print(yaml.dump(info, default_flow_style=False, sort_keys=False))

    except ProfileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except CircularInheritanceError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@profile.command("current")
def profile_current() -> None:
    """Show currently active profile."""
    from ai_rules.state import get_active_profile

    active = get_active_profile()
    if active:
        console.print(f"Active profile: [cyan]{active}[/cyan]")
    else:
        console.print("[dim]No profile set (using default)[/dim]")


def _detect_profile_override_conflicts(
    profile: Profile, user_config: dict[str, Any]
) -> list[tuple[str, str, Any]]:
    """Detect conflicts between profile settings and user overrides.

    Args:
        profile: The profile being installed
        user_config: User config dict from ~/.ai-rules-config.yaml

    Returns:
        List of (agent, key, value) tuples for settings that conflict
    """
    conflicts = []
    user_settings = user_config.get("settings_overrides", {})

    for agent, profile_overrides in profile.settings_overrides.items():
        if agent in user_settings:
            for key in profile_overrides:
                if key in user_settings[agent]:
                    conflicts.append((agent, key, user_settings[agent][key]))

    return conflicts


def _handle_profile_conflicts(
    conflicts: list[tuple[str, str, Any]],
    profile_name: str,
    user_config: dict[str, Any],
) -> None:
    """Show conflicts and prompt user to clear them.

    Args:
        conflicts: List of (agent, key, value) tuples
        profile_name: Name of profile being installed
        user_config: User config dict to potentially modify
    """
    if not conflicts:
        return

    console.print(
        f"\n[yellow]⚠[/yellow]  User overrides conflict with profile '{profile_name}':"
    )
    for agent, key, value in conflicts:
        console.print(f"  • {agent}.{key}: {value}")

    if click.confirm("\nRemove these from user config?", default=False):
        user_settings = user_config.get("settings_overrides", {})
        for agent, key, _ in conflicts:
            if agent in user_settings and key in user_settings[agent]:
                del user_settings[agent][key]
                if not user_settings[agent]:
                    del user_settings[agent]

        Config.save_user_config(user_config)
        console.print("[green]✓[/green] Cleared conflicting overrides\n")
    else:
        console.print()


@profile.command("switch")
@click.argument("name", shell_complete=complete_profiles)
@click.pass_context
def profile_switch(ctx: click.Context, name: str) -> None:
    """Switch to a different profile."""
    from ai_rules.profiles import ProfileLoader, ProfileNotFoundError

    loader = ProfileLoader()
    try:
        profile_obj = loader.load_profile(name)
    except ProfileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    user_config = Config.load_user_config()
    profile_conflicts = _detect_profile_override_conflicts(profile_obj, user_config)
    if profile_conflicts:
        _handle_profile_conflicts(profile_conflicts, name, user_config)

    console.print(f"Switching to profile: [cyan]{name}[/cyan]")
    ctx.invoke(
        install,
        profile=name,
        rebuild_cache=True,
        force=True,
        skip_completions=True,
        agents=None,
        dry_run=False,
        config_dir_override=None,
    )


@main.group()
def completions() -> None:
    """Manage shell tab completion."""
    pass


from ai_rules.completions import get_supported_shells

_SUPPORTED_SHELLS = list(get_supported_shells())


@completions.command(name="bash")
def completions_bash() -> None:
    """Output bash completion script for manual installation."""
    from ai_rules.completions import generate_completion_script

    try:
        script = generate_completion_script("bash")
        console.print(script)
        console.print(
            "\n[dim]To install: Add the above to your ~/.bashrc or run:[/dim]"
        )
        console.print("[dim]  ai-rules completions install[/dim]")
    except Exception as e:
        console.print(f"[red]Error generating completion script:[/red] {e}")
        sys.exit(1)


@completions.command(name="zsh")
def completions_zsh() -> None:
    """Output zsh completion script for manual installation."""
    from ai_rules.completions import generate_completion_script

    try:
        script = generate_completion_script("zsh")
        console.print(script)
        console.print("\n[dim]To install: Add the above to your ~/.zshrc or run:[/dim]")
        console.print("[dim]  ai-rules completions install[/dim]")
    except Exception as e:
        console.print(f"[red]Error generating completion script:[/red] {e}")
        sys.exit(1)


@completions.command(name="install")
@click.option(
    "--shell",
    type=click.Choice(_SUPPORTED_SHELLS, case_sensitive=False),
    help="Shell type (auto-detected if not specified)",
)
def completions_install(shell: str | None) -> None:
    """Install shell completion to config file."""
    from ai_rules.completions import detect_shell, install_completion

    if shell is None:
        shell = detect_shell()
        if shell is None:
            console.print(
                "[red]Error:[/red] Could not detect shell. Please specify with --shell"
            )
            sys.exit(1)
        console.print(f"[dim]Detected shell:[/dim] {shell}")

    success, message = install_completion(shell, dry_run=False)

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]Error:[/red] {message}")
        sys.exit(1)


@completions.command(name="uninstall")
@click.option(
    "--shell",
    type=click.Choice(_SUPPORTED_SHELLS, case_sensitive=False),
    help="Shell type (auto-detected if not specified)",
)
def completions_uninstall(shell: str | None) -> None:
    """Remove shell completion from config file."""
    from ai_rules.completions import (
        detect_shell,
        find_config_file,
        uninstall_completion,
    )

    if shell is None:
        shell = detect_shell()
        if shell is None:
            console.print(
                "[red]Error:[/red] Could not detect shell. Please specify with --shell"
            )
            sys.exit(1)

    config_path = find_config_file(shell)
    if config_path is None:
        console.print(f"[red]Error:[/red] No {shell} config file found")
        sys.exit(1)

    success, message = uninstall_completion(config_path)

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]Error:[/red] {message}")
        sys.exit(1)


@completions.command(name="status")
def completions_status() -> None:
    """Show shell completion installation status."""
    from ai_rules.completions import (
        detect_shell,
        find_config_file,
        get_supported_shells,
        is_completion_installed,
    )

    detected_shell = detect_shell()
    console.print("[bold cyan]Shell Completions Status[/bold cyan]\n")

    if detected_shell:
        console.print(f"Detected shell: [cyan]{detected_shell}[/cyan]\n")
    else:
        console.print("[yellow]No supported shell detected[/yellow]\n")

    from rich.table import Table

    table = Table(show_header=True)
    table.add_column("Shell")
    table.add_column("Status")
    table.add_column("Config File")

    for shell in get_supported_shells():
        config_path = find_config_file(shell)

        if config_path is None:
            status = "[dim]-[/dim]"
            config_str = "[dim]No config file found[/dim]"
        elif is_completion_installed(config_path):
            status = "[green]✓[/green]"
            config_str = str(config_path)
        else:
            status = "[yellow]○[/yellow]"
            config_str = f"{config_path} [dim](not installed)[/dim]"

        shell_name = f"[bold]{shell}[/bold]" if shell == detected_shell else shell
        table.add_row(shell_name, status, config_str)

    console.print(table)
    console.print("\n[dim]To install: ai-rules completions install[/dim]")


if __name__ == "__main__":
    main()
