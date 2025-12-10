"""Integration tests for profile CLI commands."""

import pytest

from click.testing import CliRunner

from ai_rules.cli import main


@pytest.fixture
def runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.mark.integration
class TestInstallWithProfile:
    """Tests for install command with --profile option."""

    def test_install_with_nonexistent_profile_fails(self, runner):
        """Test that using non-existent profile shows error."""
        result = runner.invoke(
            main, ["install", "--profile", "nonexistent", "--dry-run"]
        )

        assert result.exit_code == 1
        assert "not found" in result.output


@pytest.mark.integration
class TestProfileListCommand:
    """Tests for profile list command."""

    def test_profile_list_shows_default(self, runner):
        """Test that default profile is always listed."""
        result = runner.invoke(main, ["profile", "list"])

        assert result.exit_code == 0
        assert "default" in result.output


@pytest.mark.integration
class TestProfileShowCommand:
    """Tests for profile show command."""

    def test_profile_show_default(self, runner):
        """Test showing default profile."""
        result = runner.invoke(main, ["profile", "show", "default"])

        assert result.exit_code == 0
        assert "default" in result.output

    def test_profile_show_resolved_displays_inheritance(self, runner):
        """Test showing resolved profile with inheritance."""
        result = runner.invoke(main, ["profile", "show", "work", "--resolved"])

        assert result.exit_code == 0
        assert "work" in result.output
        assert "resolved" in result.output

    def test_profile_show_nonexistent_shows_error(self, runner):
        """Test that showing non-existent profile shows error."""
        result = runner.invoke(main, ["profile", "show", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
