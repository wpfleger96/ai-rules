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
uv run ai-rules <cmd>         # Run CLI
```

## Project Structure

```
src/ai_rules/
├── cli.py              # Click CLI commands
├── config.py           # Config loading, path parsing, merging
├── display.py          # Rich console display utilities
├── symlinks.py         # Symlink operations with backups
├── mcp.py              # MCP server management
├── agents/
│   ├── base.py         # Abstract Agent base class
│   ├── claude.py       # ClaudeAgent
│   ├── goose.py        # GooseAgent
│   └── shared.py       # SharedAgent
├── bootstrap/          # Auto-update utilities
└── config/             # Source configs (bundled in package)
    ├── claude/         # Claude Code configs
    └── goose/          # Goose configs
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
- `settings_overrides` for machine-specific agent settings

## Testing

```bash
uv run pytest -m unit           # Unit only
uv run pytest -m integration    # Integration only
```

## Code Style

- Run `just` before committing (handles linting, formatting, type checks)
- **pathlib.Path** not string paths
- **rich.console** for CLI output
- **Conventional commits** (`feat:`, `fix:`, `chore:`)

## Common Gotchas

1. **Array path notation** - Setting paths use brackets for arrays: `hooks.SubagentStop[0].command`

2. **Mocking HOME in tests** - Must patch both or tests fail subtly:
   ```python
   monkeypatch.setenv("HOME", str(home))
   monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
   ```

## Key Files by Task

| Task | Files |
|------|-------|
| Add CLI command | `cli.py` |
| Config loading | `config.py` |
| Symlink behavior | `symlinks.py` |
| New agent | `agents/base.py`, `agents/<new>.py`, `cli.py` |
| MCP management | `mcp.py`, `agents/claude.py` |
