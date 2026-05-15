"""LSP language-to-plugin registry for Claude Code."""

from __future__ import annotations

import shutil

from dataclasses import dataclass


@dataclass(frozen=True)
class LspLanguage:
    """LSP language server configuration."""

    plugin: str
    marketplace: str
    binary: str
    install_hint: str


LSP_REGISTRY: dict[str, LspLanguage] = {
    "python": LspLanguage(
        plugin="pyright-lsp",
        marketplace="cc-marketplace",
        binary="pyright-langserver",
        install_hint="npm install -g pyright",
    ),
    "typescript": LspLanguage(
        plugin="typescript-lsp",
        marketplace="cc-marketplace",
        binary="typescript-language-server",
        install_hint="npm install -g typescript-language-server typescript",
    ),
    "rust": LspLanguage(
        plugin="rust-analyzer-lsp",
        marketplace="cc-marketplace",
        binary="rust-analyzer",
        install_hint="rustup component add rust-analyzer",
    ),
    "go": LspLanguage(
        plugin="gopls-lsp",
        marketplace="claude-code-lsps",
        binary="gopls",
        install_hint="go install golang.org/x/tools/gopls@latest",
    ),
    "java": LspLanguage(
        plugin="jdtls-lsp",
        marketplace="claude-code-lsps",
        binary="jdtls",
        install_hint="brew install jdtls",
    ),
    "c": LspLanguage(
        plugin="clangd-lsp",
        marketplace="claude-code-lsps",
        binary="clangd",
        install_hint="brew install llvm",
    ),
    "cpp": LspLanguage(
        plugin="clangd-lsp",
        marketplace="claude-code-lsps",
        binary="clangd",
        install_hint="brew install llvm",
    ),
    "csharp": LspLanguage(
        plugin="omnisharp-lsp",
        marketplace="claude-code-lsps",
        binary="OmniSharp",
        install_hint="dotnet tool install -g omnisharp",
    ),
    "ruby": LspLanguage(
        plugin="solargraph-lsp",
        marketplace="claude-code-lsps",
        binary="solargraph",
        install_hint="gem install solargraph",
    ),
    "php": LspLanguage(
        plugin="intelephense-lsp",
        marketplace="claude-code-lsps",
        binary="intelephense",
        install_hint="npm install -g intelephense",
    ),
    "kotlin": LspLanguage(
        plugin="kotlin-lsp",
        marketplace="claude-code-lsps",
        binary="kotlin-language-server",
        install_hint="brew install kotlin-language-server",
    ),
}

MARKETPLACE_SOURCES: dict[str, str] = {
    "cc-marketplace": "ananddtyagi/cc-marketplace",
    "claude-code-lsps": "Piebald-AI/claude-code-lsps",
}


def get_supported_languages() -> list[str]:
    """Return sorted list of supported language names."""
    return sorted(LSP_REGISTRY.keys())


def resolve_languages(
    languages: list[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Resolve language names into plugin and marketplace configs.

    Returns:
        Tuple of (plugin_dicts, marketplace_dicts) ready to merge into profile config.

    Raises:
        ValueError: If any language name is not in the registry.
    """
    plugins: dict[str, dict[str, str]] = {}
    marketplaces: dict[str, dict[str, str]] = {}

    for lang in languages:
        if lang not in LSP_REGISTRY:
            supported = ", ".join(get_supported_languages())
            raise ValueError(f"Unknown LSP language '{lang}'. Supported: {supported}")

        entry = LSP_REGISTRY[lang]
        plugin_key = entry.plugin
        if plugin_key not in plugins:
            plugins[plugin_key] = {
                "name": entry.plugin,
                "marketplace": entry.marketplace,
            }

        if entry.marketplace not in marketplaces:
            if entry.marketplace not in MARKETPLACE_SOURCES:
                raise ValueError(
                    f"Registry entry for '{lang}' references unknown marketplace "
                    f"'{entry.marketplace}'. Add it to MARKETPLACE_SOURCES."
                )
            marketplaces[entry.marketplace] = {
                "name": entry.marketplace,
                "source": MARKETPLACE_SOURCES[entry.marketplace],
            }

    return list(plugins.values()), list(marketplaces.values())


def check_binaries(languages: list[str]) -> list[tuple[str, str, str | None]]:
    """Check if LSP server binaries are available in PATH.

    Returns:
        List of (language, binary_name, path_or_none) tuples.
    """
    results = []
    seen_binaries: set[str] = set()

    for lang in languages:
        entry = LSP_REGISTRY.get(lang)
        if not entry or entry.binary in seen_binaries:
            continue

        seen_binaries.add(entry.binary)
        path = shutil.which(entry.binary)
        results.append((lang, entry.binary, path))

    return results
