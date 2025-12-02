# CHANGELOG


## v0.4.1 (2025-12-02)

### Bug Fixes

- Expose both package names
  ([`dc78525`](https://github.com/wpfleger96/ai-rules/commit/dc78525b2ad019cdeaf4b713fa7ec054bc4ec77d))

### Chores

- Only run publish workflow if we released a new version tag
  ([`5b8488b`](https://github.com/wpfleger96/ai-rules/commit/5b8488b0d37aa38236bcfae466d96c88a1b41dd4))

- Readme badges
  ([`274b949`](https://github.com/wpfleger96/ai-rules/commit/274b949ce9d91a39bc23b861a6aa879be0c2bb3e))


## v0.4.0 (2025-12-02)

### Chores

- Ai spaghetti refactor
  ([`e1c0694`](https://github.com/wpfleger96/ai-rules/commit/e1c0694822c34320c2ad7ee0b9dee4667460eff8))

- Cleanup and another CI test fix
  ([`7acadcf`](https://github.com/wpfleger96/ai-rules/commit/7acadcf9b757f211d1fd306cace79e3932f6f131))

### Features

- Add bootstrap install and auto update processes
  ([`6569767`](https://github.com/wpfleger96/ai-rules/commit/65697676c24c08a2b5da7a0fb6deb6df0b065920))

- Publish to pypi
  ([`14e41f3`](https://github.com/wpfleger96/ai-rules/commit/14e41f3863284d08ddd645c9324ea741fed858d0))


## v0.3.0 (2025-12-01)

### Bug Fixes

- Address critical code review issues
  ([`8b97673`](https://github.com/wpfleger96/ai-rules/commit/8b976730ce1ca41c9e7c3cf5a69594baf457bd6f))

This commit fixes the critical and high-priority issues identified in the code review:

Critical Fixes: - Fix deep merge shallow copy bug - Use copy.deepcopy() instead of base.copy() to
  prevent mutation of base dictionaries (CRITICAL) - Add nested key support to override unset
  command - Now matches override set functionality for consistency

High-Priority Fixes: - Add cache invalidation/staleness detection - Cache is now checked against
  base settings and user config modification times - Optimize cache rebuilding - Cache only built
  during install, not on every get_symlinks() call (status checks are now read-only)

Technical Changes: - Added is_cache_stale() method to check if cache needs rebuilding - Added
  get_settings_file_for_symlink() for read-only symlink enumeration - Modified
  build_merged_settings() to skip rebuild when cache is fresh - Added force_rebuild parameter to
  build_merged_settings() - Cache building moved to install command, before symlink creation - Added
  7 new tests for cache invalidation logic

Test Results: - All 30 tests passing (23 original + 7 new) - Tests cover cache staleness detection,
  force rebuild, and file selection

Performance Impact: - Status/diff commands no longer rebuild cache unnecessarily - Cache
  automatically invalidates when base settings or overrides change - --rebuild-cache flag forces
  cache rebuild when needed

### Chores

- Couple more CC perms
  ([`2af58b4`](https://github.com/wpfleger96/ai-rules/commit/2af58b475f76e0900fce0a35d4911381ace03af9))

- Tweak AGENTS file
  ([`8b02b94`](https://github.com/wpfleger96/ai-rules/commit/8b02b94197dc50cd86cc8b69586bd1f45133a57f))

### Features

- Improve exclusion config UX and add settings merge functionality
  ([`673057a`](https://github.com/wpfleger96/ai-rules/commit/673057a8c5278ed913d698deaf11482f4a447737))

This commit significantly improves the user experience for managing exclusions and adds powerful
  settings override capabilities for machine-specific configurations.

Major Features: - Glob pattern support for exclusions (e.g., ~/.claude/*.json) - Settings overrides
  for machine-specific settings with deep merge - Interactive config wizard (ai-rules config init) -
  New CLI command groups: exclude, override, config - Settings cache management with --rebuild-cache
  flag

CLI Improvements: - ai-rules config init: Interactive wizard for first-time setup - ai-rules config
  show: View raw or merged settings - ai-rules config edit: Edit config in $EDITOR - ai-rules
  exclude add/remove/list: Manage exclusions - ai-rules override set/unset/list: Manage settings
  overrides

Settings Merge System: - Sync base settings.json via git - Override specific keys per machine (e.g.,
  model access) - Deep merge with caching in ~/.ai-rules/cache/ - Supports different settings across
  work/personal laptops

Technical Changes: - Added fnmatch for glob pattern matching in config.py - Implemented deep merge
  algorithm for settings - Added build_merged_settings() for cache management - Enhanced ClaudeAgent
  to use merged settings - Added 16 new tests covering glob patterns and merging

Documentation: - Comprehensive README updates with examples - Updated .ai-rules-config.yaml.example
  with detailed comments - Added troubleshooting section - Documented config precedence and merging
  behavior - Updated CHANGELOG.md

All tests passing (23 tests).

Fixes #[issue-number]


## v0.2.0 (2025-12-01)

### Bug Fixes

- Don't double-prompt the user for confirmation
  ([`54fa5e1`](https://github.com/wpfleger96/ai-rules/commit/54fa5e1399f78188854a3a8703382a5761343fc5))

### Chores

- Update README and readd MIT license
  ([`9bd4e65`](https://github.com/wpfleger96/ai-rules/commit/9bd4e65c4e790e15c5457d33f00db4a2e342ad57))

### Features

- Add SubagentStop hook, project-level rule support, shared AGENTS.md config, and post-merge hook
  ([`263e07c`](https://github.com/wpfleger96/ai-rules/commit/263e07cbf712afad6720c17fe4327818d80fedb1))

- Initial release
  ([`8a9c739`](https://github.com/wpfleger96/ai-rules/commit/8a9c73994c4b84f2754076d555bed68303d715fe))
