import os

from unittest.mock import patch

import pytest

from ai_rules.completions import (
    COMPLETION_MARKER_END,
    COMPLETION_MARKER_START,
    detect_shell,
    find_config_file,
    generate_completion_script,
    get_shell_config_candidates,
    install_completion,
    is_completion_installed,
    uninstall_completion,
)


@pytest.mark.unit
@pytest.mark.completions
class TestDetectShell:
    """Test shell detection from environment."""

    def test_detect_bash(self):
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert detect_shell() == "bash"

    def test_detect_zsh(self):
        with patch.dict(os.environ, {"SHELL": "/usr/bin/zsh"}):
            assert detect_shell() == "zsh"

    def test_unsupported_shell(self):
        with patch.dict(os.environ, {"SHELL": "/bin/fish"}):
            assert detect_shell() is None

    def test_no_shell_env(self):
        with patch.dict(os.environ, {}, clear=True):
            assert detect_shell() is None


@pytest.mark.unit
@pytest.mark.completions
class TestGetShellConfigCandidates:
    """Test finding shell config file candidates."""

    def test_bash_candidates(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        bashrc = home / ".bashrc"
        bashrc.write_text("# bashrc")

        with patch("ai_rules.completions.Path.home", return_value=home):
            candidates = get_shell_config_candidates("bash")
            assert len(candidates) == 1
            assert candidates[0] == bashrc

    def test_zsh_candidates(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        zshrc = home / ".zshrc"
        zshrc.write_text("# zshrc")

        with patch("ai_rules.completions.Path.home", return_value=home):
            candidates = get_shell_config_candidates("zsh")
            assert len(candidates) == 1
            assert candidates[0] == zshrc

    def test_multiple_candidates(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        bashrc = home / ".bashrc"
        bash_profile = home / ".bash_profile"
        bashrc.write_text("# bashrc")
        bash_profile.write_text("# bash_profile")

        with patch("ai_rules.completions.Path.home", return_value=home):
            candidates = get_shell_config_candidates("bash")
            assert len(candidates) == 2
            assert bashrc in candidates
            assert bash_profile in candidates

    def test_no_existing_files(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        with patch("ai_rules.completions.Path.home", return_value=home):
            candidates = get_shell_config_candidates("bash")
            assert len(candidates) == 0


@pytest.mark.unit
@pytest.mark.completions
class TestFindConfigFile:
    """Test finding the appropriate config file."""

    def test_finds_first_existing(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        bashrc = home / ".bashrc"
        bashrc.write_text("# bashrc")

        with patch("ai_rules.completions.Path.home", return_value=home):
            config_file = find_config_file("bash")
            assert config_file == bashrc

    def test_returns_none_if_no_candidates(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        with patch("ai_rules.completions.Path.home", return_value=home):
            config_file = find_config_file("bash")
            assert config_file is None


@pytest.mark.unit
@pytest.mark.completions
class TestIsCompletionInstalled:
    """Test checking if completion is installed."""

    def test_not_installed(self, tmp_path):
        config_file = tmp_path / ".bashrc"
        config_file.write_text("# Some config\n")

        assert is_completion_installed(config_file) is False

    def test_installed(self, tmp_path):
        config_file = tmp_path / ".bashrc"
        config_file.write_text(
            f"# Some config\n{COMPLETION_MARKER_START}\neval something\n{COMPLETION_MARKER_END}\n"
        )

        assert is_completion_installed(config_file) is True

    def test_file_not_exists(self, tmp_path):
        config_file = tmp_path / ".bashrc"
        assert is_completion_installed(config_file) is False


@pytest.mark.unit
@pytest.mark.completions
class TestGenerateCompletionScript:
    """Test completion script generation."""

    def test_generates_bash_script(self):
        script = generate_completion_script("bash")

        assert COMPLETION_MARKER_START in script
        assert COMPLETION_MARKER_END in script
        assert "_AI_RULES_COMPLETE=bash_source ai-rules" in script

    def test_generates_zsh_script(self):
        script = generate_completion_script("zsh")

        assert COMPLETION_MARKER_START in script
        assert COMPLETION_MARKER_END in script
        assert "_AI_RULES_COMPLETE=zsh_source ai-rules" in script

    def test_unsupported_shell_raises_error(self):
        with pytest.raises(ValueError, match="Unsupported shell"):
            generate_completion_script("ksh")


@pytest.mark.unit
@pytest.mark.completions
class TestInstallCompletion:
    """Test completion installation."""

    def test_install_bash(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        bashrc = home / ".bashrc"
        bashrc.write_text("# bashrc\n")

        with patch("ai_rules.completions.Path.home", return_value=home):
            success, message = install_completion("bash", dry_run=False)

            assert success is True
            assert "Completion installed" in message
            content = bashrc.read_text()
            assert COMPLETION_MARKER_START in content
            assert "_AI_RULES_COMPLETE=bash_source ai-rules" in content

    def test_install_dry_run(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        bashrc = home / ".bashrc"
        bashrc.write_text("# bashrc\n")

        with patch("ai_rules.completions.Path.home", return_value=home):
            success, message = install_completion("bash", dry_run=True)

            assert success is True
            assert "Would append" in message
            content = bashrc.read_text()
            assert COMPLETION_MARKER_START not in content

    def test_install_already_installed(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        bashrc = home / ".bashrc"
        bashrc.write_text(
            f"# bashrc\n{COMPLETION_MARKER_START}\neval something\n{COMPLETION_MARKER_END}\n"
        )

        with patch("ai_rules.completions.Path.home", return_value=home):
            success, message = install_completion("bash", dry_run=False)

            assert success is True
            assert "already installed" in message

    def test_install_no_config_file(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()

        with patch("ai_rules.completions.Path.home", return_value=home):
            success, message = install_completion("bash", dry_run=False)

            assert success is False
            assert "No bash config file found" in message

    def test_install_unsupported_shell(self):
        success, message = install_completion("ksh", dry_run=False)

        assert success is False
        assert "Unsupported shell" in message


@pytest.mark.unit
@pytest.mark.completions
class TestUninstallCompletion:
    """Test completion uninstallation."""

    def test_uninstall(self, tmp_path):
        config_file = tmp_path / ".bashrc"
        config_file.write_text(
            f"# before\n{COMPLETION_MARKER_START}\neval something\n{COMPLETION_MARKER_END}\n# after\n"
        )

        success, message = uninstall_completion(config_file)

        assert success is True
        assert "Completion removed" in message
        content = config_file.read_text()
        assert COMPLETION_MARKER_START not in content
        assert "# before\n" in content
        assert "# after\n" in content

    def test_uninstall_not_installed(self, tmp_path):
        config_file = tmp_path / ".bashrc"
        config_file.write_text("# bashrc\n")

        success, message = uninstall_completion(config_file)

        assert success is True
        assert "not installed" in message

    def test_uninstall_file_not_exists(self, tmp_path):
        config_file = tmp_path / ".bashrc"

        success, message = uninstall_completion(config_file)

        assert success is False
        assert "not found" in message
