# AGENTS.md

Instructions for AI coding agents working on this repository.

## Project Identity

| Aspect | Value |
|--------|-------|
| **PyPI package** | `ai-agent-rules` |
| **CLI command** | `ai-rules` (preferred) or `ai-agent-rules` |
| **Python module** | `ai_rules` |

The name `ai-rules` was taken on PyPI, so the package is published as `ai-agent-rules`. Both CLI entry points work, but use `ai-rules` in docs and examples (shorter).

## Quick Commands

```bash
just setup                    # First-time setup (deps + git hooks)
just                          # Lint, format, and type check
just test                     # Run tests
just test-fast                # Tests without performance benchmarks (parallel)
just benchmark-compare        # Run and compare performance benchmarks
uv run ai-rules <cmd>         # Run CLI

# GitHub installation
uv run ai-rules setup --github  # Install from GitHub instead of PyPI
```

## Tech Stack

- Python 3.10+ with strict type checking (mypy)
- **uv** for dependency management
- **Click** for CLI framework
- **Rich** for console output
- **pytest** with xdist for parallel testing
- **just** for task automation
- **ruff** for linting and formatting

## Project Structure

```
src/ai_rules/
├── cli.py              # Click CLI commands
├── config.py           # Config loading, path parsing, merging
├── profiles.py         # Profile loading and inheritance resolution
├── state.py            # State management (active profile tracking)
├── utils.py            # Deep merge and utility functions
├── display.py          # Rich console display utilities
├── symlinks.py         # Symlink operations with backups
├── mcp.py              # MCP server management
├── completions.py      # Shell completion management
├── agents/
│   ├── base.py         # Abstract Agent base class
│   ├── claude.py       # ClaudeAgent
│   ├── cursor.py       # CursorAgent
│   ├── goose.py        # GooseAgent
│   └── shared.py       # SharedAgent
├── bootstrap/          # Auto-update and GitHub install utilities
│   ├── installer.py    # Tool installation (PyPI and GitHub)
│   ├── updater.py      # Update checking
│   └── version.py      # Version parsing
└── config/             # Source configs (bundled in package)
    ├── claude/         # Claude Code configs (settings, agents, commands, skills)
    ├── cursor/         # Cursor IDE configs (settings, keybindings)
    ├── goose/          # Goose configs (.goosehints, config.yaml)
    └── profiles/       # Built-in profiles (default.yaml, work.yaml)
tests/
├── unit/               # No filesystem side effects
└── integration/        # Modifies files/symlinks
```

## Key Patterns

### Agent Abstraction
All AI tools inherit from `Agent` (`agents/base.py`). To add a new tool:
1. Create `agents/<tool>.py` inheriting from `Agent`
2. Implement: `name`, `agent_id`, `get_symlinks()`
3. Register in `cli.py::get_agents()`

### Config System
- User config: `~/.ai-rules-config.yaml`
- **State file**: `~/.ai-rules/state.yaml` (tracks active profile, last install time)
- **Profiles**: Named collections of overrides (default, work) with inheritance
  - Built-in: `config/profiles/{default,work}.yaml`
  - User: `~/.ai-rules/profiles/*.yaml`
  - Inheritance via `extends:` key (e.g., work extends default)
  - Commands: `profile list`, `profile show`, `profile current`, `profile switch`
- `settings_overrides` for machine-specific agent settings
- Cache-based override merging for settings.json files (Claude, Cursor, Goose)
- Cursor uses cache for settings.json, direct symlinks for keybindings.json
- Agent-specific hints (CLAUDE.md, .goosehints) use `@~/AGENTS.md` to reference main file (token-saving)

## Testing

```bash
uv run pytest -m unit           # Unit only
uv run pytest -m integration    # Integration only
uv run pytest -m agents         # Agent tests only
uv run pytest -m bootstrap      # Bootstrap tests only
uv run pytest -m completions    # Shell completion tests only
uv run pytest -m config         # Config tests only
uv run pytest -m state          # State management tests only
```

## Code Style

- Run `just` before committing (handles linting, formatting, type checks)
- **pathlib.Path** not string paths
- **rich.console** for CLI output
- **Conventional commits** (`feat:`, `fix:`, `chore:`)
- **ripgrep over grep** - Use `rg` instead of `grep -rn` for searching (10-100x faster on large codebases)

## Common Gotchas

1. **Array path notation** - Setting paths use brackets for arrays: `hooks.SubagentStop[0].command`

2. **Mocking HOME in tests** - Must patch both or tests fail subtly:
   ```python
   monkeypatch.setenv("HOME", str(home))
   monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
   ```

3. **Package index config** - `uvx pip` and `uv tool` use different index configs:
   - `uvx pip` → pip config (PIP_INDEX_URL)
   - `uv tool` → uv config (UV_DEFAULT_INDEX/UV_INDEX_URL)
   - Solution: Pass explicit `--index-url` to pip, `--default-index` to uv

4. **Local testing vs uv tool** - Installing locally doesn't affect the installed tool:
   - `uv pip install -e .` → installs to .venv (use `uv run ai-rules`)
   - `ai-rules` command → runs from uv tool at `~/.local/share/uv/tools/`
   - For local testing: use `uv run ai-rules` or `uv tool install -e . --force`

5. **Package data dotfiles** - Dotfiles require explicit glob pattern:
   - `pyproject.toml`: `ai_rules = ["config/**/*", "config/**/.*"]`
   - Second pattern needed for `.goosehints` and other dotfiles to be included in wheel

6. **GitHub installs** - `setup --github` installs from HEAD of main branch, not tags:
   - Update checks use GitHub API tags
   - Useful for pre-release features before PyPI publish

## Slash Commands & Skills

**Slash commands** (config/claude/commands/):
- `/test-cleanup` - Audit and optimize test suite
- `/comment-cleanup` - Remove unnecessary comments
- `/continue-crash` - Resume after crash
- `/pr-creator` - Create PRs with comprehensive descriptions
- `/dev-docs` - Create/update PLAN.md
- `/update-docs` - Update docs from commits
- `/annotate-changelog` - Annotate changelog entries
- `/agents-md` - Create/update AGENTS.md

**Skills** (config/claude/skills/):
- `doc-writer` - Expert guidance for technical documentation
- `prompt-engineer` - Prompt crafting and LLM optimization

## Key Files by Task

| Task | Files |
|------|-------|
| Add CLI command | `cli.py` |
| Config loading | `config.py` |
| Profile management | `profiles.py`, `state.py`, `cli.py` (profile command) |
| State management | `state.py` (active profile tracking) |
| Symlink behavior | `symlinks.py` |
| Shell completions | `completions.py` |
| New agent | `agents/base.py`, `agents/<new>.py`, `cli.py` |
| MCP management | `mcp.py`, `agents/claude.py` |
| Auto-update/upgrade | `bootstrap/updater.py`, `bootstrap/installer.py` |
| GitHub install support | `bootstrap/installer.py` (GITHUB_REPO_URL) |
