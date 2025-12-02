"""Tests for MCP management functionality."""

import json

import pytest

from ai_rules.config import Config
from ai_rules.mcp import MCPManager, OperationResult


@pytest.fixture(autouse=True)
def setup_test_mcp(test_repo):
    """Add test-mcp to mcps.json for MCP-specific tests."""
    mcps_file = test_repo / "claude" / "mcps.json"
    mcps_data = {"test-mcp": {"type": "stdio", "command": "test", "args": []}}
    mcps_file.write_text(json.dumps(mcps_data, indent=2))
    return test_repo


@pytest.fixture
def manager():
    """Create an MCPManager instance."""
    return MCPManager()


@pytest.fixture
def config_with_overrides():
    """Create a config with MCP overrides."""
    return Config(
        mcp_overrides={
            "test-mcp": {"env": {"TEST_API_KEY": "test-key"}},
            "override-only": {"type": "stdio", "command": "override-mcp", "args": []},
        }
    )


def test_load_managed_mcps(manager, test_repo):
    """Test loading managed MCPs from repo config file."""
    config = Config()
    mcps = manager.load_managed_mcps(test_repo, config)

    assert "test-mcp" in mcps
    assert mcps["test-mcp"]["type"] == "stdio"
    assert mcps["test-mcp"]["command"] == "test"


def test_merge_mcp_overrides(manager, test_repo, config_with_overrides):
    """Test that user overrides merge correctly with base MCPs."""
    mcps = manager.load_managed_mcps(test_repo, config_with_overrides)

    assert mcps["test-mcp"]["env"]["TEST_API_KEY"] == "test-key"
    assert mcps["test-mcp"]["type"] == "stdio"
    assert mcps["test-mcp"]["command"] == "test"

    assert "override-only" in mcps
    assert mcps["override-only"]["command"] == "override-mcp"


def test_install_mcps_fresh(manager, mock_home, test_repo):
    """Test first install creates tracking and updates ~/.claude.json."""
    config = Config()
    result, message, conflicts = manager.install_mcps(test_repo, config)

    assert result == OperationResult.UPDATED
    assert "MCPs installed" in message
    assert conflicts == []

    assert manager.CLAUDE_JSON.exists()
    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert "mcpServers" in data
        assert "test-mcp" in data["mcpServers"]
        assert data["mcpServers"]["test-mcp"]["_managedBy"] == "ai-rules"


def test_install_mcps_update(manager, mock_home, test_repo):
    """Test subsequent install updates existing MCPs."""
    config = Config()

    manager.install_mcps(test_repo, config, force=True)

    mcps_file = test_repo / "claude" / "mcps.json"
    with open(mcps_file) as f:
        mcps_data = json.load(f)
        mcps_data["test-mcp"]["args"] = ["modified"]
    with open(mcps_file, "w") as f:
        json.dump(mcps_data, f)

    result, message, conflicts = manager.install_mcps(test_repo, config, force=True)
    assert result == OperationResult.UPDATED

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert data["mcpServers"]["test-mcp"]["args"] == ["modified"]


def test_install_mcps_conflict_detection(manager, mock_home, test_repo):
    """Test that conflicts are detected when user modifies managed MCP."""
    config = Config()

    manager.install_mcps(test_repo, config, force=True)

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        data["mcpServers"]["test-mcp"]["args"] = ["user-modified"]
    with open(manager.CLAUDE_JSON, "w") as f:
        json.dump(data, f)

    result, message, conflicts = manager.install_mcps(test_repo, config, force=False)
    assert result == OperationResult.ERROR
    assert "test-mcp" in conflicts


def test_uninstall_mcps(manager, mock_home, test_repo):
    """Test that uninstall removes only tracked MCPs."""
    config = Config()
    manager.install_mcps(test_repo, config, force=True)

    result, message = manager.uninstall_mcps(force=True)
    assert result == OperationResult.REMOVED
    assert "Removed" in message

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert "test-mcp" not in data.get("mcpServers", {})


def test_uninstall_preserves_user_mcps(manager, mock_home, test_repo):
    """Test that user MCPs are untouched during uninstall."""
    config = Config()
    manager.install_mcps(test_repo, config, force=True)

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        data["mcpServers"]["user-custom-mcp"] = {
            "type": "stdio",
            "command": "user-mcp",
            "args": [],
        }
    with open(manager.CLAUDE_JSON, "w") as f:
        json.dump(data, f)

    manager.uninstall_mcps(force=True)

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert "user-custom-mcp" in data["mcpServers"]
        assert "test-mcp" not in data["mcpServers"]


def test_status_shows_managed_vs_unmanaged(manager, mock_home, test_repo):
    """Test that status correctly categorizes managed vs unmanaged MCPs."""
    config = Config()
    manager.install_mcps(test_repo, config, force=True)

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        data["mcpServers"]["user-mcp"] = {
            "type": "stdio",
            "command": "user-mcp",
            "args": [],
        }
    with open(manager.CLAUDE_JSON, "w") as f:
        json.dump(data, f)

    status = manager.get_status(test_repo, config)

    assert "test-mcp" in status.managed_mcps
    assert "user-mcp" in status.unmanaged_mcps


def test_claude_json_missing(manager, mock_home, test_repo):
    """Test that install handles missing ~/.claude.json gracefully."""
    config = Config()
    assert not manager.CLAUDE_JSON.exists()

    result, message, conflicts = manager.install_mcps(test_repo, config)
    assert result == OperationResult.UPDATED
    assert manager.CLAUDE_JSON.exists()

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert "mcpServers" in data


def test_atomic_write_backup(manager, mock_home, test_repo):
    """Test that backup is created before modification."""
    config = Config()

    original_content = {"mcpServers": {}, "existingKey": "existingValue"}
    manager.CLAUDE_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(manager.CLAUDE_JSON, "w") as f:
        json.dump(original_content, f)

    manager.install_mcps(test_repo, config, force=True)

    backup_files = list(manager.CLAUDE_JSON.parent.glob("*.ai-rules-backup.*"))
    assert len(backup_files) == 1

    with open(backup_files[0]) as f:
        backup_data = json.load(f)
        assert backup_data == original_content


def test_dry_run_mode(manager, mock_home, test_repo):
    """Test that dry run mode doesn't modify files."""
    config = Config()

    result, message, conflicts = manager.install_mcps(test_repo, config, dry_run=True)
    assert result == OperationResult.UPDATED
    assert "Would update" in message

    assert not manager.CLAUDE_JSON.exists()


def test_format_diff(manager):
    """Test diff formatting for conflicts."""
    expected = {"type": "stdio", "command": "uvx", "args": ["mcp_test@latest"]}
    installed = {"type": "stdio", "command": "uvx", "args": ["mcp_test@0.2.0"]}

    diff = manager.format_diff("test-mcp", expected, installed)
    assert "test-mcp" in diff
    assert "mcp_test@latest" in diff
    assert "mcp_test@0.2.0" in diff
    assert "Expected (repo)" in diff
    assert "Installed (local)" in diff


def test_detect_conflicts(manager):
    """Test conflict detection logic."""
    expected = {"mcp1": {"command": "cmd1"}, "mcp2": {"command": "cmd2"}}
    installed = {"mcp1": {"command": "cmd1-modified"}, "mcp2": {"command": "cmd2"}}

    conflicts = manager.detect_conflicts(expected, installed)
    assert conflicts == ["mcp1"]


def test_status_sync_detection(manager, mock_home, test_repo):
    """Test that status correctly detects synced vs outdated MCPs."""
    config = Config()
    manager.install_mcps(test_repo, config, force=True)

    status = manager.get_status(test_repo, config)
    assert status.synced["test-mcp"] is True

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        data["mcpServers"]["test-mcp"]["args"] = ["modified"]
    with open(manager.CLAUDE_JSON, "w") as f:
        json.dump(data, f)

    status = manager.get_status(test_repo, config)
    assert status.synced["test-mcp"] is False


def test_status_override_detection(
    manager, mock_home, test_repo, config_with_overrides
):
    """Test that status detects which MCPs have overrides."""
    manager.install_mcps(test_repo, config_with_overrides, force=True)

    status = manager.get_status(test_repo, config_with_overrides)
    assert status.has_overrides["test-mcp"] is True
    assert status.has_overrides.get("override-only", False) is True


def test_install_removes_mcps_no_longer_in_repo(manager, mock_home, test_repo):
    """Test that MCPs removed from repo config are cleaned up on install."""
    config = Config()

    manager.install_mcps(test_repo, config, force=True)
    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert "test-mcp" in data["mcpServers"]
        assert data["mcpServers"]["test-mcp"]["_managedBy"] == "ai-rules"

    mcps_file = test_repo / "claude" / "mcps.json"
    mcps_file.write_text("{}")

    result, message, _ = manager.install_mcps(test_repo, config, force=True)
    assert result == OperationResult.UPDATED
    assert "removed" in message

    with open(manager.CLAUDE_JSON) as f:
        data = json.load(f)
        assert "test-mcp" not in data.get("mcpServers", {})
