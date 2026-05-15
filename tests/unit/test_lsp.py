"""Unit tests for LSP registry and language resolution."""

from unittest.mock import patch

import pytest

from ai_rules.lsp import (
    LSP_REGISTRY,
    check_binaries,
    get_supported_languages,
    resolve_languages,
)


@pytest.mark.unit
class TestLspRegistry:
    def test_registry_contains_core_languages(self):
        assert "python" in LSP_REGISTRY
        assert "typescript" in LSP_REGISTRY
        assert "rust" in LSP_REGISTRY
        assert "go" in LSP_REGISTRY

    def test_registry_entries_are_complete(self):
        for lang, entry in LSP_REGISTRY.items():
            assert entry.plugin, f"{lang}: missing plugin"
            assert entry.marketplace, f"{lang}: missing marketplace"
            assert entry.binary, f"{lang}: missing binary"
            assert entry.install_hint, f"{lang}: missing install_hint"

    def test_c_and_cpp_share_clangd(self):
        assert LSP_REGISTRY["c"].plugin == LSP_REGISTRY["cpp"].plugin
        assert LSP_REGISTRY["c"].binary == LSP_REGISTRY["cpp"].binary

    def test_get_supported_languages_sorted(self):
        languages = get_supported_languages()
        assert languages == sorted(languages)
        assert len(languages) == len(LSP_REGISTRY)


@pytest.mark.unit
class TestResolveLanguages:
    def test_resolve_single_official_language(self):
        plugins, marketplaces = resolve_languages(["python"])

        assert len(plugins) == 1
        assert plugins[0]["name"] == "pyright-lsp"
        assert plugins[0]["marketplace"] == "cc-marketplace"

        assert len(marketplaces) == 1
        assert marketplaces[0]["name"] == "cc-marketplace"

    def test_resolve_community_language(self):
        plugins, marketplaces = resolve_languages(["go"])

        assert len(plugins) == 1
        assert plugins[0]["name"] == "gopls-lsp"
        assert plugins[0]["marketplace"] == "claude-code-lsps"

        marketplace_names = {m["name"] for m in marketplaces}
        assert "claude-code-lsps" in marketplace_names

    def test_resolve_multiple_languages(self):
        plugins, marketplaces = resolve_languages(["python", "typescript", "go"])

        assert len(plugins) == 3
        plugin_names = {p["name"] for p in plugins}
        assert plugin_names == {"pyright-lsp", "typescript-lsp", "gopls-lsp"}

        marketplace_names = {m["name"] for m in marketplaces}
        assert "cc-marketplace" in marketplace_names
        assert "claude-code-lsps" in marketplace_names

    def test_resolve_deduplicates_shared_plugin(self):
        plugins, _ = resolve_languages(["c", "cpp"])

        assert len(plugins) == 1
        assert plugins[0]["name"] == "clangd-lsp"

    def test_resolve_unknown_language_raises(self):
        with pytest.raises(ValueError, match="Unknown LSP language 'fortran'"):
            resolve_languages(["fortran"])

    def test_resolve_empty_list(self):
        plugins, marketplaces = resolve_languages([])
        assert plugins == []
        assert marketplaces == []


@pytest.mark.unit
class TestCheckBinaries:
    @patch("ai_rules.lsp.shutil.which")
    def test_binary_found(self, mock_which):
        mock_which.return_value = "/usr/local/bin/pyright-langserver"

        results = check_binaries(["python"])

        assert len(results) == 1
        lang, binary, path = results[0]
        assert lang == "python"
        assert binary == "pyright-langserver"
        assert path == "/usr/local/bin/pyright-langserver"

    @patch("ai_rules.lsp.shutil.which")
    def test_binary_not_found(self, mock_which):
        mock_which.return_value = None

        results = check_binaries(["python"])

        assert len(results) == 1
        assert results[0][2] is None

    @patch("ai_rules.lsp.shutil.which")
    def test_deduplicates_shared_binary(self, mock_which):
        mock_which.return_value = "/usr/bin/clangd"

        results = check_binaries(["c", "cpp"])

        assert len(results) == 1
        assert results[0][1] == "clangd"

    def test_unknown_language_skipped(self):
        results = check_binaries(["nonexistent"])
        assert results == []
