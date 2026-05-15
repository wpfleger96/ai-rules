"""LSP management commands."""

from __future__ import annotations

import shutil

import click


@click.group()
def lsp() -> None:
    """Manage LSP language server integrations."""
    pass


@lsp.command("status")
def lsp_status() -> None:
    """Show LSP configuration status."""
    from rich.console import Console
    from rich.table import Table

    from ai_rules.config import Config
    from ai_rules.lsp import LSP_REGISTRY, check_binaries
    from ai_rules.plugins import PluginManager

    console = Console()
    config = Config.load()

    if not config.lsp:
        console.print("[dim]No LSP languages configured in profile.[/dim]")
        console.print("\nAdd languages to your profile's [bold]lsp[/bold] key:")
        console.print("[dim]  lsp:")
        console.print("    - python")
        console.print("    - typescript[/dim]")
        return

    plugin_manager = PluginManager()
    installed_plugins = plugin_manager.load_installed_plugins().get("plugins", {})

    table = Table(title="LSP Status")
    table.add_column("Language", style="bold")
    table.add_column("Plugin")
    table.add_column("Plugin Installed")
    table.add_column("Binary")
    table.add_column("Binary Found")

    binary_results = {
        lang: (binary, path) for lang, binary, path in check_binaries(config.lsp)
    }

    for lang in config.lsp:
        entry = LSP_REGISTRY.get(lang)
        if not entry:
            table.add_row(lang, "[red]Unknown[/red]", "", "", "")
            continue

        plugin_key = f"{entry.plugin}@{entry.marketplace}"
        plugin_installed = plugin_key in installed_plugins

        binary_name = entry.binary
        binary_info = binary_results.get(lang)
        binary_found = binary_info[1] is not None if binary_info else False

        table.add_row(
            lang,
            f"{entry.plugin}",
            "[green]Yes[/green]" if plugin_installed else "[yellow]No[/yellow]",
            binary_name,
            "[green]Yes[/green]" if binary_found else "[yellow]No[/yellow]",
        )

    console.print(table)

    missing_binaries = [
        (lang, LSP_REGISTRY[lang])
        for lang in config.lsp
        if lang in LSP_REGISTRY
        and lang in binary_results
        and binary_results[lang][1] is None
    ]

    if missing_binaries:
        console.print("\n[yellow]Missing binaries:[/yellow]")
        for lang, entry in missing_binaries:
            console.print(f"  {lang}: [dim]{entry.install_hint}[/dim]")


@lsp.command("list")
def lsp_list() -> None:
    """List all supported LSP languages."""
    from rich.console import Console
    from rich.table import Table

    from ai_rules.lsp import LSP_REGISTRY

    console = Console()

    table = Table(title="Supported LSP Languages")
    table.add_column("Language", style="bold")
    table.add_column("Plugin")
    table.add_column("Marketplace")
    table.add_column("Binary")
    table.add_column("Install Hint", style="dim")

    for lang in sorted(LSP_REGISTRY.keys()):
        entry = LSP_REGISTRY[lang]
        binary_path = shutil.which(entry.binary)
        binary_display = (
            f"[green]{entry.binary}[/green]"
            if binary_path
            else f"[dim]{entry.binary}[/dim]"
        )
        table.add_row(
            lang,
            entry.plugin,
            entry.marketplace,
            binary_display,
            entry.install_hint,
        )

    console.print(table)
