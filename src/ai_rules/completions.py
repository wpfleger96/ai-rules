"""Shell completion installation and management."""

import os

from pathlib import Path

COMPLETION_MARKER_START = "# ai-rules shell completion"
COMPLETION_MARKER_END = "# End ai-rules shell completion"


def detect_shell() -> str | None:
    """Detect current shell from $SHELL environment variable.

    Returns:
        Shell name ('bash' or 'zsh') if supported, None otherwise
    """
    shell_path = os.environ.get("SHELL", "")
    shell_name = Path(shell_path).name if shell_path else None
    return shell_name if shell_name in ("bash", "zsh") else None


def get_shell_config_candidates(shell: str) -> list[Path]:
    """Return candidate config files for a shell, checking which exist.

    Args:
        shell: Shell name ('bash' or 'zsh')

    Returns:
        List of config file paths that exist on the system
    """
    home = Path.home()
    candidates = {
        "bash": [home / ".bashrc", home / ".bash_profile", home / ".profile"],
        "zsh": [home / ".zshrc", home / ".zprofile"],
    }
    return [p for p in candidates.get(shell, []) if p.exists()]


def find_config_file(shell: str) -> Path | None:
    """Find the appropriate config file - first existing candidate.

    Args:
        shell: Shell name ('bash' or 'zsh')

    Returns:
        Path to config file, or None if no candidates exist
    """
    candidates = get_shell_config_candidates(shell)
    return candidates[0] if candidates else None


def is_completion_installed(config_path: Path) -> bool:
    """Check if completion is already installed in config file.

    Args:
        config_path: Path to shell config file

    Returns:
        True if completion marker found in file
    """
    if not config_path.exists():
        return False

    content = config_path.read_text()
    return COMPLETION_MARKER_START in content


def generate_completion_script(shell: str) -> str:
    """Generate completion script using Click's shell_completion module.

    Args:
        shell: Shell name ('bash' or 'zsh')

    Returns:
        Completion script to add to shell config

    Raises:
        ValueError: If shell is not supported
    """
    from click.shell_completion import get_completion_class

    comp_cls = get_completion_class(shell)
    if comp_cls is None:
        raise ValueError(f"Unsupported shell: {shell}")

    prog_name = "ai-rules"
    env_var = f"_{prog_name.upper().replace('-', '_')}_COMPLETE"

    return f"""{COMPLETION_MARKER_START}
eval "$({env_var}={shell}_source {prog_name})"
{COMPLETION_MARKER_END}"""


def install_completion(shell: str, dry_run: bool = False) -> tuple[bool, str]:
    """Install completion to shell config file.

    Args:
        shell: Shell name ('bash' or 'zsh'), or None to auto-detect
        dry_run: If True, only show what would be done

    Returns:
        Tuple of (success: bool, message: str)
    """
    if shell not in ("bash", "zsh"):
        return False, f"Unsupported shell: {shell}"

    config_path = find_config_file(shell)
    if config_path is None:
        return (
            False,
            f"No {shell} config file found. Expected one of: "
            + ", ".join(str(p) for p in get_shell_config_candidates(shell)),
        )

    if is_completion_installed(config_path):
        return True, f"Completion already installed in {config_path}"

    script = generate_completion_script(shell)

    if dry_run:
        return True, f"Would append completion script to {config_path}"

    try:
        with config_path.open("a") as f:
            f.write(f"\n{script}\n")
        return (
            True,
            f"Completion installed to {config_path}. Restart your shell or run: source {config_path}",
        )
    except Exception as e:
        return False, f"Failed to write to {config_path}: {e}"


def uninstall_completion(config_path: Path) -> tuple[bool, str]:
    """Remove completion block from shell config file.

    Args:
        config_path: Path to shell config file

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not config_path.exists():
        return False, f"Config file not found: {config_path}"

    if not is_completion_installed(config_path):
        return True, f"Completion not installed in {config_path}"

    try:
        content = config_path.read_text()
        lines = content.split("\n")

        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if COMPLETION_MARKER_START in line:
                start_idx = i
            elif COMPLETION_MARKER_END in line:
                end_idx = i
                break

        if start_idx is not None and end_idx is not None:
            new_lines = lines[:start_idx] + lines[end_idx + 1 :]
            new_content = "\n".join(new_lines)
            config_path.write_text(new_content)
            return True, f"Completion removed from {config_path}"
        else:
            return False, f"Could not find completion block markers in {config_path}"
    except Exception as e:
        return False, f"Failed to modify {config_path}: {e}"
