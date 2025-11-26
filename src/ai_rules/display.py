"""Console display utilities for consistent formatting."""

from ai_rules.symlinks import console


def success(message: str, prefix: str = "") -> None:
    """Display a success message with green checkmark."""
    if prefix:
        console.print(f"  [green]✓[/green] {prefix} {message}")
    else:
        console.print(f"  [green]✓[/green] {message}")


def error(message: str, prefix: str = "") -> None:
    """Display an error message with red X."""
    if prefix:
        console.print(f"  [red]✗[/red] {prefix} {message}")
    else:
        console.print(f"  [red]✗[/red] {message}")


def warning(message: str, prefix: str = "") -> None:
    """Display a warning message with yellow warning symbol."""
    if prefix:
        console.print(f"  [yellow]⚠[/yellow] {prefix} {message}")
    else:
        console.print(f"  [yellow]⚠[/yellow] {message}")


def info(message: str, prefix: str = "") -> None:
    """Display an info message with dim circle."""
    if prefix:
        console.print(f"  [dim]•[/dim] {prefix} {message}")
    else:
        console.print(f"  [dim]•[/dim] {message}")


def dim(message: str) -> None:
    """Display a dimmed message."""
    console.print(f"[dim]{message}[/dim]")
