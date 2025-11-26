"""Integration tests for project-level configuration."""

import pytest
import yaml

from click.testing import CliRunner

from ai_rules.cli import main
from ai_rules.config import Config


@pytest.mark.integration
def test_project_configuration_loading(tmp_path, monkeypatch):
    """Test that projects are correctly loaded from ~/.ai-rules-config.yaml."""
    monkeypatch.setenv("HOME", str(tmp_path))

    project_path = tmp_path / "test-project"
    project_path.mkdir()

    config_file = tmp_path / ".ai-rules-config.yaml"
    config_data = {
        "version": 1,
        "exclude_symlinks": [],
        "projects": {
            "test-project": {
                "path": str(project_path),
                "exclude_symlinks": [".goosehints"],
            }
        },
    }
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    repo_root = tmp_path / "ai-rules"
    repo_root.mkdir()
    (repo_root / "config").mkdir()

    config = Config.load(repo_root)

    assert "test-project" in config.projects
    project = config.projects["test-project"]
    assert project.path == project_path
    assert ".goosehints" in project.exclude_symlinks


@pytest.mark.integration
def test_project_exclusion_logic(tmp_path, monkeypatch):
    """Test that both global and project-specific exclusions are applied."""
    monkeypatch.setenv("HOME", str(tmp_path))

    project_path = tmp_path / "test-project"
    project_path.mkdir()

    config_file = tmp_path / ".ai-rules-config.yaml"
    config_data = {
        "version": 1,
        "exclude_symlinks": ["~/global-file"],
        "projects": {
            "test-project": {
                "path": str(project_path),
                "exclude_symlinks": ["project-file"],
            }
        },
    }
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    repo_root = tmp_path / "ai-rules"
    repo_root.mkdir()
    (repo_root / "config").mkdir()

    config = Config.load(repo_root)

    assert config.is_project_excluded("test-project", "~/global-file")
    assert config.is_project_excluded("test-project", "project-file")
    assert not config.is_project_excluded("test-project", "other-file")


@pytest.mark.integration
def test_add_project_command(tmp_path, monkeypatch):
    """Test add-project command creates correct config structure."""
    monkeypatch.setenv("HOME", str(tmp_path))

    project_path = tmp_path / "new-project"
    project_path.mkdir()

    runner = CliRunner()
    result = runner.invoke(main, ["add-project", "my-project", str(project_path)])

    assert result.exit_code == 0
    assert "Added project 'my-project'" in result.output

    config_file = tmp_path / ".ai-rules-config.yaml"
    assert config_file.exists()

    with open(config_file) as f:
        config_data = yaml.safe_load(f)

    assert "projects" in config_data
    assert "my-project" in config_data["projects"]
    assert config_data["projects"]["my-project"]["path"] == str(project_path)
    assert config_data["projects"]["my-project"]["exclude_symlinks"] == []


@pytest.mark.integration
def test_list_projects_command(tmp_path, monkeypatch):
    """Test list-projects command shows configured projects."""
    monkeypatch.setenv("HOME", str(tmp_path))

    project_path = tmp_path / "test-project"
    project_path.mkdir()

    config_file = tmp_path / ".ai-rules-config.yaml"
    config_data = {
        "version": 1,
        "projects": {
            "test-project": {"path": str(project_path), "exclude_symlinks": []}
        },
    }
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    runner = CliRunner()
    result = runner.invoke(main, ["list-projects"])

    assert result.exit_code == 0
    assert "test-project" in result.output
    assert "Exists" in result.output or "✓" in result.output
