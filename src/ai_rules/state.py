"""State management for ai-rules."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


def _get_state_file() -> Path:
    """Get the state file path."""
    return Path.home() / ".ai-rules" / "state.yaml"


def get_state() -> dict[str, Any]:
    """Load state from file."""
    state_file = _get_state_file()
    if not state_file.exists():
        return {}

    try:
        with state_file.open() as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save_state(state: dict[str, Any]) -> None:
    """Save state to file."""
    state_file = _get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def get_active_profile() -> str | None:
    """Get the currently active profile."""
    state = get_state()
    return state.get("active_profile")


def set_active_profile(profile: str) -> None:
    """Set the active profile."""
    state = get_state()
    state["active_profile"] = profile
    state["last_install"] = datetime.now(UTC).isoformat()
    _save_state(state)
