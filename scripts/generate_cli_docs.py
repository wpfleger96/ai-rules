#!/usr/bin/env python3
"""Generate CLI reference documentation from Click help text."""

import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ai_rules.cli import main


def discover_commands(
    group: Any, prefix: str = "ai-rules", include_root: bool = True
) -> list[str]:
    """Recursively discover all CLI commands."""
    commands = []
    if include_root:
        commands.append(f"{prefix} --help")

    for name in sorted(group.list_commands(None)):
        cmd = group.get_command(None, name)
        cmd_path = f"{prefix} {name}"
        commands.append(f"{cmd_path} --help")

        if hasattr(cmd, "list_commands"):
            commands.extend(discover_commands(cmd, cmd_path, include_root=False))

    return commands


def run_help_command(cmd: str) -> tuple[str, str | None]:
    """Run a single help command, return (cmd, output or None)."""
    result = subprocess.run(
        f"uv run {cmd}", shell=True, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return (cmd, None)
    return (cmd, result.stdout)


def generate() -> None:
    """Generate CLI reference documentation from help text."""
    commands = discover_commands(main)
    total = len(commands)
    results: dict[str, str] = {}
    failed: list[str] = []

    print(f"Discovered {total} commands")

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(run_help_command, cmd): cmd for cmd in commands}
        for i, future in enumerate(as_completed(futures), 1):
            cmd, cmd_output = future.result()
            print(f"\rProcessing: {i}/{total} commands...", end="", flush=True)
            if cmd_output is None:
                failed.append(cmd)
            else:
                results[cmd] = cmd_output

    print()

    if failed:
        print(f"⚠️  {len(failed)} command(s) failed:")
        for cmd in failed:
            print(f"  - {cmd}")

    output: list[str] = [
        "# ai-rules CLI Reference\n\n",
        "Auto-generated from `--help`. Do not edit manually.\n\n",
        "This is the complete CLI reference for ai-rules. For quick start examples and usage guides, see [README.md](../README.md).\n\n",
    ]

    for cmd in commands:
        if cmd not in results:
            continue

        cmd_name = cmd.replace(" --help", "")
        output.append(f"## `{cmd_name}`\n\n")
        output.append("```\n")
        output.append(results[cmd])
        output.append("```\n\n")

    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    output_file = docs_dir / "CLI_REFERENCE.md"
    output_file.write_text("".join(output))
    print(f"✓ Generated {output_file} ({len(results)}/{total} commands)")


if __name__ == "__main__":
    generate()
