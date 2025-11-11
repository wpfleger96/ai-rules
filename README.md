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

**Supported:** Claude Code (settings, agents, commands), Goose (hints, config), Shared (AGENTS.md)

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
ai-rules install --rebuild-cache    # Rebuild merged settings cache

ai-rules status                     # Check symlink status (✓✗⚠○)
ai-rules status --user-only         # Check only user-level configs
ai-rules diff                       # Show config differences
ai-rules validate                   # Verify source files exist
ai-rules update                     # Re-sync after adding files
ai-rules uninstall                  # Remove all symlinks
ai-rules uninstall --user-only      # Remove only user-level symlinks
ai-rules list-agents                # Show available agents
```

### Configuration Management

```bash
# Interactive wizard for first-time setup
ai-rules config init                # Start configuration wizard

# View configuration
ai-rules config show                # Show raw config files
ai-rules config show --merged       # Show merged settings with overrides
ai-rules config show --agent claude # Show config for specific agent
ai-rules config edit                # Edit user config in $EDITOR
ai-rules config keys                # List all available configuration keys
ai-rules config keys --agent claude # List keys for specific agent
ai-rules config keys --json-output  # Output as JSON for scripting
ai-rules config clear-cache         # Clear cached merged settings
ai-rules config clear-cache --agent claude  # Clear cache for specific agent

# Manage exclusions
ai-rules exclude add "~/.claude/*.json"      # Add exclusion pattern (supports globs)
ai-rules exclude remove "~/.claude/*.json"   # Remove exclusion pattern
ai-rules exclude list                        # List all exclusions

# Manage settings overrides (for machine-specific settings)
ai-rules override set claude.model "claude-sonnet-4-5-20250929"  # Set override
ai-rules override unset claude.model         # Remove override
ai-rules override list                       # List all overrides
ai-rules override show claude.model          # Show value and source of a specific key
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

### Quick Start with Config Wizard

Run the interactive configuration wizard for guided setup:

```bash
ai-rules config init
```

This will walk you through:
1. Selecting common exclusions
2. Adding custom exclusion patterns (with glob support)
3. Setting up machine-specific settings overrides
4. Configuring projects

### User-Level Config

Create `~/.ai-rules-config.yaml` for user-level settings and project mappings:

```yaml
version: 1

# Global exclusions (apply to all contexts)
# Supports glob patterns: *.json, **/*.yaml, etc.
exclude_symlinks:
  - "~/.config/goose/config.yaml"
  - "~/.claude/*.log"              # Glob: exclude all log files
  - "~/.claude/agents/debug-*.md"  # Glob: exclude debug agents

# Machine-specific settings overrides
# Keeps repo settings.json synced via git, but allows local overrides
settings_overrides:
  claude:
    model: "claude-sonnet-4-5-20250929"  # Override model on personal laptop
    # Other settings inherited from repo config/claude/settings.json
  goose:
    provider: "anthropic"

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

**Config File Locations:**
- `~/.ai-rules-config.yaml` - User-specific config (exclusions, overrides, projects)
- `<repo>/.ai-rules-config.yaml` - Repo defaults (global exclusions only)

**Config Precedence:**
- User config exclusions + Repo config exclusions = Combined (additive)
- Settings overrides only loaded from user config (machine-specific, not in git)

### Settings Overrides - Syncing Configs Across Machines

**Problem:** You want to sync your `settings.json` via git, but need different settings on different machines (e.g., different model access on work vs personal laptop).

**Solution:** Use `settings_overrides` in your user config:

```yaml
# ~/.ai-rules-config.yaml on personal laptop
settings_overrides:
  claude:
    model: "claude-sonnet-4-5-20250929"  # No Opus access

# ~/.ai-rules-config.yaml on work laptop
settings_overrides:
  claude:
    model: "claude-opus-4-20250514"  # Has Opus access
```

Both machines sync the same `config/claude/settings.json` via git, but each has different local overrides. The system merges them at install time:

1. **Base settings** from `config/claude/settings.json` (git-tracked)
2. **Merged with** overrides from `~/.ai-rules-config.yaml` (local only)
3. **Cached** in `~/.ai-rules/cache/<agent>/<repo-hash>/settings.json`
4. **Symlinked** to `~/.claude/settings.json`

**Cache Management:**
- Cache is automatically built/updated during `ai-rules install`
- Cache is invalidated when base settings or overrides are modified
- Cache location: `~/.ai-rules/cache/<agent>/<repo-hash>/`
- Each repository has its own cache directory (prevents conflicts when using multiple repos)

**Discovering Available Keys:**
```bash
# See all available configuration keys that can be overridden
ai-rules config keys

# See keys for a specific agent
ai-rules config keys --agent claude

# Check a specific key's value and source
ai-rules override show claude.model
```

After changing overrides, run:
```bash
ai-rules install --rebuild-cache  # Force rebuild cache
# OR
ai-rules config clear-cache       # Clear all cached settings
ai-rules install                  # Rebuild on next install
```

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
- `<project>/AGENTS.md` → `config/projects/<name>/AGENTS.md`
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
├── AGENTS.md              # User-level rules → ~/AGENTS.md, ~/.CLAUDE.md, ~/.config/goose/.goosehints
├── projects/              # Project-level configurations
│   ├── my-api/
│   │   └── AGENTS.md      # → <project>/AGENTS.md, <project>/CLAUDE.md, <project>/.goosehints
│   └── my-blog/
│       └── AGENTS.md      # → <project>/AGENTS.md, <project>/CLAUDE.md, <project>/.goosehints
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

**Disable symlink:** Use the exclude command or add to config manually:
```bash
ai-rules exclude add "~/.claude/settings.json"
# Or edit manually: ai-rules config edit
```

**Override not applying:** Rebuild the merged settings cache:
```bash
ai-rules install --rebuild-cache
```

**View merged settings:** Check what's actually being applied:
```bash
ai-rules config show --merged
ai-rules config show --merged --agent claude
```

## License

MIT
