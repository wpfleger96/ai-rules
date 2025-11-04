from pathlib import Path

import pytest

from ai_rules.symlinks import (
    SymlinkResult,
    check_symlink,
    create_backup_path,
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

    def test_handles_missing_target_gracefully(self, tmp_path):
        target = tmp_path / "nonexistent.txt"

        success, message = remove_symlink(target, force=True)

        assert success is False

    def test_removes_broken_symlink(self, tmp_path):
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        target.symlink_to(source)

        success, message = remove_symlink(target, force=True)

        assert success is True
        assert not target.exists()

    def test_force_mode_still_protects_real_files(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("important data")

        success, message = remove_symlink(target, force=True)

        assert success is False
        assert target.exists()
        assert target.read_text() == "important data"


@pytest.mark.unit
class TestCreateBackupPath:
    """Test backup path generation."""

    def test_generates_timestamped_backup_path(self, tmp_path):
        target = tmp_path / "test.txt"

        backup = create_backup_path(target)

        assert backup.parent == target.parent
        assert backup.name.startswith("test.txt.ai-rules-backup.")
        assert len(backup.name) > len("test.txt.ai-rules-backup.")
