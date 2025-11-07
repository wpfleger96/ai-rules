# AI Rules

Manage AI agent configurations through symlinks. Keep all your configs in one git-tracked location.

[![GitHub Contributors](https://img.shields.io/github/contributors/wpfleger96/ai-rules.svg)](https://github.com/wpfleger96/ai-rules/graphs/contributors)
[![License](https://img.shields.io/github/license/wpfleger96/ai-rules.svg)](https://github.com/wpfleger96/ai-rules/blob/main/LICENSE)

## Overview

Consolidates config files for AI coding agents (Claude Code, Goose) into a single source of truth via symlinks:

- Git-tracked configs synced across machines
- Edit once, apply everywhere
- Exclude specific files (e.g., company-managed)
- Per-agent customizations

**Supported:** Claude Code (settings, agents, commands), Goose (hints, config)

## Getting Started

**Requirements:** Python 3.10+, [uv](https://github.com/astral-sh/uv)

1. Clone the repository:
```bash
git clone https://github.com/wpfleger96/ai-rules.git
```

2. Install dependencies:
```bash
cd ai-rules
uv sync
```

## Usage

### User-Level Configuration

```bash
ai-rules install                    # Install all agents (user + projects)
ai-rules install --user-only        # Install only user-level configs
ai-rules install --agents claude    # Install specific agents
ai-rules install --dry-run          # Preview changes
ai-rules install --force            # Skip confirmations

ai-rules status                     # Check symlink status (✓✗⚠○)
ai-rules status --user-only         # Check only user-level configs
ai-rules diff                       # Show config differences
ai-rules validate                   # Verify source files exist
ai-rules update                     # Re-sync after adding files
ai-rules uninstall                  # Remove all symlinks
ai-rules uninstall --user-only      # Remove only user-level symlinks
ai-rules list-agents                # Show available agents
```

### Project-Level Configuration

```bash
ai-rules list-projects              # List configured projects
ai-rules add-project <name> <path>  # Add a project
ai-rules remove-project <name>      # Remove a project

ai-rules install --projects my-api  # Install specific project only
ai-rules status --projects my-api   # Check specific project status
ai-rules uninstall --projects api   # Uninstall specific project
```

## Configuration

### User-Level Config

Create `~/.ai-rules-config.yaml` for user-level settings and project mappings:

```yaml
version: 1

# Global exclusions (apply to all contexts)
exclude_symlinks:
  - "~/.config/goose/config.yaml"
  - "~/.claude/settings.json"

# Project configurations
projects:
  my-api:
    path: ~/Development/work/my-api
    exclude_symlinks:
      - ".goosehints"  # Don't use Goose for this project

  personal-blog:
    path: ~/Projects/personal-blog
    exclude_symlinks: []  # Use all agents

  python-project:
    path: ~/Development/python-ml
    exclude_symlinks:
      - "CLAUDE.md"  # Only use Goose
```

Optional: Add `.ai-rules-config.yaml` in repo for defaults. User config takes precedence.

### Project-Level Rules

1. **Create project config directory:**
   ```bash
   mkdir -p config/projects/my-api
   ```

2. **Add project-specific rules:**
   ```bash
   # Edit config/projects/my-api/AGENTS.md
   # Add project-specific AI agent rules
   ```

3. **Configure and install:**
   ```bash
   ai-rules add-project my-api ~/Development/my-api
   ai-rules install --projects my-api
   ```

The system will create symlinks in your project:
- `<project>/CLAUDE.md` → `config/projects/<name>/AGENTS.md`
- `<project>/.goosehints` → `config/projects/<name>/AGENTS.md`

### Exclusion Behavior

Exclusions are additive:
- **Global exclusions** (root config) apply everywhere (user + all projects)
- **Project exclusions** only apply to that specific project
- A symlink is excluded if it matches *either* global or project exclusions

## Structure

```
config/
├── AGENTS.md              # User-level rules → ~/.CLAUDE.md, ~/.config/goose/.goosehints
├── projects/              # Project-level configurations
│   ├── my-api/
│   │   └── AGENTS.md      # → <project>/CLAUDE.md, <project>/.goosehints
│   └── my-blog/
│       └── AGENTS.md      # → <project>/CLAUDE.md, <project>/.goosehints
├── claude/
│   ├── settings.json      # → ~/.claude/settings.json
│   ├── agents/*.md        # → ~/.claude/agents/*.md (dynamic)
│   └── commands/*.md      # → ~/.claude/commands/*.md (dynamic)
└── goose/
    └── config.yaml        # → ~/.config/goose/config.yaml
```

See [config/projects/README.md](config/projects/README.md) for detailed project configuration guide.

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
