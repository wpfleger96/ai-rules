# ai-agent-rules CLI Reference

Auto-generated from `--help`. Do not edit manually.

This is the complete CLI reference for ai-agent-rules. For quick start examples and usage guides, see [README.md](../README.md).

## `ai-agent-rules`

```
Usage: ai-agent-rules [OPTIONS] COMMAND [ARGS]...

  AI Rules - Manage user-level AI agent configurations.

Options:
  --version  Show version and check for updates
  --help     Show this message and exit.

Commands:
  completions  Manage shell tab completion.
  config       Manage ai-agent-rules configuration.
  diff         Show differences between repo configs and installed symlinks.
  exclude      Manage exclusion patterns.
  info         Show installation method and version info for...
  install      Install AI agent configs via symlinks.
  list-agents  List available AI agents.
  override     Manage settings overrides.
  profile      Manage configuration profiles.
  setup        One-time setup: install symlinks and make ai-agent-rules...
  status       Check status of AI agent symlinks.
  uninstall    Remove AI agent symlinks.
  upgrade      Upgrade ai-agent-rules and related tools to the latest...
  validate     Validate configuration and source files.
```

## `ai-agent-rules completions`

```
Usage: ai-agent-rules completions [OPTIONS] COMMAND [ARGS]...

  Manage shell tab completion.

Options:
  --help  Show this message and exit.

Commands:
  bash       Output bash completion script for manual installation.
  install    Install shell completion to config file.
  status     Show shell completion installation status.
  uninstall  Remove shell completion from config file.
  update     Re-generate completion block (fixes PATH shadowing issues).
  zsh        Output zsh completion script for manual installation.
```

## `ai-agent-rules completions bash`

```
Usage: ai-agent-rules completions bash [OPTIONS]

  Output bash completion script for manual installation.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules completions install`

```
Usage: ai-agent-rules completions install [OPTIONS]

  Install shell completion to config file.

Options:
  --shell [bash|zsh]  Shell type (auto-detected if not specified)
  --help              Show this message and exit.
```

## `ai-agent-rules completions status`

```
Usage: ai-agent-rules completions status [OPTIONS]

  Show shell completion installation status.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules completions uninstall`

```
Usage: ai-agent-rules completions uninstall [OPTIONS]

  Remove shell completion from config file.

Options:
  --shell [bash|zsh]  Shell type (auto-detected if not specified)
  --help              Show this message and exit.
```

## `ai-agent-rules completions update`

```
Usage: ai-agent-rules completions update [OPTIONS]

  Re-generate completion block (fixes PATH shadowing issues).

Options:
  --shell [bash|zsh]  Shell type (auto-detected if not specified)
  --help              Show this message and exit.
```

## `ai-agent-rules completions zsh`

```
Usage: ai-agent-rules completions zsh [OPTIONS]

  Output zsh completion script for manual installation.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules config`

```
Usage: ai-agent-rules config [OPTIONS] COMMAND [ARGS]...

  Manage ai-agent-rules configuration.

Options:
  --help  Show this message and exit.

Commands:
  edit  Edit user configuration file in $EDITOR.
  init  Interactive configuration wizard.
  show  Show current configuration.
```

## `ai-agent-rules config edit`

```
Usage: ai-agent-rules config edit [OPTIONS]

  Edit user configuration file in $EDITOR.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules config init`

```
Usage: ai-agent-rules config init [OPTIONS]

  Interactive configuration wizard.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules config show`

```
Usage: ai-agent-rules config show [OPTIONS]

  Show current configuration.

Options:
  --merged      Show merged settings with overrides applied
  --agent TEXT  Show config for specific agent only
  --help        Show this message and exit.
```

## `ai-agent-rules diff`

```
Usage: ai-agent-rules diff [OPTIONS]

  Show differences between repo configs and installed symlinks.

Options:
  --agents TEXT  Comma-separated list of agents to check (default: all)
  --help         Show this message and exit.
```

## `ai-agent-rules exclude`

```
Usage: ai-agent-rules exclude [OPTIONS] COMMAND [ARGS]...

  Manage exclusion patterns.

Options:
  --help  Show this message and exit.

Commands:
  add     Add an exclusion pattern to user config.
  list    List all exclusion patterns.
  remove  Remove an exclusion pattern from user config.
```

## `ai-agent-rules exclude add`

```
Usage: ai-agent-rules exclude add [OPTIONS] PATTERN

  Add an exclusion pattern to user config.

  PATTERN can be an exact path or glob pattern (e.g., ~/.claude/*.json)

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules exclude list`

```
Usage: ai-agent-rules exclude list [OPTIONS]

  List all exclusion patterns.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules exclude remove`

```
Usage: ai-agent-rules exclude remove [OPTIONS] PATTERN

  Remove an exclusion pattern from user config.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules info`

```
Usage: ai-agent-rules info [OPTIONS]

  Show installation method and version info for ai-agent-rules tools.

  Displays how each tool was installed (PyPI or GitHub) along with current
  versions and update availability.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules install`

```
Usage: ai-agent-rules install [OPTIONS]

  Install AI agent configs via symlinks.

Options:
  -y, --yes           Auto-confirm without prompting
  --dry-run           Preview changes without applying
  --rebuild-cache     Rebuild merged settings cache (use after changing
                      overrides)
  --agents TEXT       Comma-separated list of agents to install (default: all)
  --skip-completions  Skip shell completion installation
  --profile TEXT      Profile to use (default: 'default' for backward
                      compatibility)
  --help              Show this message and exit.
```

## `ai-agent-rules list-agents`

```
Usage: ai-agent-rules list-agents [OPTIONS]

  List available AI agents.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules override`

```
Usage: ai-agent-rules override [OPTIONS] COMMAND [ARGS]...

  Manage settings overrides.

Options:
  --help  Show this message and exit.

Commands:
  list   List all settings overrides.
  set    Set a settings override for an agent.
  unset  Remove a settings override.
```

## `ai-agent-rules override list`

```
Usage: ai-agent-rules override list [OPTIONS]

  List all settings overrides.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules override set`

```
Usage: ai-agent-rules override set [OPTIONS] KEY VALUE

  Set a settings override for an agent.

  KEY should be in format 'agent.setting' (e.g., 'claude.model') Supports
  array notation: 'claude.hooks.SubagentStop[0].hooks[0].command' VALUE will
  be parsed as JSON if possible, otherwise treated as string

  Array notation examples: - claude.hooks.SubagentStop[0].command -
  claude.hooks.SubagentStop[0].hooks[0].command -
  claude.items[0].nested[1].value

  Path validation: - Validates agent name (must be 'claude', 'goose', etc.) -
  Validates full path against base settings structure - Provides helpful
  suggestions when paths are invalid

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules override unset`

```
Usage: ai-agent-rules override unset [OPTIONS] KEY

  Remove a settings override.

  KEY should be in format 'agent.setting' (e.g., 'claude.model') Supports
  nested keys like 'agent.nested.key'

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules profile`

```
Usage: ai-agent-rules profile [OPTIONS] COMMAND [ARGS]...

  Manage configuration profiles.

Options:
  --help  Show this message and exit.

Commands:
  current  Show currently active profile.
  list     List available profiles.
  show     Show profile details.
  switch   Switch to a different profile.
```

## `ai-agent-rules profile current`

```
Usage: ai-agent-rules profile current [OPTIONS]

  Show currently active profile.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules profile list`

```
Usage: ai-agent-rules profile list [OPTIONS]

  List available profiles.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules profile show`

```
Usage: ai-agent-rules profile show [OPTIONS] NAME

  Show profile details.

Options:
  --resolved  Show resolved profile with inheritance applied
  --help      Show this message and exit.
```

## `ai-agent-rules profile switch`

```
Usage: ai-agent-rules profile switch [OPTIONS] NAME

  Switch to a different profile.

Options:
  --help  Show this message and exit.
```

## `ai-agent-rules setup`

```
Usage: ai-agent-rules setup [OPTIONS]

  One-time setup: install symlinks and make ai-agent-rules available system-
  wide.

  This is the recommended way to install ai-agent-rules for first-time users.

  Example:     uvx ai-agent-rules setup

Options:
  --github            Install from GitHub instead of PyPI
  -y, --yes           Auto-confirm without prompting
  --dry-run           Show what would be done
  --skip-symlinks     Skip symlink installation step
  --skip-completions  Skip shell completion setup
  --profile TEXT      Profile to use (default: 'default')
  --help              Show this message and exit.
```

## `ai-agent-rules status`

```
Usage: ai-agent-rules status [OPTIONS]

  Check status of AI agent symlinks.

Options:
  --agents TEXT  Comma-separated list of agents to check (default: all)
  --help         Show this message and exit.
```

## `ai-agent-rules uninstall`

```
Usage: ai-agent-rules uninstall [OPTIONS]

  Remove AI agent symlinks.

Options:
  -y, --yes      Auto-confirm without prompting
  --agents TEXT  Comma-separated list of agents to uninstall (default: all)
  --help         Show this message and exit.
```

## `ai-agent-rules upgrade`

```
Usage: ai-agent-rules upgrade [OPTIONS]

  Upgrade ai-agent-rules and related tools to the latest versions from PyPI.

  Examples:     ai-agent-rules upgrade                    # Check and install
  all updates     ai-agent-rules upgrade --check            # Only check for
  updates     ai-agent-rules upgrade -y                 # Auto-confirm
  installation     ai-agent-rules upgrade --only=statusline  # Only upgrade
  statusline tool

Options:
  --check                         Check for updates without installing
  --force                         Force reinstall even if up to date
  -y, --yes                       Auto-confirm installation without prompting
  --skip-install                  Skip running 'install --rebuild-cache' after
                                  upgrade
  --only [ai-agent-rules|ai-rules|statusline]
                                  Only upgrade specific tool
  --help                          Show this message and exit.
```

## `ai-agent-rules validate`

```
Usage: ai-agent-rules validate [OPTIONS]

  Validate configuration and source files.

Options:
  --agents TEXT  Comma-separated list of agents to validate (default: all)
  --help         Show this message and exit.
```

