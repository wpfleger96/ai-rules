"""Command-line interface for ai-rules."""

import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

from ai_rules.agents.base import Agent
from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.config import Config
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

    response = console.input("[yellow]?[/yellow] Continue? (y/N): ")
    return response.lower() == "y"


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI Rules - Manage user-level AI agent configurations."""
    pass


@main.command()
@click.option("--force", is_flag=True, help="Skip all confirmations")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option(
    "--agents",
    help="Comma-separated list of agents to install (default: all)",
)
def install(force: bool, dry_run: bool, agents: Optional[str]):
    """Install AI agent configs via symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    if not dry_run and not check_first_run(selected_agents, force):
        console.print("[yellow]Installation cancelled[/yellow]")
        sys.exit(0)

    if dry_run:
        console.print("[bold]Dry run mode - no changes will be made[/bold]\n")

    total_created = 0
    total_updated = 0
    total_skipped = 0
    total_excluded = 0
    total_errors = 0

    for agent in selected_agents:
        console.print(f"\n[bold]{agent.name}[/bold]")

        all_symlinks = agent.get_symlinks()
        filtered_symlinks = agent.get_filtered_symlinks()
        excluded_count = len(all_symlinks) - len(filtered_symlinks)

        if excluded_count > 0:
            console.print(
                f"  [dim]({excluded_count} symlink(s) excluded by config)[/dim]"
            )
            total_excluded += excluded_count

        for target, source in filtered_symlinks:
            effective_force = force or not dry_run
            result, message = create_symlink(target, source, effective_force, dry_run)

            if result == SymlinkResult.CREATED:
                console.print(f"  [green]✓[/green] {target} → {source}")
                total_created += 1
            elif result == SymlinkResult.ALREADY_CORRECT:
                console.print(f"  [dim]•[/dim] {target} [dim](already correct)[/dim]")
            elif result == SymlinkResult.UPDATED:
                console.print(f"  [yellow]↻[/yellow] {target} → {source}")
                total_updated += 1
            elif result == SymlinkResult.SKIPPED:
                console.print(f"  [yellow]○[/yellow] {target} [dim](skipped)[/dim]")
                total_skipped += 1
            elif result == SymlinkResult.ERROR:
                console.print(f"  [red]✗[/red] {target}: {message}")
                total_errors += 1

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


@main.command()
@click.option(
    "--agents",
    help="Comma-separated list of agents to check (default: all)",
)
def status(agents: Optional[str]):
    """Check status of AI agent symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    console.print("[bold]AI Rules Status[/bold]\n")

    all_correct = True

    for agent in selected_agents:
        console.print(f"[bold]{agent.name}:[/bold]")

        all_symlinks = agent.get_symlinks()
        filtered_symlinks = agent.get_filtered_symlinks()
        excluded_symlinks = [
            (t, s) for t, s in all_symlinks if (t, s) not in filtered_symlinks
        ]

        for target, source in filtered_symlinks:
            status_code, message = check_symlink(target, source)

            if status_code == "correct":
                console.print(f"  [green]✓[/green] {target}")
            elif status_code == "missing":
                console.print(f"  [red]✗[/red] {target} [dim](not installed)[/dim]")
                all_correct = False
            elif status_code == "broken":
                console.print(f"  [red]✗[/red] {target} [dim](broken symlink)[/dim]")
                all_correct = False
            elif status_code == "wrong_target":
                console.print(f"  [yellow]⚠[/yellow] {target} [dim]({message})[/dim]")
                all_correct = False
            elif status_code == "not_symlink":
                console.print(
                    f"  [yellow]⚠[/yellow] {target} [dim](not a symlink)[/dim]"
                )
                all_correct = False

        for target, _ in excluded_symlinks:
            console.print(f"  [dim]○[/dim] {target} [dim](excluded by config)[/dim]")

        console.print()

    if not all_correct:
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
def uninstall(force: bool, agents: Optional[str]):
    """Remove AI agent symlinks."""
    repo_root = get_repo_root()
    config = Config.load(repo_root)
    all_agents = get_agents(repo_root, config)
    selected_agents = select_agents(all_agents, agents)

    if not force:
        console.print("[yellow]Warning:[/yellow] This will remove symlinks for:\n")
        for agent in selected_agents:
            console.print(f"  • {agent.name}")
        console.print()
        response = console.input("[yellow]?[/yellow] Continue? (y/N): ")
        if response.lower() != "y":
            console.print("[yellow]Uninstall cancelled[/yellow]")
            sys.exit(0)

    total_removed = 0
    total_skipped = 0

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

    console.print(
        f"\n[bold]Summary:[/bold] Removed {total_removed}, skipped {total_skipped}"
    )


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
    ctx.invoke(install, force=force, dry_run=False, agents=None)


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


if __name__ == "__main__":
    main()
