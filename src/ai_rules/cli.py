"""Command-line interface for ai-rules."""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from ai_rules.agents.base import Agent
from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.agents.shared import SharedAgent
from ai_rules.config import (
    AGENT_CONFIG_METADATA,
    Config,
    ProjectConfig,
    parse_setting_path,
    validate_override_path,
)
from ai_rules.symlinks import (
    SymlinkResult,
    check_symlink,
    create_symlink,
    remove_symlink,
)

console = Console()


def get_repo_root() -> Path:
    """Get the ai-rules project root directory."""
    return Path(__file__).parent.parent.parent.absolute()


def get_agents(repo_root: Path, config: Config) -> List[Agent]:
    """Get all available agents."""
    return [
        ClaudeAgent(repo_root, config),
        GooseAgent(repo_root, config),
        SharedAgent(repo_root, config),
    ]


def select_agents(all_agents: List[Agent], filter_string: Optional[str]) -> List[Agent]:
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


def filter_selected_projects(
    config: Config, projects_filter: Optional[str], user_only: bool
) -> Dict[str, ProjectConfig]:
    """Filter and validate project selection.

    Args:
        config: Configuration object containing all projects
        projects_filter: Comma-separated project names or None for all
        user_only: If True, return empty dict

    Returns:
        Dictionary of selected projects

    Raises:
        SystemExit: If invalid project names are specified
    """
    if user_only:
        return {}

    if projects_filter:
        project_ids = {p.strip() for p in projects_filter.split(",") if p.strip()}
        selected = {
            name: proj for name, proj in config.projects.items() if name in project_ids
        }
        invalid_projects = project_ids - set(config.projects.keys())
        if invalid_projects:
            console.print(
                f"[red]Error:[/red] Invalid project(s): {', '.join(sorted(invalid_projects))}\n"
                f"[dim]Available projects: {', '.join(sorted(config.projects.keys())) or 'none'}[/dim]"
            )
            sys.exit(1)
        return selected
    else:
        return config.projects


def get_filtered_project_symlinks(
    agent: Agent, project: ProjectConfig, config: Config, project_name: str
) -> List[Tuple[Path, Path]]:
    """Get project symlinks filtered by exclusions.

    Args:
        agent: Agent to get symlinks for
        project: Project configuration
        config: Global configuration with exclusion rules
        project_name: Name of the project

    Returns:
        List of (target, source) tuples after filtering exclusions
    """
    all_symlinks = agent.get_project_symlinks(project)
    return [
        (target, source)
        for target, source in all_symlinks
        if not config.is_project_excluded(project_name, str(target))
    ]


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


def check_first_run(agents: List[Agent], force: bool) -> bool:
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


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI Rules - Manage user-level AI agent configurations."""
    pass


def cleanup_deprecated_symlinks(
    selected_agents: List[Agent], config_dir: Path, force: bool, dry_run: bool
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

            # Skip if doesn't exist
            if not target.exists() and not target.is_symlink():
                continue

            # Only remove if it's a symlink (not a regular file)
            if not target.is_symlink():
                continue

            # Check if it points to our AGENTS.md file
            try:
                resolved = target.resolve()
                if resolved != agents_md:
                    # Points to something else, don't touch it
                    continue
            except (OSError, RuntimeError):
                # Broken symlink, but let's be conservative and skip it
                continue

            # Safe to remove - it's our deprecated symlink
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
    selected_agents: List[Agent], force: bool, dry_run: bool
) -> Dict[str, int]:
    """Install user-level symlinks for all selected agents.

    Returns dict with keys: created, updated, skipped, excluded, errors
    """
    console.print("[bold cyan]User-Level Configuration[/bold cyan]")

    # Clean up deprecated symlinks first
    if selected_agents:
        config_dir = selected_agents[0].config_dir
        cleanup_deprecated_symlinks(selected_agents, config_dir, force, dry_run)

    created = updated = skipped = excluded = errors = 0

    for agent in selected_agents:
        console.print(f"\n[bold]{agent.name}[/bold]")

        all_symlinks = agent.get_symlinks()
        filtered_symlinks = agent.get_filtered_symlinks()
        excluded_count = len(all_symlinks) - len(filtered_symlinks)

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


def install_project_symlinks(
    selected_agents: List[Agent],
    selected_projects: Dict[str, ProjectConfig],
    config: Config,
    repo_root: Path,
    force: bool,
    dry_run: bool,
) -> Dict[str, int]:
    """Install project-level symlinks for all selected projects.

    Returns dict with keys: created, updated, skipped, excluded, errors
    """
    created = updated = skipped = excluded = errors = 0

    if not selected_projects:
        return {"created": 0, "updated": 0, "skipped": 0, "excluded": 0, "errors": 0}

    console.print("\n[bold cyan]Project-Level Configurations[/bold cyan]")

    for project_name, project in selected_projects.items():
        console.print(f"\n[bold]{project_name}[/bold] [dim]({project.path})[/dim]")

        project_agents_file = (
            repo_root / "config" / "projects" / project_name / "AGENTS.md"
        )
        if not project_agents_file.exists():
            console.print(
                f"  [yellow]⚠[/yellow] No AGENTS.md found for project '{project_name}'\n"
                f"    [dim]Create: config/projects/{project_name}/AGENTS.md[/dim]"
            )
            continue

        for agent in selected_agents:
            all_project_symlinks = agent.get_project_symlinks(project)
            filtered_project_symlinks = get_filtered_project_symlinks(
                agent, project, config, project_name
            )
            excluded_count = len(all_project_symlinks) - len(filtered_project_symlinks)

            if excluded_count > 0:
                excluded += excluded_count

            agent_label = f"[{agent.agent_id}]"
            for target, source in filtered_project_symlinks:
                effective_force = force or not dry_run
                result, message = create_symlink(
                    target, source, effective_force, dry_run
                )

                if result == SymlinkResult.CREATED:
                    console.print(
                        f"  [green]✓[/green] {agent_label} {target.name} → {source}"
                    )
                    created += 1
                elif result == SymlinkResult.ALREADY_CORRECT:
                    console.print(
                        f"  [dim]•[/dim] {agent_label} {target.name} [dim](already correct)[/dim]"
                    )
                elif result == SymlinkResult.UPDATED:
                    console.print(
                        f"  [yellow]↻[/yellow] {agent_label} {target.name} → {source}"
                    )
                    updated += 1
                elif result == SymlinkResult.SKIPPED:
                    console.print(
                        f"  [yellow]○[/yellow] {agent_label} {target.name} [dim](skipped)[/dim]"
                    )
                    skipped += 1
                elif result == SymlinkResult.ERROR:
                    console.print(
                        f"  [red]✗[/red] {agent_label} {target.name}: {message}"
                    )
                    errors += 1

            if excluded_count > 0:
                console.print(
                    f"  [dim]{agent_label} ({excluded_count} symlink(s) excluded by config)[/dim]"
                )

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "excluded": excluded,
        "errors": errors,
    }


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
)
@click.option(
    "--projects",
    help="Comma-separated list of projects to install (default: all projects)",
)
@click.option(
    "--user-only",
    is_flag=True,
    help="Install only user-level configs, skip all projects",
)
def install(
    force: bool,
    dry_run: bool,
    rebuild_cache: bool,
    agents: Optional[str],
    projects: Optional[str],
    user_only: bool,
):
    """Install AI agent configs via symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)

    if rebuild_cache and not dry_run:
        import shutil

        cache_dir = Config.get_cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            console.print("[dim]✓ Cleared settings cache[/dim]")
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    if not user_only:
        validation_errors = config.validate_projects()
        if validation_errors:
            console.print("[red]Error:[/red] Project validation failed:\n")
            for error in validation_errors:
                console.print(f"  • {error}")
            console.print(
                "\n[dim]Fix these issues or use --user-only to skip projects[/dim]"
            )
            sys.exit(1)

    selected_projects = filter_selected_projects(config, projects, user_only)

    if not dry_run and not check_first_run(selected_agents, force):
        console.print("[yellow]Installation cancelled[/yellow]")
        sys.exit(0)

    if dry_run:
        console.print("[bold]Dry run mode - no changes will be made[/bold]\n")

    if not dry_run:
        for agent in selected_agents:
            if agent.agent_id in ["claude", "goose"]:
                settings_file = (
                    repo_root / "config" / agent.agent_id / agent.config_file_name
                )
                if settings_file.exists():
                    config.build_merged_settings(
                        agent.agent_id,
                        settings_file,
                        repo_root,
                        force_rebuild=rebuild_cache,
                    )

        orphaned = config.cleanup_orphaned_cache(repo_root)
        if orphaned:
            console.print(
                f"[dim]✓ Cleaned up orphaned cache for: {', '.join(orphaned)}[/dim]"
            )

    user_results = install_user_symlinks(selected_agents, force, dry_run)

    project_results = install_project_symlinks(
        selected_agents, selected_projects, config, repo_root, force, dry_run
    )

    claude_agent = next((a for a in selected_agents if a.agent_id == "claude"), None)
    if claude_agent:
        from ai_rules.mcp import MCPManager, OperationResult

        result, message, conflicts = claude_agent.install_mcps(
            force=force, dry_run=dry_run
        )

        if conflicts and not force:
            console.print("\n[bold yellow]MCP Conflicts Detected:[/bold yellow]")
            mgr = MCPManager()
            expected_mcps = mgr.load_managed_mcps(repo_root, config)
            claude_data = mgr.load_claude_json()
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

    total_created = user_results["created"] + project_results["created"]
    total_updated = user_results["updated"] + project_results["updated"]
    total_skipped = user_results["skipped"] + project_results["skipped"]
    total_excluded = user_results["excluded"] + project_results["excluded"]
    total_errors = user_results["errors"] + project_results["errors"]
    if not dry_run:
        hooks_dir = repo_root / ".hooks"
        post_merge_hook = hooks_dir / "post-merge"
        git_dir = repo_root / ".git"

        if post_merge_hook.exists() and git_dir.is_dir():
            import subprocess

            try:
                subprocess.run(
                    ["git", "config", "core.hooksPath", ".hooks"],
                    cwd=repo_root,
                    check=True,
                    capture_output=True,
                )
                console.print("\n[dim]✓ Configured git hooks[/dim]")
            except subprocess.CalledProcessError:
                pass

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
    agent_label: Optional[str] = None,
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
)
@click.option(
    "--projects",
    help="Comma-separated list of projects to check (default: all projects)",
)
@click.option(
    "--user-only",
    is_flag=True,
    help="Check only user-level configs, skip all projects",
)
def status(agents: Optional[str], projects: Optional[str], user_only: bool):
    """Check status of AI agent symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    console.print("[bold]AI Rules Status[/bold]\n")

    all_correct = True

    console.print("[bold cyan]User-Level Configuration[/bold cyan]\n")
    cache_stale = False
    for agent in selected_agents:
        console.print(f"[bold]{agent.name}:[/bold]")

        all_symlinks = agent.get_symlinks()
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
                repo_root / "config" / agent.agent_id / agent_config["config_file"]
            )
            if config.is_cache_stale(agent.agent_id, base_settings_path, repo_root):
                console.print("  [yellow]⚠[/yellow] Cached settings are stale")
                all_correct = False
                cache_stale = True

        if agent.agent_id == "claude":
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

    if not user_only and config.projects:
        selected_projects = filter_selected_projects(config, projects, user_only=False)

        if selected_projects:
            console.print("[bold cyan]Project-Level Configurations[/bold cyan]\n")
            for project_name, project in selected_projects.items():
                console.print(
                    f"[bold]{project_name}[/bold] [dim]({project.path})[/dim]"
                )

                if not project.path.exists():
                    console.print("  [red]✗[/red] Project path does not exist")
                    all_correct = False
                    console.print()
                    continue

                for agent in selected_agents:
                    all_project_symlinks = agent.get_project_symlinks(project)
                    filtered_project_symlinks = get_filtered_project_symlinks(
                        agent, project, config, project_name
                    )
                    excluded_symlinks = [
                        (t, s)
                        for t, s in all_project_symlinks
                        if (t, s) not in filtered_project_symlinks
                    ]

                    agent_label = f"[{agent.agent_id}]"
                    for target, source in filtered_project_symlinks:
                        status_code, message = check_symlink(target, source)
                        is_correct = _display_symlink_status(
                            status_code, target, source, message, agent_label
                        )
                        if not is_correct:
                            all_correct = False

                    for target, _ in excluded_symlinks:
                        console.print(
                            f"  [dim]○[/dim] {agent_label} {target.name} [dim](excluded by config)[/dim]"
                        )

                    agent_config = AGENT_CONFIG_METADATA.get(agent.agent_id)
                    if agent_config and agent.agent_id in config.settings_overrides:
                        base_settings_path = (
                            repo_root
                            / "config"
                            / agent.agent_id
                            / agent_config["config_file"]
                        )
                        if config.is_cache_stale(
                            agent.agent_id, base_settings_path, repo_root
                        ):
                            console.print(
                                f"  [yellow]⚠[/yellow] {agent_label} Cached settings are stale"
                            )
                            all_correct = False
                            cache_stale = True

                console.print()

    console.print("[bold cyan]Git Hooks Configuration[/bold cyan]\n")
    hooks_dir = repo_root / ".hooks"
    post_merge_hook = hooks_dir / "post-merge"

    if post_merge_hook.exists() and (repo_root / ".git").is_dir():
        import subprocess

        try:
            result = subprocess.run(
                ["git", "config", "--get", "core.hooksPath"],
                cwd=repo_root,
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
        console.print("  [dim]○[/dim] Post-merge hook not available in this repository")

    console.print()

    if not all_correct:
        if cache_stale:
            console.print(
                "[yellow]💡 Run 'ai-rules install --rebuild-cache' to fix issues[/yellow]"
            )
        else:
            console.print("[yellow]💡 Run 'ai-rules install' to fix issues[/yellow]")
        sys.exit(1)
    else:
        console.print("[green]All symlinks are correct![/green]")


@main.command()
@click.option("--force", is_flag=True, help="Skip confirmations")
@click.option(
    "--agents",
    help="Comma-separated list of agents to uninstall (default: all)",
)
@click.option(
    "--projects",
    help="Comma-separated list of projects to uninstall (default: all projects)",
)
@click.option(
    "--user-only",
    is_flag=True,
    help="Uninstall only user-level configs, skip all projects",
)
def uninstall(
    force: bool, agents: Optional[str], projects: Optional[str], user_only: bool
):
    """Remove AI agent symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    selected_projects = filter_selected_projects(config, projects, user_only)

    if not force:
        console.print("[yellow]Warning:[/yellow] This will remove symlinks for:\n")
        console.print("[bold]Agents:[/bold]")
        for agent in selected_agents:
            console.print(f"  • {agent.name}")
        if selected_projects:
            console.print("\n[bold]Projects:[/bold]")
            for project_name in selected_projects:
                console.print(f"  • {project_name}")
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

        if agent.agent_id == "claude":
            from ai_rules.mcp import OperationResult

            result, message = agent.uninstall_mcps(force=force, dry_run=False)
            if result == OperationResult.REMOVED:
                console.print(f"  [green]✓[/green] {message}")
            elif result == OperationResult.NOT_FOUND:
                console.print(f"  [dim]•[/dim] {message}")

    if selected_projects:
        console.print("\n[bold cyan]Project-Level Configurations[/bold cyan]")
        for project_name, project in selected_projects.items():
            console.print(f"\n[bold]{project_name}[/bold] [dim]({project.path})[/dim]")

            for agent in selected_agents:
                filtered_project_symlinks = get_filtered_project_symlinks(
                    agent, project, config, project_name
                )

                agent_label = f"[{agent.agent_id}]"
                for target, _ in filtered_project_symlinks:
                    success, message = remove_symlink(target, force)

                    if success:
                        console.print(
                            f"  [green]✓[/green] {agent_label} {target.name} removed"
                        )
                        total_removed += 1
                    elif "Does not exist" in message:
                        console.print(
                            f"  [dim]•[/dim] {agent_label} {target.name} [dim](not installed)[/dim]"
                        )
                    else:
                        console.print(
                            f"  [yellow]○[/yellow] {agent_label} {target.name} [dim]({message})[/dim]"
                        )
                        total_skipped += 1

    console.print(
        f"\n[bold]Summary:[/bold] Removed {total_removed}, skipped {total_skipped}"
    )


@main.command("list-projects")
def list_projects_cmd():
    """List configured projects."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)

    if not config.projects:
        console.print("[yellow]No projects configured[/yellow]")
        console.print(
            "\n[dim]Add projects to ~/.ai-rules-config.yaml or run 'ai-rules add-project'[/dim]"
        )
        return

    table = Table(title="Configured Projects", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="bold")
    table.add_column("Exclusions", justify="right")
    table.add_column("Status")

    for project_name, project in config.projects.items():
        path_str = str(project.path)
        exclusions = len(project.exclude_symlinks)
        exclusions_str = str(exclusions) if exclusions > 0 else "-"

        if project.path.exists():
            status = "[green]✓ Exists[/green]"
        else:
            status = "[red]✗ Missing[/red]"

        table.add_row(project_name, path_str, exclusions_str, status)

    console.print(table)


@main.command("add-project")
@click.argument("name")
@click.argument("path")
def add_project_cmd(name: str, path: str):
    """Add a new project configuration."""
    from pathlib import Path as PathLib

    config_path = PathLib.home() / ".ai-rules-config.yaml"

    project_path = PathLib(path).expanduser().resolve()

    if not project_path.exists():
        console.print(f"[red]Error:[/red] Path does not exist: {project_path}")
        console.print("[dim]Create the directory first, or check the path[/dim]")
        sys.exit(1)

    if not project_path.is_dir():
        console.print(f"[red]Error:[/red] Path is not a directory: {project_path}")
        sys.exit(1)

    existing_config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            existing_config = yaml.safe_load(f) or {}

    projects = existing_config.get("projects", {})
    if name in projects:
        console.print(f"[yellow]Warning:[/yellow] Project '{name}' already exists")
        if not Confirm.ask("Overwrite?", default=False):
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)

    projects[name] = {"path": str(project_path), "exclude_symlinks": []}
    existing_config["projects"] = projects
    with open(config_path, "w") as f:
        yaml.safe_dump(existing_config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]✓[/green] Added project '{name}' at {project_path}")
    console.print(
        f"\n[dim]Next steps:[/dim]\n"
        f"  1. Create project config: mkdir -p config/projects/{name}\n"
        f"  2. Add rules: edit config/projects/{name}/AGENTS.md\n"
        f"  3. Install: ai-rules install --projects {name}"
    )


@main.command("remove-project")
@click.argument("name")
@click.option("--force", is_flag=True, help="Skip confirmation")
def remove_project_cmd(name: str, force: bool):
    """Remove a project configuration."""
    from pathlib import Path as PathLib

    config_path = PathLib.home() / ".ai-rules-config.yaml"

    if not config_path.exists():
        console.print("[yellow]No config file found[/yellow]")
        sys.exit(1)

    with open(config_path, "r") as f:
        existing_config = yaml.safe_load(f) or {}

    projects = existing_config.get("projects", {})
    if name not in projects:
        console.print(f"[red]Error:[/red] Project '{name}' not found")
        console.print(
            f"[dim]Available projects: {', '.join(projects.keys()) or 'none'}[/dim]"
        )
        sys.exit(1)

    if not force:
        console.print(f"[yellow]Warning:[/yellow] Remove project '{name}'?")
        console.print(f"  Path: {projects[name].get('path', 'unknown')}")
        console.print(
            "\n[dim]This will not remove the project directory or symlinks[/dim]"
        )
        console.print(
            "[dim]Run 'ai-rules uninstall --projects {name}' first to remove symlinks[/dim]\n"
        )
        if not Confirm.ask("Continue?", default=False):
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)

    del projects[name]
    existing_config["projects"] = projects
    with open(config_path, "w") as f:
        yaml.safe_dump(existing_config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]✓[/green] Removed project '{name}' from configuration")


@main.command("list-agents")
def list_agents_cmd():
    """List available AI agents."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    agents = get_agents(repo_root, config)

    table = Table(title="Available AI Agents", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Symlinks", justify="right")
    table.add_column("Status")

    for agent in agents:
        all_symlinks = agent.get_symlinks()
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
@click.option("--force", is_flag=True, help="Skip confirmations")
def update(force: bool):
    """Re-sync symlinks (useful after adding new agents/commands)."""
    console.print("[bold]Updating AI Rules symlinks...[/bold]\n")

    ctx = click.get_current_context()
    ctx.invoke(
        install,
        force=force,
        dry_run=False,
        rebuild_cache=False,
        agents=None,
        projects=None,
        user_only=False,
    )


@main.command()
@click.option(
    "--agents",
    help="Comma-separated list of agents to validate (default: all)",
)
def validate(agents: Optional[str]):
    """Validate configuration and source files."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    console.print("[bold]Validating AI Rules Configuration[/bold]\n")

    all_valid = True
    total_checked = 0
    total_issues = 0

    for agent in selected_agents:
        console.print(f"[bold]{agent.name}:[/bold]")
        agent_issues = []

        for target, source in agent.get_symlinks():
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
            for t, s in agent.get_symlinks()
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
)
def diff(agents: Optional[str]):
    """Show differences between repo configs and installed symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
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
def exclude():
    """Manage exclusion patterns."""
    pass


@exclude.command("add")
@click.argument("pattern")
def exclude_add(pattern: str):
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
def exclude_remove(pattern: str):
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
def exclude_list():
    """List all exclusion patterns."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    user_config_path = Path.home() / ".ai-rules-config.yaml"
    repo_config_path = repo_root / ".ai-rules-config.yaml"

    if not config.exclude_symlinks:
        console.print("[dim]No exclusion patterns configured[/dim]")
        return

    console.print("[bold]Exclusion Patterns:[/bold]\n")

    user_exclusions = []
    repo_exclusions = []

    if user_config_path.exists():
        with open(user_config_path, "r") as f:
            data = yaml.safe_load(f) or {}
            user_exclusions = data.get("exclude_symlinks", [])

    if repo_config_path.exists():
        with open(repo_config_path, "r") as f:
            data = yaml.safe_load(f) or {}
            repo_exclusions = data.get("exclude_symlinks", [])

    for pattern in sorted(config.exclude_symlinks):
        source = []
        if pattern in user_exclusions:
            source.append("user")
        if pattern in repo_exclusions:
            source.append("repo")
        source_str = ", ".join(source)
        console.print(f"  • {pattern} [dim]({source_str})[/dim]")


@main.group()
def override():
    """Manage settings overrides."""
    pass


@override.command("set")
@click.argument("key")
@click.argument("value")
def override_set(key: str, value: str):
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
    repo_root = get_repo_root()

    parts = key.split(".", 1)
    if len(parts) != 2:
        console.print("[red]Error:[/red] Key must be in format 'agent.setting'")
        console.print(
            "[dim]Example: claude.model or claude.hooks.SubagentStop[0].command[/dim]"
        )
        sys.exit(1)

    agent, setting = parts

    is_valid, error_msg, warning_msg, suggestions = validate_override_path(
        agent, setting, repo_root
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
def override_unset(key: str):
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
def override_list():
    """List all settings overrides."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)

    if not config.settings_overrides:
        console.print("[dim]No settings overrides configured[/dim]")
        return

    console.print("[bold]Settings Overrides:[/bold]\n")

    for agent, overrides in sorted(config.settings_overrides.items()):
        console.print(f"[bold]{agent}:[/bold]")
        for key, value in sorted(overrides.items()):
            console.print(f"  • {key}: {value}")
        console.print()


@main.group()
def config():
    """Manage ai-rules configuration."""
    pass


@config.command("show")
@click.option(
    "--merged", is_flag=True, help="Show merged settings with overrides applied"
)
@click.option("--agent", help="Show config for specific agent only")
def config_show(merged: bool, agent: Optional[str]):
    """Show current configuration."""
    repo_root = get_repo_root()
    cfg = Config.load(repo_root)
    user_config_path = Path.home() / ".ai-rules-config.yaml"

    if merged:
        console.print("[bold]Merged Settings:[/bold]\n")

        agents_to_show = [agent] if agent else ["claude", "goose"]

        for agent_name in agents_to_show:
            if agent_name not in cfg.settings_overrides:
                console.print(
                    f"[dim]{agent_name}: No overrides (using repo settings)[/dim]\n"
                )
                continue

            console.print(f"[bold]{agent_name}:[/bold]")

            from ai_rules.config import AGENT_CONFIG_METADATA

            agent_config = AGENT_CONFIG_METADATA.get(agent_name)
            if not agent_config:
                console.print(f"  [red]✗[/red] Unknown agent: {agent_name}")
                console.print()
                continue

            base_path = repo_root / "config" / agent_name / agent_config["config_file"]
            if base_path.exists():
                with open(base_path, "r") as f:
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
            with open(user_config_path, "r") as f:
                content = f.read()
            console.print(f"[bold]User Config:[/bold] {user_config_path}")
            console.print(content)
        else:
            console.print(f"[dim]No user config at {user_config_path}[/dim]\n")

        repo_config_path = repo_root / ".ai-rules-config.yaml"
        if repo_config_path.exists():
            with open(repo_config_path, "r") as f:
                content = f.read()
            console.print(f"\n[bold]Repo Config:[/bold] {repo_config_path}")
            console.print(content)


@config.command("edit")
def config_edit():
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


def _get_common_exclusions() -> List[Tuple[str, str, bool]]:
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


def _collect_exclusion_patterns() -> List[str]:
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


def _collect_settings_overrides() -> Dict[str, Dict[str, any]]:
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


def _collect_project_configurations() -> Dict[str, Dict[str, any]]:
    """Collect project configurations from user (Step 3).

    Returns:
        Dictionary of project configurations
    """
    console.print("\n[bold]Step 3: Projects (Optional)[/bold]")
    response = console.input(
        "Do you want to configure project-specific settings? [y/N]: "
    )

    if response.lower() != "y":
        return {}

    projects = {}

    while True:
        console.print("\n[dim]Leave project name empty to finish[/dim]")
        project_name = console.input("Project name: ").strip()
        if not project_name:
            break

        project_path = console.input("Project path: ").strip()
        if not project_path:
            console.print("[yellow]Path required[/yellow]")
            continue

        project_config = {"path": project_path}

        console.print(f"\n[dim]Project-specific exclusions for '{project_name}':[/dim]")
        console.print("[dim]One per line, empty line to finish:[/dim]")
        project_exclusions = []
        while True:
            pattern = console.input("> ").strip()
            if not pattern:
                break
            project_exclusions.append(pattern)
            console.print(f"  [green]✓[/green] Added: {pattern}")

        if project_exclusions:
            project_config["exclude_symlinks"] = project_exclusions

        projects[project_name] = project_config
        console.print(f"[green]✓[/green] Added project: {project_name}")

        if not Confirm.ask("\nAdd another project?", default=False):
            break

    if projects:
        console.print(f"\n[green]✓[/green] Configured {len(projects)} project(s)")

    return projects


def _display_configuration_summary(config_data: Dict[str, any]) -> None:
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

    if "projects" in config_data:
        console.print(f"\n[bold]Projects ({len(config_data['projects'])}):[/bold]")
        for name, proj in config_data["projects"].items():
            console.print(f"  [bold]{name}:[/bold]")
            console.print(f"    • path: {proj['path']}")
            if "exclude_symlinks" in proj:
                console.print(
                    f"    • exclusions: {', '.join(proj['exclude_symlinks'])}"
                )

    console.print("\n" + "=" * 50)


@config.command("init")
def config_init():
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

    config_data = {"version": 1}

    selected_exclusions = _collect_exclusion_patterns()
    if selected_exclusions:
        config_data["exclude_symlinks"] = selected_exclusions

    settings_overrides = _collect_settings_overrides()
    if settings_overrides:
        config_data["settings_overrides"] = settings_overrides

    projects = _collect_project_configurations()
    if projects:
        config_data["projects"] = projects

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


if __name__ == "__main__":
    main()
