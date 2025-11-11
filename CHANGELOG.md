# CHANGELOG


## Unreleased

### Features

- **Glob Pattern Support**: Exclusion patterns now support glob matching (e.g., `~/.claude/*.json`, `**/*.yaml`)
  - Enables flexible exclusions without listing every file
  - Works with both exact paths and glob patterns

- **Settings Overrides**: New machine-specific settings override system
  - Sync base `settings.json` via git while maintaining local overrides
  - Perfect for different model access across work/personal laptops
  - Deep merge support for nested settings
  - Cached merged settings in `~/.ai-rules/cache/`

- **Improved CLI UX**: New command groups for easier configuration management
  - `ai-rules config init` - Interactive configuration wizard for first-time setup
  - `ai-rules config show` - View raw config or merged settings with overrides
  - `ai-rules config edit` - Edit user config in $EDITOR
  - `ai-rules config keys` - Discover all available configuration keys that can be overridden
  - `ai-rules config clear-cache` - Clear cached merged settings
  - `ai-rules exclude add/remove/list` - Manage exclusions without touching YAML
  - `ai-rules override set/unset/list/show` - Manage and inspect settings overrides via CLI

- **Install Enhancements**:
  - `--rebuild-cache` flag to rebuild merged settings cache
  - Automatic settings merging during install
  - Cache management for merged configurations
  - Progress indication during cache building
  - Automatic config backup before overwriting in `config init`

- **Discoverability Features**:
  - Configuration keys are now discoverable via `config keys` command
  - Override validation warns when setting unknown keys
  - Value diff display shows base, current, and new values when setting overrides
  - Helpful suggestions in error messages

### Bug Fixes

- **Cache Path Collision**: Fixed cache collision when using multiple ai-rules repos
  - Each repository now has its own cache directory using a repo path hash
  - Prevents settings from one repo affecting another repo

### Documentation

- Comprehensive README updates with new command documentation
- Updated example config file with detailed comments and use cases
- Added troubleshooting section for common override scenarios
- Documented config file precedence and merging behavior

### Tests

- Added comprehensive test suite for glob pattern matching
- Added tests for settings override loading and merging
- Added tests for cache creation and management
- Added tests for cache path collision prevention
- Added tests for JSON parsing error handling
- All 88 tests passing


## v0.2.0 (2025-11-07)

### Features

- Add SubagentStop hook, project-level rule support, shared AGENTS.md config, and post-merge hook
  ([`263e07c`](https://github.com/wpfleger96/ai-rules/commit/263e07cbf712afad6720c17fe4327818d80fedb1))


## v0.1.1 (2025-11-04)

### Bug Fixes

- Don't double-prompt the user for confirmation
  ([`54fa5e1`](https://github.com/wpfleger96/ai-rules/commit/54fa5e1399f78188854a3a8703382a5761343fc5))

### Chores

- Update README and readd MIT license
  ([`9bd4e65`](https://github.com/wpfleger96/ai-rules/commit/9bd4e65c4e790e15c5457d33f00db4a2e342ad57))


## v0.1.0 (2025-11-04)

### Features

- Initial release
  ([`8a9c739`](https://github.com/wpfleger96/ai-rules/commit/8a9c73994c4b84f2754076d555bed68303d715fe))
