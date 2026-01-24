# ai-rules CLI Reference

Auto-generated from `--help`. Do not edit manually.

This is the complete CLI reference for ai-rules. For quick start examples and usage guides, see [README.md](../README.md).

## `ai-rules`

```
Usage: ai-rules [OPTIONS] COMMAND [ARGS]...

  AI Rules - Manage user-level AI agent configurations.

Options:
  --version  Show version and check for updates
  --help     Show this message and exit.

Commands:
  completions  Manage shell tab completion.
  config       Manage ai-rules configuration.
  diff         Show differences between repo configs and installed symlinks.
  exclude      Manage exclusion patterns.
  info         Show installation method and version info for ai-rules tools.
  install      Install AI agent configs via symlinks.
  list-agents  List available AI agents.
  override     Manage settings overrides.
  profile      Manage configuration profiles.
  setup        One-time setup: install symlinks and make ai-rules...
  status       Check status of AI agent symlinks.
  uninstall    Remove AI agent symlinks.
  upgrade      Upgrade ai-rules and related tools to the latest versions...
  validate     Validate configuration and source files.
```

## `ai-rules completions`

```
Usage: ai-rules completions [OPTIONS] COMMAND [ARGS]...

  Manage shell tab completion.

Options:
  --help  Show this message and exit.

Commands:
  bash       Output bash completion script for manual installation.
  install    Install shell completion to config file.
  status     Show shell completion installation status.
  uninstall  Remove shell completion from config file.
  zsh        Output zsh completion script for manual installation.
```

## `ai-rules completions bash`

```
Usage: ai-rules completions bash [OPTIONS]

  Output bash completion script for manual installation.

Options:
  --help  Show this message and exit.
```

## `ai-rules completions install`

```
Usage: ai-rules completions install [OPTIONS]

  Install shell completion to config file.

Options:
  --shell [bash|zsh]  Shell type (auto-detected if not specified)
  --help              Show this message and exit.
```

## `ai-rules completions status`

```
Usage: ai-rules completions status [OPTIONS]

  Show shell completion installation status.

Options:
  --help  Show this message and exit.
```

## `ai-rules completions uninstall`

```
Usage: ai-rules completions uninstall [OPTIONS]

  Remove shell completion from config file.

Options:
  --shell [bash|zsh]  Shell type (auto-detected if not specified)
  --help              Show this message and exit.
```

## `ai-rules completions zsh`

```
Usage: ai-rules completions zsh [OPTIONS]

  Output zsh completion script for manual installation.

Options:
  --help  Show this message and exit.
```

## `ai-rules config`

```
Usage: ai-rules config [OPTIONS] COMMAND [ARGS]...

  Manage ai-rules configuration.

Options:
  --help  Show this message and exit.

Commands:
  edit  Edit user configuration file in $EDITOR.
  init  Interactive configuration wizard.
  show  Show current configuration.
```

## `ai-rules config edit`

```
Usage: ai-rules config edit [OPTIONS]

  Edit user configuration file in $EDITOR.

Options:
  --help  Show this message and exit.
```

## `ai-rules config init`

```
Usage: ai-rules config init [OPTIONS]

  Interactive configuration wizard.

Options:
  --help  Show this message and exit.
```

## `ai-rules config show`

```
Usage: ai-rules config show [OPTIONS]

  Show current configuration.

Options:
  --merged      Show merged settings with overrides applied
  --agent TEXT  Show config for specific agent only
  --help        Show this message and exit.
```

## `ai-rules diff`

```
Usage: ai-rules diff [OPTIONS]

  Show differences between repo configs and installed symlinks.

Options:
  --agents TEXT  Comma-separated list of agents to check (default: all)
  --help         Show this message and exit.
```

## `ai-rules exclude`

```
Usage: ai-rules exclude [OPTIONS] COMMAND [ARGS]...

  Manage exclusion patterns.

Options:
  --help  Show this message and exit.

Commands:
  add     Add an exclusion pattern to user config.
  list    List all exclusion patterns.
  remove  Remove an exclusion pattern from user config.
```

## `ai-rules exclude add`

```
Usage: ai-rules exclude add [OPTIONS] PATTERN

  Add an exclusion pattern to user config.

  PATTERN can be an exact path or glob pattern (e.g., ~/.claude/*.json)

Options:
  --help  Show this message and exit.
```

## `ai-rules exclude list`

```
Usage: ai-rules exclude list [OPTIONS]

  List all exclusion patterns.

Options:
  --help  Show this message and exit.
```

## `ai-rules exclude remove`

```
Usage: ai-rules exclude remove [OPTIONS] PATTERN

  Remove an exclusion pattern from user config.

Options:
  --help  Show this message and exit.
```

## `ai-rules info`

```
Usage: ai-rules info [OPTIONS]

  Show installation method and version info for ai-rules tools.

  Displays how each tool was installed (PyPI or GitHub) along with current
  versions and update availability.

Options:
  --help  Show this message and exit.
```

## `ai-rules install`

```
Usage: ai-rules install [OPTIONS]

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

## `ai-rules list-agents`

```
Usage: ai-rules list-agents [OPTIONS]

  List available AI agents.

Options:
  --help  Show this message and exit.
```

## `ai-rules override`

```
Usage: ai-rules override [OPTIONS] COMMAND [ARGS]...

  Manage settings overrides.

Options:
  --help  Show this message and exit.

Commands:
  list   List all settings overrides.
  set    Set a settings override for an agent.
  unset  Remove a settings override.
```

## `ai-rules override list`

```
Usage: ai-rules override list [OPTIONS]

  List all settings overrides.

Options:
  --help  Show this message and exit.
```

## `ai-rules override set`

```
Usage: ai-rules override set [OPTIONS] KEY VALUE

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

## `ai-rules override unset`

```
Usage: ai-rules override unset [OPTIONS] KEY

  Remove a settings override.

  KEY should be in format 'agent.setting' (e.g., 'claude.model') Supports
  nested keys like 'agent.nested.key'

Options:
  --help  Show this message and exit.
```

## `ai-rules profile`

```
Usage: ai-rules profile [OPTIONS] COMMAND [ARGS]...

  Manage configuration profiles.

Options:
  --help  Show this message and exit.

Commands:
  current  Show currently active profile.
  list     List available profiles.
  show     Show profile details.
  switch   Switch to a different profile.
```

## `ai-rules profile current`

```
Usage: ai-rules profile current [OPTIONS]

  Show currently active profile.

Options:
  --help  Show this message and exit.
```

## `ai-rules profile list`

```
Usage: ai-rules profile list [OPTIONS]

  List available profiles.

Options:
  --help  Show this message and exit.
```

## `ai-rules profile show`

```
Usage: ai-rules profile show [OPTIONS] NAME

  Show profile details.

Options:
  --resolved  Show resolved profile with inheritance applied
  --help      Show this message and exit.
```

## `ai-rules profile switch`

```
Usage: ai-rules profile switch [OPTIONS] NAME

  Switch to a different profile.

Options:
  --help  Show this message and exit.
```

## `ai-rules setup`

```
Usage: ai-rules setup [OPTIONS]

  One-time setup: install symlinks and make ai-rules available system-wide.

  This is the recommended way to install ai-rules for first-time users.

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

## `ai-rules status`

```
Usage: ai-rules status [OPTIONS]

  Check status of AI agent symlinks.

Options:
  --agents TEXT  Comma-separated list of agents to check (default: all)
  --help         Show this message and exit.
```

## `ai-rules uninstall`

```
Usage: ai-rules uninstall [OPTIONS]

  Remove AI agent symlinks.

Options:
  -y, --yes      Auto-confirm without prompting
  --agents TEXT  Comma-separated list of agents to uninstall (default: all)
  --help         Show this message and exit.
```

## `ai-rules upgrade`

```
Usage: ai-rules upgrade [OPTIONS]

  Upgrade ai-rules and related tools to the latest versions from PyPI.

  Examples:     ai-rules upgrade                    # Check and install all
  updates     ai-rules upgrade --check            # Only check for updates
  ai-rules upgrade -y                 # Auto-confirm installation     ai-rules
  upgrade --only=statusline  # Only upgrade statusline tool

Options:
  --check                       Check for updates without installing
  --force                       Force reinstall even if up to date
  -y, --yes                     Auto-confirm installation without prompting
  --skip-install                Skip running 'install --rebuild-cache' after
                                upgrade
  --only [ai-rules|statusline]  Only upgrade specific tool
  --help                        Show this message and exit.
```

## `ai-rules validate`

```
Usage: ai-rules validate [OPTIONS]

  Validate configuration and source files.

Options:
  --agents TEXT  Comma-separated list of agents to validate (default: all)
  --help         Show this message and exit.
```

