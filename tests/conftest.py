import json
import os

import pytest


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


@pytest.fixture
def load_fixture():
    def _load_file(filename):
        with open(os.path.join("tests", "fixtures", filename)) as f:
            return json.load(f)

    return _load_file


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Create a mock home directory for testing."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    return home_dir


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository structure with config files."""
    repo_root = tmp_path / "test-repo"
    repo_root.mkdir()

    config_dir = repo_root / "config"
    config_dir.mkdir()

    (config_dir / "AGENTS.md").write_text("# Shared Agent Rules\nTest content")

    claude_dir = config_dir / "claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text('{"test": "settings"}')

    claude_agents = claude_dir / "agents"
    claude_agents.mkdir()
    (claude_agents / "test-agent.md").write_text("# Test Agent\nAgent content")

    claude_commands = claude_dir / "commands"
    claude_commands.mkdir()
    (claude_commands / "test-command.md").write_text("# Test Command\nCommand content")

    goose_dir = config_dir / "goose"
    goose_dir.mkdir()
    (goose_dir / "config.yaml").write_text("test: config")

    return repo_root
