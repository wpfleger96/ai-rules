"""Tests for version utilities."""

import pytest

from packaging.version import InvalidVersion

from ai_rules.bootstrap.version import get_package_version, is_newer, parse_version


@pytest.mark.unit
@pytest.mark.bootstrap
class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_version_without_v_prefix(self):
        """Test parsing version without 'v' prefix."""
        version = parse_version("1.2.3")
        assert str(version) == "1.2.3"

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        version = parse_version("v1.2.3")
        assert str(version) == "1.2.3"

    def test_parse_version_with_prerelease(self):
        """Test parsing version with prerelease tag."""
        version = parse_version("v1.2.3-alpha.1")
        assert str(version) == "1.2.3a1"

    def test_parse_version_with_build_metadata(self):
        """Test parsing version with build metadata."""
        version = parse_version("1.2.3+build.123")
        assert "1.2.3" in str(version)

    def test_parse_version_invalid_raises_error(self):
        """Test that invalid version strings raise InvalidVersion."""
        with pytest.raises(InvalidVersion):
            parse_version("not.a.version")

    def test_parse_version_empty_string_raises_error(self):
        """Test that empty string raises InvalidVersion."""
        with pytest.raises(InvalidVersion):
            parse_version("")


@pytest.mark.unit
@pytest.mark.bootstrap
class TestIsNewer:
    """Tests for is_newer function."""

    def test_newer_version_returns_true(self):
        """Test that newer version is detected."""
        assert is_newer("1.2.0", "1.1.0") is True

    def test_older_version_returns_false(self):
        """Test that older version is not considered newer."""
        assert is_newer("1.1.0", "1.2.0") is False

    def test_same_version_returns_false(self):
        """Test that same version is not considered newer."""
        assert is_newer("1.2.0", "1.2.0") is False

    def test_major_version_bump(self):
        """Test detection of major version bump."""
        assert is_newer("2.0.0", "1.9.9") is True

    def test_minor_version_bump(self):
        """Test detection of minor version bump."""
        assert is_newer("1.3.0", "1.2.9") is True

    def test_patch_version_bump(self):
        """Test detection of patch version bump."""
        assert is_newer("1.2.4", "1.2.3") is True

    def test_with_v_prefix_both_versions(self):
        """Test comparison with 'v' prefix on both versions."""
        assert is_newer("v1.2.0", "v1.1.0") is True

    def test_with_v_prefix_one_version(self):
        """Test comparison with 'v' prefix on one version."""
        assert is_newer("v1.2.0", "1.1.0") is True
        assert is_newer("1.2.0", "v1.1.0") is True

    def test_prerelease_versions(self):
        """Test comparison of prerelease versions."""
        assert is_newer("1.2.0", "1.2.0-alpha.1") is True
        assert is_newer("1.2.0-beta.1", "1.2.0-alpha.1") is True

    def test_invalid_latest_version_returns_false(self):
        """Test that invalid latest version returns False."""
        assert is_newer("invalid", "1.2.0") is False

    def test_invalid_current_version_returns_false(self):
        """Test that invalid current version returns False."""
        assert is_newer("1.2.0", "invalid") is False

    def test_both_invalid_versions_returns_false(self):
        """Test that both invalid versions returns False."""
        assert is_newer("invalid", "also-invalid") is False


@pytest.mark.unit
@pytest.mark.bootstrap
class TestGetPackageVersion:
    """Tests for get_package_version function."""

    def test_get_version_for_installed_package(self, monkeypatch):
        """Test getting version for installed package."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.version.get_version", lambda pkg: "1.2.3"
        )
        version = get_package_version("ai-rules")
        assert version == "1.2.3"

    def test_get_version_with_custom_package_name(self, monkeypatch):
        """Test getting version with custom package name."""
        monkeypatch.setattr(
            "ai_rules.bootstrap.version.get_version", lambda pkg: "2.0.0"
        )
        version = get_package_version("custom-package")
        assert version == "2.0.0"

    def test_get_version_package_not_found_raises_error(self, monkeypatch):
        """Test that PackageNotFoundError is raised for missing package."""
        from importlib.metadata import PackageNotFoundError

        def mock_get_version(pkg):
            raise PackageNotFoundError("package-not-found")

        monkeypatch.setattr("ai_rules.bootstrap.version.get_version", mock_get_version)
        with pytest.raises(PackageNotFoundError):
            get_package_version("nonexistent-package")
