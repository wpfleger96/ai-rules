# AI Rules

Manage AI agent configurations through symlinks. Keep all your configs in one git-tracked location.

[![PyPI Downloads](https://img.shields.io/pypi/dm/ai-agent-rules.svg)](https://pypi.org/project/ai-agent-rules/)
[![PyPI version](https://img.shields.io/pypi/v/ai-agent-rules.svg)](https://pypi.org/project/ai-agent-rules/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ai-agent-rules.svg)](https://pypi.org/project/ai-agent-rules/)
[![CI](https://github.com/wpfleger96/ai-rules/actions/workflows/ci.yml/badge.svg)](https://github.com/wpfleger96/ai-rules/actions/workflows/ci.yml)
[![GitHub Contributors](https://img.shields.io/github/contributors/wpfleger96/ai-rules.svg)](https://github.com/wpfleger96/ai-rules/graphs/contributors)
[![Lines of Code](https://aschey.tech/tokei/github/wpfleger96/ai-rules?category=code)](https://github.com/wpfleger96/ai-rules)
[![License](https://img.shields.io/github/license/wpfleger96/ai-rules.svg)](https://github.com/wpfleger96/ai-rules/blob/main/LICENSE)

## Overview

Consolidates config files for AI coding agents (Claude Code, Cursor, Goose) into a single source of truth via symlinks:

- Git-tracked configs synced across machines
- Edit once, apply everywhere
- Exclude specific files (e.g., company-managed)
- Per-agent customizations

**Supported:** Claude Code (settings, agents, commands), Cursor (settings, keybindings), Goose (hints, config), Shared (AGENTS.md)

## Installation

**Requirements:** Python 3.10+, [uv](https://github.com/astral-sh/uv)

### From PyPI (Recommended)

One-command setup from PyPI:

```bash
uvx --from ai-agent-rules ai-rules setup
```

This will:
1. Install AI agent configuration symlinks
2. Make `ai-rules` available system-wide
3. Auto-install optional tools (claude-code-statusline)

After setup, you can run `ai-rules` from any directory.

### From GitHub (Development)

Install from GitHub to get the latest development code:

```bash
uvx --from ai-agent-rules ai-rules setup --github
```

This installs from the main branch and auto-detects the GitHub source for future updates.

### Local Development

For contributing or local development:

```bash
git clone https://github.com/wpfleger96/ai-rules.git
cd ai-rules
uv run ai-rules install
```

Use `uv run ai-rules <command>` to test local changes. The global `ai-rules` command continues to run your installed version (PyPI/GitHub).

### Updating

Check for and install updates:

```bash
ai-rules upgrade              # Check and install updates
ai-rules upgrade --check      # Only check for updates
```

Auto-update checks run weekly by default. Configure in `~/.ai-rules/update_config.yaml`:

```yaml
enabled: true
frequency: weekly  # daily, weekly, never
notify_only: false
```

## Usage

### User-Level Configuration

```bash
ai-rules setup                      # One-time setup: install symlinks + make available system-wide
ai-rules setup --github             # Install from GitHub (pre-release)
ai-rules setup --profile work       # Setup with a specific profile
ai-rules upgrade                    # Upgrade to latest version
ai-rules upgrade --check            # Check for updates without installing

ai-rules install                    # Install all agent configs + optional tools
ai-rules install --agents claude    # Install specific agents
ai-rules install --dry-run          # Preview changes
ai-rules install --force            # Skip confirmations
ai-rules install --rebuild-cache    # Rebuild merged settings cache

ai-rules status                     # Check symlink status + optional tools + active profile (✓✗⚠○)
ai-rules diff                       # Show config differences
ai-rules validate                   # Verify source files exist
ai-rules install                    # Re-sync after adding files
ai-rules uninstall                  # Remove all symlinks
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

# Manage exclusions
ai-rules exclude add "~/.claude/*.json"      # Add exclusion pattern (supports globs)
ai-rules exclude remove "~/.claude/*.json"   # Remove exclusion pattern
ai-rules exclude list                        # List all exclusions

# Manage settings overrides (for machine-specific settings)
ai-rules override set claude.model "claude-sonnet-4-5-20250929"  # Set simple override
ai-rules override set cursor.editor.fontSize 14  # Override Cursor font size
ai-rules override set claude.hooks.SubagentStop[0].hooks[0].command "script.py"  # Array notation
ai-rules override unset claude.model         # Remove override
ai-rules override list                       # List all overrides
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

### User-Level Config

Create `~/.ai-rules-config.yaml` for user-level settings:

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
    # Other settings inherited from base config/claude/settings.json
  cursor:
    editor.fontSize: 14  # Override font size on this machine
  goose:
    provider: "anthropic"
```

**Config File Location:**
- `~/.ai-rules-config.yaml` - User-specific config (exclusions and overrides)
- `~/.ai-rules/state.yaml` - Active profile and last install timestamp (auto-managed)
- `~/.ai-rules/cache/` - Merged settings cache (auto-generated)
- `~/.ai-rules/update_config.yaml` - Update check configuration

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
3. **Cached** in `~/.ai-rules/cache/claude/settings.json`
4. **Symlinked** to `~/.claude/settings.json`

After changing overrides, run:
```bash
ai-rules install --rebuild-cache
```

#### Array Notation for Nested Settings

Override commands support array index notation for complex nested structures:

```bash
# Override nested array elements (e.g., hooks)
ai-rules override set claude.hooks.SubagentStop[0].hooks[0].command "uv run ~/my-hook.py"

# Override environment variables
ai-rules override set claude.env.MY_VAR "value"

# The system validates paths and provides helpful suggestions
ai-rules override set claude.modle "sonnet"
# Error: Key 'modle' not found at 'modle'
# Available options: model, env, hooks, statusLine, ...
```

Path validation ensures you only set valid overrides that exist in the base settings, preventing typos and configuration errors.

### Cursor Settings

Cursor settings support the same override mechanism as other agents:

```yaml
# ~/.ai-rules-config.yaml
settings_overrides:
  cursor:
    editor.fontSize: 14
    terminal.integrated.defaultLocation: "editor"
```

> **Note:** `keybindings.json` uses direct symlinks without override merging (array structure).

### Profiles - Machine-Specific Configuration

Profiles let you group configuration overrides into named presets. Instead of manually maintaining different `~/.ai-rules-config.yaml` files across machines, define profiles once and select them at install time.

```bash
# List available profiles
ai-rules profile list

# View profile details
ai-rules profile show work
ai-rules profile show work --resolved  # Show with inheritance

# Check which profile is active
ai-rules profile current

# Switch to a different profile
ai-rules profile switch work

# Install with a specific profile
ai-rules install --profile work
```

Profiles are stored in `src/ai_rules/config/profiles/` and support inheritance:

```yaml
# profiles/work.yaml
name: work
description: Work laptop with extended context model
extends: null
settings_overrides:
  claude:
    env:
      ANTHROPIC_DEFAULT_SONNET_MODEL: "claude-sonnet-4-5-20250929[1m]"
    model: opusplan
```

Configuration layers (lowest to highest priority):
1. Profile overrides
2. Local `~/.ai-rules-config.yaml` overrides

Your local config always wins, so you can use a profile as a base and tweak specific settings per-machine. Profiles are git-tracked and can be shared across your team.

The active profile is tracked in `~/.ai-rules/state.yaml` and persists across sessions. Use `profile current` to see which profile is active, or `profile switch` to quickly change profiles without re-running the full install.

## Structure

```
config/
├── AGENTS.md              # User-level rules → ~/AGENTS.md, ~/.CLAUDE.md, ~/.config/goose/.goosehints
├── claude/
│   ├── settings.json      # → ~/.claude/settings.json
│   ├── agents/*.md        # → ~/.claude/agents/*.md (dynamic)
│   ├── commands/*.md      # → ~/.claude/commands/*.md (dynamic)
│   ├── hooks/*.py         # → ~/.claude/hooks/*.py (dynamic)
│   └── skills/*/SKILL.md  # → ~/.claude/skills/*/SKILL.md (dynamic)
├── cursor/
│   ├── settings.json      # → ~/Library/Application Support/Cursor/User/ (macOS)
│   │                      #    ~/AppData/Roaming/Cursor/User/ (Windows)
│   │                      #    ~/.config/Cursor/User/ (Linux)
│   └── keybindings.json   # → (same paths as settings.json)
└── goose/
    └── config.yaml        # → ~/.config/goose/config.yaml
```

> **Note:** The Cursor config files contain the maintainer's personal preferences
> (e.g., macOS-specific terminal settings). Customize for your environment.

## Optional Tools

AI Rules automatically installs optional tools that enhance functionality:

- **claude-code-statusline** - Custom status line for Claude Code showing token usage, git info, time, and workspace details

These tools are installed automatically during `setup` and `install` commands. Check installation status:

```bash
ai-rules status  # Shows Optional Tools section
```

If a tool fails to install, ai-rules continues normally (fail-open behavior).

## Extending

**Add Claude agent/command:**
1. Create `config/claude/agents/my-agent.md` or `config/claude/commands/my-cmd.md`
2. Run `ai-rules install`

**Add Claude skill with auto-activation:**
1. Create `config/claude/skills/my-skill/SKILL.md` with frontmatter:
```yaml
---
name: my-skill
description: "Brief description"
metadata:
  trigger-keywords: "keyword1, keyword2"
  trigger-patterns: "pattern1, pattern2"
---
```
2. Run `ai-rules install`
3. Skill auto-suggests when user prompt matches keywords/patterns

**Add Claude hook:**
1. Create `config/claude/hooks/my-hook.py`
2. Run `ai-rules install`
3. Configure in settings or overrides (e.g., UserPromptSubmit, SubagentStop)

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

### Quick Start with Just

This project uses [just](https://github.com/casey/just) for task automation.

**Install just**:
```bash
# macOS
brew install just

# Linux
cargo install just
# or: sudo apt install just (Ubuntu 23.04+)

# Windows
choco install just
```

**Common commands**:
```bash
just              # Run quick quality checks (sync, type-check, lint-check, format-check)
just --list       # List all available recipes

# Setup
just setup        # First-time setup: sync deps + install git hooks
just sync         # Sync dependencies only

# Code Quality
just check        # Quick quality checks (no tests)
just check-all    # All checks including tests
just lint         # Fix linting issues
just format       # Auto-format code
just type-check   # Run mypy type checking

# Testing
just test         # Run all tests (default config)
just test-unit    # Unit tests only
just test-integration  # Integration tests only
just test-cov     # Tests with coverage report

# Benchmarking
just benchmark-save     # Run and save baseline
just benchmark-compare  # Compare against baseline
just benchmark-record   # Compare and save
just benchmark-list     # List saved benchmarks
just benchmark-clean    # Remove all benchmarks

# Build
just build        # Build package
just rebuild      # Clean and build
```

### Running Tests
The test suite includes both unit tests and integration tests.

Using just (recommended):
```bash
just test         # Run all tests with default config
just test-unit    # Only unit tests
just test-integration  # Only integration tests
just test-cov     # Tests with coverage report
```

Using uv directly:
```bash
uv run pytest [--cov=src --cov-report=term-missing]  # All tests
uv run pytest -m unit      # Unit tests only
uv run pytest -m integration  # Integration tests only
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
