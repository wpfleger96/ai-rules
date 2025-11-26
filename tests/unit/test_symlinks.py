from pathlib import Path

import pytest

from ai_rules.agents.claude import ClaudeAgent
from ai_rules.cli import cleanup_deprecated_symlinks
from ai_rules.config import Config
from ai_rules.symlinks import (
    SymlinkResult,
    check_symlink,
    create_symlink,
    remove_symlink,
)


@pytest.mark.unit
class TestCreateSymlink:
    """Test symlink creation with critical safety and correctness scenarios."""

    def test_creates_new_symlink_successfully(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test content")
        target = tmp_path / "target.txt"

        result, message = create_symlink(target, source, force=False, dry_run=False)

        assert result == SymlinkResult.CREATED
        assert target.is_symlink()
        assert target.resolve() == source.resolve()

    def test_handles_existing_correct_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test content")
        target = tmp_path / "target.txt"
        target.symlink_to(source)

        result, message = create_symlink(target, source, force=False, dry_run=False)

        assert result == SymlinkResult.ALREADY_CORRECT
        assert target.is_symlink()
        assert target.resolve() == source.resolve()

    def test_creates_backup_when_replacing_existing_file(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("source content")
        target = tmp_path / "target.txt"
        target.write_text("original content")

        result, message = create_symlink(target, source, force=True, dry_run=False)

        assert result == SymlinkResult.CREATED
        assert target.is_symlink()
        backup_files = list(tmp_path.glob("target.txt.ai-rules-backup.*"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == "original content"

    def test_updates_wrong_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("source content")
        wrong_source = tmp_path / "wrong.txt"
        wrong_source.write_text("wrong content")
        target = tmp_path / "target.txt"
        target.symlink_to(wrong_source)

        result, message = create_symlink(target, source, force=True, dry_run=False)

        assert result == SymlinkResult.CREATED
        assert target.is_symlink()
        assert target.resolve() == source.resolve()

    def test_dry_run_does_not_modify_filesystem(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test content")
        target = tmp_path / "target.txt"

        result, message = create_symlink(target, source, force=False, dry_run=True)

        assert result == SymlinkResult.CREATED
        assert not target.exists()

    def test_dry_run_with_existing_file_no_backup(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("source content")
        target = tmp_path / "target.txt"
        target.write_text("original content")

        result, message = create_symlink(target, source, force=True, dry_run=True)

        assert result == SymlinkResult.CREATED
        assert target.read_text() == "original content"
        backup_files = list(tmp_path.glob("target.txt.ai-rules-backup.*"))
        assert len(backup_files) == 0

    def test_fails_when_source_does_not_exist(self, tmp_path):
        source = tmp_path / "nonexistent.txt"
        target = tmp_path / "target.txt"

        result, message = create_symlink(target, source, force=False, dry_run=False)

        assert result == SymlinkResult.ERROR
        assert not target.exists()
        assert "does not exist" in message.lower()

    def test_creates_parent_directories_for_target(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test content")
        target = tmp_path / "nested" / "dir" / "target.txt"

        result, message = create_symlink(target, source, force=False, dry_run=False)

        assert result == SymlinkResult.CREATED
        assert target.is_symlink()
        assert target.parent.exists()


@pytest.mark.unit
class TestCheckSymlink:
    """Test symlink status detection."""

    def test_detects_correct_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test")
        target = tmp_path / "target.txt"
        target.symlink_to(source)

        status, message = check_symlink(target, source)

        assert status == "correct"

    def test_detects_missing_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test")
        target = tmp_path / "target.txt"

        status, message = check_symlink(target, source)

        assert status == "missing"

    def test_detects_broken_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test")
        nonexistent = tmp_path / "nonexistent.txt"
        target = tmp_path / "target.txt"
        target.symlink_to(nonexistent)

        status, message = check_symlink(target, source)

        assert status in ["broken", "wrong_target"]

    def test_detects_wrong_target(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test")
        wrong = tmp_path / "wrong.txt"
        wrong.write_text("wrong")
        target = tmp_path / "target.txt"
        target.symlink_to(wrong)

        status, message = check_symlink(target, source)

        assert status == "wrong_target"

    def test_detects_regular_file_instead_of_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test")
        target = tmp_path / "target.txt"
        target.write_text("not a symlink")

        status, message = check_symlink(target, source)

        assert status == "not_symlink"


@pytest.mark.unit
class TestRemoveSymlink:
    """Test symlink removal safety mechanisms."""

    def test_removes_valid_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("test")
        target = tmp_path / "target.txt"
        target.symlink_to(source)

        success, message = remove_symlink(target, force=True)

        assert success is True
        assert not target.exists()
        assert source.exists()

    def test_never_removes_regular_files(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("important data")

        success, message = remove_symlink(target, force=True)

        assert success is False
        assert target.exists()
        assert target.read_text() == "important data"
        assert "not a symlink" in message.lower()

    def test_removes_broken_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        target.symlink_to(source)

        success, message = remove_symlink(target, force=True)

        assert success is True
        assert not target.exists()


@pytest.mark.unit
class TestCleanupDeprecatedSymlinks:
    """Test deprecated symlink cleanup with safety checks."""

    def test_removes_deprecated_symlink_pointing_to_our_file(
        self, test_repo, tmp_path, monkeypatch
    ):
        """Test that deprecated symlinks pointing to our AGENTS.md are removed."""
        # Set up: create AGENTS.md in config
        agents_md = test_repo / "config" / "AGENTS.md"
        agents_md.parent.mkdir(parents=True, exist_ok=True)
        agents_md.write_text("# Test Agents")

        # Create deprecated symlink at ~/CLAUDE.md pointing to our AGENTS.md
        deprecated_path = tmp_path / "CLAUDE.md"
        deprecated_path.symlink_to(agents_md)

        # Mock expanduser to use tmp_path instead of actual home
        def mock_expanduser(self):
            if str(self) == "~/CLAUDE.md":
                return deprecated_path
            return Path(str(self).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", mock_expanduser)

        # Create agent and run cleanup
        config = Config(exclude_symlinks=[])
        agent = ClaudeAgent(test_repo, config)
        removed = cleanup_deprecated_symlinks(
            [agent], test_repo / "config", force=True, dry_run=False
        )

        # Verify symlink was removed
        assert removed == 1
        assert not deprecated_path.exists()

    def test_does_not_remove_regular_file_at_deprecated_location(
        self, test_repo, tmp_path, monkeypatch
    ):
        """Test that regular files at deprecated locations are NOT removed."""
        # Set up: create AGENTS.md in config
        agents_md = test_repo / "config" / "AGENTS.md"
        agents_md.parent.mkdir(parents=True, exist_ok=True)
        agents_md.write_text("# Test Agents")

        # Create regular file (not symlink) at deprecated location
        deprecated_path = tmp_path / "CLAUDE.md"
        deprecated_path.write_text("# User's own file")

        # Mock expanduser
        def mock_expanduser(self):
            if str(self) == "~/CLAUDE.md":
                return deprecated_path
            return Path(str(self).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", mock_expanduser)

        # Create agent and run cleanup
        config = Config(exclude_symlinks=[])
        agent = ClaudeAgent(test_repo, config)
        removed = cleanup_deprecated_symlinks(
            [agent], test_repo / "config", force=True, dry_run=False
        )

        # Verify file was NOT removed
        assert removed == 0
        assert deprecated_path.exists()
        assert deprecated_path.read_text() == "# User's own file"

    def test_does_not_remove_symlink_pointing_elsewhere(
        self, test_repo, tmp_path, monkeypatch
    ):
        """Test that symlinks pointing to other files are NOT removed."""
        # Set up: create AGENTS.md in config
        agents_md = test_repo / "config" / "AGENTS.md"
        agents_md.parent.mkdir(parents=True, exist_ok=True)
        agents_md.write_text("# Test Agents")

        # Create different file and symlink to it
        other_file = tmp_path / "other.md"
        other_file.write_text("# Other file")
        deprecated_path = tmp_path / "CLAUDE.md"
        deprecated_path.symlink_to(other_file)

        # Mock expanduser
        def mock_expanduser(self):
            if str(self) == "~/CLAUDE.md":
                return deprecated_path
            return Path(str(self).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", mock_expanduser)

        # Create agent and run cleanup
        config = Config(exclude_symlinks=[])
        agent = ClaudeAgent(test_repo, config)
        removed = cleanup_deprecated_symlinks(
            [agent], test_repo / "config", force=True, dry_run=False
        )

        # Verify symlink was NOT removed
        assert removed == 0
        assert deprecated_path.exists()
        assert deprecated_path.is_symlink()

    def test_dry_run_does_not_remove_symlinks(self, test_repo, tmp_path, monkeypatch):
        """Test that dry run doesn't actually remove symlinks."""
        # Set up: create AGENTS.md in config
        agents_md = test_repo / "config" / "AGENTS.md"
        agents_md.parent.mkdir(parents=True, exist_ok=True)
        agents_md.write_text("# Test Agents")

        # Create deprecated symlink
        deprecated_path = tmp_path / "CLAUDE.md"
        deprecated_path.symlink_to(agents_md)

        # Mock expanduser
        def mock_expanduser(self):
            if str(self) == "~/CLAUDE.md":
                return deprecated_path
            return Path(str(self).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", mock_expanduser)

        # Create agent and run cleanup in dry run mode
        config = Config(exclude_symlinks=[])
        agent = ClaudeAgent(test_repo, config)
        removed = cleanup_deprecated_symlinks(
            [agent], test_repo / "config", force=True, dry_run=True
        )

        # Verify count is correct but symlink still exists
        assert removed == 1
        assert deprecated_path.exists()
