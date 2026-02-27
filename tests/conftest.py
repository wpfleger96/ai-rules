from pathlib import Path

import pytest

from click.testing import CliRunner


@pytest.fixture(autouse=True)
def clear_config_cache():
    """Clear Config._load_cached() cache before each test to prevent cache pollution."""
    from ai_rules.config import Config

    if hasattr(Config._load_cached, "cache_clear"):
        Config._load_cached.cache_clear()
    yield
    if hasattr(Config._load_cached, "cache_clear"):
        Config._load_cached.cache_clear()


def pytest_configure(config):
    """Register custom test markers to make testing and iterating easier on the developer."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that do not modify real files on the system"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests that modify real files on the system (e.g., symlinks)",
    )
    config.addinivalue_line("markers", "cli: Tests for the CLI sub-module")
    config.addinivalue_line("markers", "config: Tests for the config sub-module")
    config.addinivalue_line("markers", "agents: Tests for the agents sub-module")
    config.addinivalue_line("markers", "bootstrap: Tests for the bootstrap sub-module")


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Create a mock home directory for testing."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home_dir))
    return home_dir


@pytest.fixture
def runner():
    """Create a Click CLI runner for testing CLI commands."""
    return CliRunner()


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository structure with config files.

    Note: As of v0.5.0, config structure changed from repo/config/* to package/config/*.
    This fixture mimics the new package structure for testing.
    """
    config_root = tmp_path / "test-config"
    config_root.mkdir()

    (config_root / "AGENTS.md").write_text("# Shared Agent Rules\nTest content")

    claude_dir = config_root / "claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text('{"test": "settings"}')
    (claude_dir / "CLAUDE.md").write_text("@~/AGENTS.md\n")

    claude_agents = claude_dir / "agents"
    claude_agents.mkdir()
    (claude_agents / "test-agent.md").write_text("# Test Agent\nAgent content")

    claude_commands = claude_dir / "commands"
    claude_commands.mkdir()
    (claude_commands / "test-command.md").write_text("# Test Command\nCommand content")

    codex_dir = config_root / "codex"
    codex_dir.mkdir()
    (codex_dir / "config.toml").write_text(
        'model = "gpt-5.2-codex"\napproval_policy = "on-request"\n'
    )

    goose_dir = config_root / "goose"
    goose_dir.mkdir()
    (goose_dir / "config.yaml").write_text("test: config")
    (goose_dir / ".goosehints").write_text("@~/AGENTS.md\n")

    mcps_file = claude_dir / "mcps.json"
    mcps_file.write_text("{}")

    return config_root
