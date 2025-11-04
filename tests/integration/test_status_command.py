from pathlib import Path

import pytest

from ai_rules.agents.claude import ClaudeAgent
from ai_rules.agents.goose import GooseAgent
from ai_rules.config import Config
from ai_rules.symlinks import check_symlink, create_symlink


@pytest.mark.integration
class TestStatusValidation:
    """Test status command accuracy for symlink health checks."""

    def test_status_identifies_all_correct_symlinks(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)

        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            create_symlink(target_path, source, force=False, dry_run=False)

        all_correct = True
        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            status, message = check_symlink(target_path, source)
            if status != "correct":
                all_correct = False
                break

        assert all_correct

    def test_status_identifies_missing_symlinks(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)

        issues = []
        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            status, message = check_symlink(target_path, source)
            if status != "correct":
                issues.append((str(target), status))

        assert len(issues) > 0
        assert all(status == "missing" for _, status in issues)

    def test_status_identifies_broken_symlinks(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        target, source = claude.get_symlinks()[0]
        target_path = Path(str(target).replace("~", str(mock_home)))

        target_path.parent.mkdir(parents=True, exist_ok=True)
        nonexistent = mock_home / "nonexistent.md"
        target_path.symlink_to(nonexistent)

        status, message = check_symlink(target_path, source)

        assert status in ["broken", "wrong_target"]

    def test_status_identifies_wrong_target_symlinks(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        target, source = claude.get_symlinks()[0]
        target_path = Path(str(target).replace("~", str(mock_home)))

        wrong_file = test_repo / "wrong.txt"
        wrong_file.write_text("wrong")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.symlink_to(wrong_file)

        status, message = check_symlink(target_path, source)

        assert status == "wrong_target"

    def test_status_identifies_regular_files_instead_of_symlinks(
        self, test_repo, mock_home
    ):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        target, source = claude.get_symlinks()[0]
        target_path = Path(str(target).replace("~", str(mock_home)))

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("not a symlink")

        status, message = check_symlink(target_path, source)

        assert status == "not_symlink"

    def test_status_should_return_error_code_when_issues_found(
        self, test_repo, mock_home
    ):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)

        has_issues = False
        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            status, message = check_symlink(target_path, source)
            if status != "correct":
                has_issues = True
                break

        assert has_issues

    def test_status_should_return_success_when_all_correct(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)

        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            create_symlink(target_path, source, force=False, dry_run=False)

        all_correct = True
        for target, source in claude.get_symlinks():
            target_path = Path(str(target).replace("~", str(mock_home)))
            status, message = check_symlink(target_path, source)
            if status != "correct":
                all_correct = False
                break

        assert all_correct

    def test_status_handles_mixed_symlink_states(self, test_repo, mock_home):
        config = Config(exclude_symlinks=[])
        claude = ClaudeAgent(test_repo, config)
        symlinks = claude.get_symlinks()

        target1, source1 = symlinks[0]
        target1_path = Path(str(target1).replace("~", str(mock_home)))
        create_symlink(target1_path, source1, force=False, dry_run=False)

        target2, source2 = symlinks[1]
        target2_path = Path(str(target2).replace("~", str(mock_home)))

        target3, source3 = symlinks[2]
        target3_path = Path(str(target3).replace("~", str(mock_home)))
        target3_path.parent.mkdir(parents=True, exist_ok=True)
        target3_path.write_text("regular file")

        statuses = {}
        for target, source in [
            (target1, source1),
            (target2, source2),
            (target3, source3),
        ]:
            target_path = Path(str(target).replace("~", str(mock_home)))
            status, message = check_symlink(target_path, source)
            statuses[str(target)] = status

        assert statuses[str(target1)] == "correct"
        assert statuses[str(target2)] == "missing"
        assert statuses[str(target3)] == "not_symlink"
