# AI Rules

Manage AI agent configurations through symlinks. Keep all your configs in one git-tracked location.

## Overview

Consolidates config files for AI coding agents (Claude Code, Goose) into a single source of truth via symlinks:

- Git-tracked configs synced across machines
- Edit once, apply everywhere
- Exclude specific files (e.g., company-managed)
- Per-agent customizations

**Supported:** Claude Code (settings, agents, commands), Goose (hints, config)

## Installation

**Requirements:** Python 3.10+, [uv](https://github.com/astral-sh/uv)

```bash
cd ai-rules
uv run ai-rules install  # Run directly (no install needed)
```

## Usage

```bash
ai-rules install                    # Install all agents
ai-rules install --agents claude    # Install specific agents
ai-rules install --dry-run          # Preview changes
ai-rules install --force            # Skip confirmations

ai-rules status                     # Check symlink status (✓✗⚠○)
ai-rules diff                       # Show config differences
ai-rules validate                   # Verify source files exist
ai-rules update                     # Re-sync after adding files
ai-rules uninstall                  # Remove symlinks
ai-rules list-agents                # Show available agents
```

## Configuration

**Exclude symlinks** (company-managed, local-only, machine-specific):

Create `~/.ai-rules-config.yaml`:
```yaml
version: 1
exclude_symlinks:
  - "~/.config/goose/config.yaml"
  - "~/.claude/settings.json"
```

Optional: Add `.ai-rules-config.yaml` in repo for defaults. User config takes precedence.

## Structure

```
config/
├── AGENTS.md              # Shared rules → ~/.AGENTS.md, ~/.CLAUDE.md, ~/.config/goose/.goosehints
├── claude/
│   ├── settings.json      # → ~/.claude/settings.json
│   ├── agents/*.md        # → ~/.claude/agents/*.md (dynamic)
│   └── commands/*.md      # → ~/.claude/commands/*.md (dynamic)
└── goose/
    └── config.yaml        # → ~/.config/goose/config.yaml
```

## Extending

**Add Claude agent/command:**
1. Create `config/claude/agents/my-agent.md` or `config/claude/commands/my-cmd.md`
2. Run `ai-rules update`

**Add new AI tool:**
1. Add configs to `config/<tool>/`
2. Implement `ai_rules/agents/<tool>.py`
3. Register in `ai_rules/cli.py::get_agents()`

## Safety

- First-run warnings
- Timestamped backups (`*.ai-rules-backup.YYYYMMDD-HHMMSS`)
- Interactive prompts and dry-run mode
- Only manages symlinks (never deletes real files)
- Contextual error messages with tips

## Development

### Running Tests
The test suite includes both unit tests and integration tests.

The pytest-cov args are optional, use them to include a test coverage report in the output. To run all tests:

```bash
uv run pytest [--cov=src --cov-report=term-missing]
```

To only run unit tests:
```bash
uv run pytest -m unit
```

To only run integration tests:
```bash
uv run pytest -m integration
```

## Troubleshooting

**Wrong target:** `ai-rules status` then `ai-rules install --force`

**Restore backup:**
```bash
ls -la ~/.CLAUDE.md.ai-rules-backup.*
mv ~/.CLAUDE.md.ai-rules-backup.20250104-143022 ~/.CLAUDE.md
```

**Disable symlink:** Add to `~/.ai-rules-config.yaml` then run `ai-rules update`
```yaml
exclude_symlinks: ["~/.claude/settings.json"]
```

## License

MIT
