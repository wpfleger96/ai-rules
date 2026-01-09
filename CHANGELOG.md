# CHANGELOG


## v0.18.3 (2026-01-09)

### Bug Fixes

- Auto enable plugins
  ([`f4dafb7`](https://github.com/wpfleger96/ai-rules/commit/f4dafb74cd02464ef96bbeb669d6c790514668b8))


## v0.18.2 (2026-01-09)

### Bug Fixes

- Plugin
  ([`c695c3d`](https://github.com/wpfleger96/ai-rules/commit/c695c3dc0d4334284a2403077de2aee11bae3e93))


## v0.18.1 (2026-01-08)

### Bug Fixes

- Wordy PR descriptions
  ([`1a9fc3a`](https://github.com/wpfleger96/ai-rules/commit/1a9fc3a66bc4a72aaa5b17a2620a15ab69394d1a))


## v0.18.0 (2026-01-08)

### Chores

- Clean up vestigial code
  ([`b86a53f`](https://github.com/wpfleger96/ai-rules/commit/b86a53fa15685224d94491c1f1ccb3cc05fd09c8))

- Docs
  ([`41ff2bb`](https://github.com/wpfleger96/ai-rules/commit/41ff2bba0e5256160fe4e08fbc48e00d39afb8f0))

### Features

- Add claude code plugin support
  ([`2e18fa4`](https://github.com/wpfleger96/ai-rules/commit/2e18fa408f3fabcbcee5f664639017e383c3ac47))


## v0.17.0 (2025-12-20)

### Features

- Migrating cursor settings to shell-configs project
  ([`b95ea16`](https://github.com/wpfleger96/ai-rules/commit/b95ea16e327eba3c4ed2a543d98f7f239f2b3cbb))


## v0.16.1 (2025-12-20)

### Bug Fixes

- Optimize token usage
  ([`bb93497`](https://github.com/wpfleger96/ai-rules/commit/bb93497f41fc32fcad2064fbec0cb97f2aa8fbfb))

### Chores

- Docs
  ([`78ee562`](https://github.com/wpfleger96/ai-rules/commit/78ee56246d8639ed7492b3605126ae6c573f85e8))


## v0.16.0 (2025-12-19)

### Bug Fixes

- /update-docs should auto invoke doc-writer skill, and remove unnecessary update command
  ([`93c8f72`](https://github.com/wpfleger96/ai-rules/commit/93c8f72589f17e08363a76e74ec4f0222493435b))

### Features

- Userpromptsubmit hook to force skill activation, and claude code only autoloads skill frontmatter
  so put activation instructions there
  ([`fa37479`](https://github.com/wpfleger96/ai-rules/commit/fa374794e912dc8e87f5f063e8ffbe61fe413409))


## v0.15.15 (2025-12-18)

### Bug Fixes

- Clarify between user/manual vs. profile overrides
  ([`975694e`](https://github.com/wpfleger96/ai-rules/commit/975694e54e734e6dd68477921f91ff42dbcd2537))


## v0.15.14 (2025-12-18)

### Bug Fixes

- All commands should respect current profile if set
  ([`2a7cdd9`](https://github.com/wpfleger96/ai-rules/commit/2a7cdd90f2ba8fe9c8dda127bd8109caa44d36a6))


## v0.15.13 (2025-12-18)

### Bug Fixes

- Add completions status command
  ([`5fbe247`](https://github.com/wpfleger96/ai-rules/commit/5fbe2472ebd08262767ab9c4fb0162e58a6ef939))


## v0.15.12 (2025-12-18)

### Bug Fixes

- Get prompt-engineer skill to auto trigger
  ([`5490942`](https://github.com/wpfleger96/ai-rules/commit/5490942778813fa8aa59980c628877dda62f0a00))

### Chores

- Cleanup dead code
  ([`b98d4d7`](https://github.com/wpfleger96/ai-rules/commit/b98d4d7f5fad5eb40eb1ebde6ef8518ea8305c58))


## v0.15.11 (2025-12-18)

### Bug Fixes

- Switching profiles should gracefully handle conflicting overrides
  ([`7080a3d`](https://github.com/wpfleger96/ai-rules/commit/7080a3df51608381be23805080765622828a6125))


## v0.15.10 (2025-12-17)

### Bug Fixes

- Remove useless hook
  ([`ad4d540`](https://github.com/wpfleger96/ai-rules/commit/ad4d5403a12ca7f8a5f64041da1c43c513117038))


## v0.15.9 (2025-12-17)

### Bug Fixes

- Intelligent uninstall+reinstall logic
  ([`09274c4`](https://github.com/wpfleger96/ai-rules/commit/09274c43a3856850e6f33908e971cc39a3737101))


## v0.15.8 (2025-12-17)

### Bug Fixes

- Remove local install option expose info command for troubleshooting
  ([`b998e5d`](https://github.com/wpfleger96/ai-rules/commit/b998e5d0d2e638e117f6b06f1950c963f9c7e68f))


## v0.15.7 (2025-12-17)

### Bug Fixes

- Dryrun/force flags and cc perms
  ([`5f0d73e`](https://github.com/wpfleger96/ai-rules/commit/5f0d73e3b680ab5624f00bc19a41890ca7b9894c))

- Setup commmand should also upgrade if already installed
  ([`f381cef`](https://github.com/wpfleger96/ai-rules/commit/f381cef83c2bfeb6aed9006660d44da10b574139))


## v0.15.6 (2025-12-17)

### Bug Fixes

- **upgrade**: Flaky upgrade for GitHub-based installs
  ([`a8ed872`](https://github.com/wpfleger96/ai-rules/commit/a8ed872c20b0a0cae6cd2c17de6b7c45d0b720ac))


## v0.15.5 (2025-12-11)

### Bug Fixes

- Update code comment instructions
  ([`ef78069`](https://github.com/wpfleger96/ai-rules/commit/ef78069ac6f4b2838251737a681deb74acc4019f))

### Chores

- Docs
  ([`9a2dbdc`](https://github.com/wpfleger96/ai-rules/commit/9a2dbdc01e36a8eab3303bb75cc1a3371ca743a1))


## v0.15.4 (2025-12-11)

### Bug Fixes

- Profile should show current and let you switch
  ([`7133c0e`](https://github.com/wpfleger96/ai-rules/commit/7133c0e4e480f4f23c4b0b5ab1de64dceaf13c77))


## v0.15.3 (2025-12-11)

### Bug Fixes

- This burns through pro sub
  ([`828de97`](https://github.com/wpfleger96/ai-rules/commit/828de97921774e45a416fc953c6cb30ced90eda6))

### Chores

- Docs
  ([`859d3b4`](https://github.com/wpfleger96/ai-rules/commit/859d3b4c3c448e591b0fd4a80065616ecc5dfc7a))


## v0.15.2 (2025-12-11)

### Bug Fixes

- Goosehints not getting built in wheel
  ([`c0c4b8b`](https://github.com/wpfleger96/ai-rules/commit/c0c4b8be353b0f66cf38655398e42eeba847435b))


## v0.15.1 (2025-12-11)

### Bug Fixes

- Statusline install should respect install source
  ([`8b0bada`](https://github.com/wpfleger96/ai-rules/commit/8b0bada7a725ddc74ac4aa25b5e4fd45164bc9b2))


## v0.15.0 (2025-12-10)

### Features

- Add github installation support
  ([`a7c00cf`](https://github.com/wpfleger96/ai-rules/commit/a7c00cfb224b78ea089f2ada1ae394bdac514ba1))


## v0.14.0 (2025-12-10)

### Chores

- Update AGENTS.md
  ([`1f3e7fd`](https://github.com/wpfleger96/ai-rules/commit/1f3e7fd7dc33b928f6ff3e03397abb7cf6152e0a))

### Features

- Add profiles feature
  ([`f82159c`](https://github.com/wpfleger96/ai-rules/commit/f82159cb6752fc119a0820c009da8720fbe1879c))


## v0.13.0 (2025-12-10)

### Bug Fixes

- Dont install completions if already installed
  ([`b95e30d`](https://github.com/wpfleger96/ai-rules/commit/b95e30d8a170007d7070e4af2987b6dfaf2b87d2))

- Dont waste tokens, other hints files should @mention the main AGENTS.md
  ([`fab89e7`](https://github.com/wpfleger96/ai-rules/commit/fab89e721a851472d37f0af4cb7519c3c2501b0b))

### Features

- Add supported CursorAgent
  ([`b648e66`](https://github.com/wpfleger96/ai-rules/commit/b648e660730906ca6c3f017fc9ec8dabe05d0d0c))


## v0.12.4 (2025-12-09)

### Bug Fixes

- Cc perm
  ([`f895aa0`](https://github.com/wpfleger96/ai-rules/commit/f895aa0fc6aeb8f9921b9ddcb98dc38b28eede60))


## v0.12.3 (2025-12-08)

### Bug Fixes

- Uvx pip still uses pip config not uv
  ([`1593f0d`](https://github.com/wpfleger96/ai-rules/commit/1593f0d38f1781473a89ddec46d84fefe5ecff4e))


## v0.12.2 (2025-12-08)

### Bug Fixes

- Cc perm
  ([`7ffeb1a`](https://github.com/wpfleger96/ai-rules/commit/7ffeb1a17948a245bc1e2969cfe1307c78f0fc02))

### Chores

- Update AGENTS.md
  ([`86956f0`](https://github.com/wpfleger96/ai-rules/commit/86956f0121d8d2ba9e6d6cfb55e8bee1740c3fd0))


## v0.12.1 (2025-12-08)

### Bug Fixes

- Respect global package index settings
  ([`beb0fd4`](https://github.com/wpfleger96/ai-rules/commit/beb0fd4814007ca8d4df10c327c7a6c2059038a8))


## v0.12.0 (2025-12-08)

### Features

- Agents-md slash command
  ([`9edb6e3`](https://github.com/wpfleger96/ai-rules/commit/9edb6e30feeba26605d0b49921a3018964de397b))


## v0.11.0 (2025-12-08)

### Features

- Doc-writer skill and annotate-changelog slash command
  ([`0faaf4e`](https://github.com/wpfleger96/ai-rules/commit/0faaf4ece829a80fb646b5815b77398e48a45c86))


## v0.10.3 (2025-12-07)

### Bug Fixes

- Cc perms
  ([`9dd366c`](https://github.com/wpfleger96/ai-rules/commit/9dd366cd171480976fd25cc840256bf224453fe3))


## v0.10.2 (2025-12-07)

### Bug Fixes

- Still flaky
  ([`3a6a1ce`](https://github.com/wpfleger96/ai-rules/commit/3a6a1ce4b4b70e49cf0968b42ca78c90c2109ef5))


## v0.10.1 (2025-12-07)

### Bug Fixes

- Flaky update behavior
  ([`f894249`](https://github.com/wpfleger96/ai-rules/commit/f894249cf324fd6dfa86a6d99d6562386f1f9d85))

### Chores

- Update script
  ([`8ae0008`](https://github.com/wpfleger96/ai-rules/commit/8ae00088ee8e4db9f07c7f4f101c214f425c79e1))


## v0.10.0 (2025-12-06)

### Chores

- More code quality
  ([`f639929`](https://github.com/wpfleger96/ai-rules/commit/f639929156d919ea582140e151ee6114002d485a))

### Features

- Opus avaliable on pro now
  ([`c7e9969`](https://github.com/wpfleger96/ai-rules/commit/c7e9969fadc997bfa7fe70d463fcd0deafd92197))


## v0.9.5 (2025-12-05)

### Chores

- Code quality
  ([`9793b0e`](https://github.com/wpfleger96/ai-rules/commit/9793b0e22ab752bdf4deddfe9e2f083aff63d13a))


## v0.9.4 (2025-12-05)

### Bug Fixes

- Show diff during install
  ([`ea63ecc`](https://github.com/wpfleger96/ai-rules/commit/ea63ecc5996a2994325c3cdc6cc741441c4421ec))


## v0.9.3 (2025-12-05)

### Bug Fixes

- Cc perm
  ([`490ad02`](https://github.com/wpfleger96/ai-rules/commit/490ad0204b37f1553852f6dd96aceaf8556ce8c8))

- Llms are dumb
  ([`fd29f5b`](https://github.com/wpfleger96/ai-rules/commit/fd29f5b9e9c62064737853e29da7cb3e4fe63d74))


## v0.9.2 (2025-12-04)

### Bug Fixes

- Update daily and force --version to bypass cache
  ([`f2efa65`](https://github.com/wpfleger96/ai-rules/commit/f2efa653bfea854476c33e947078c1ade9d6e07d))

### Chores

- Add editor config and fix precommit bug
  ([`35693f0`](https://github.com/wpfleger96/ai-rules/commit/35693f0f986bc272ff90875ddf9424ab1c9d820e))


## v0.9.1 (2025-12-04)

### Bug Fixes

- Shell lint cmds
  ([`447463e`](https://github.com/wpfleger96/ai-rules/commit/447463e4da6b35c840e3201ec3c8a3d968e865b3))


## v0.9.0 (2025-12-04)

### Features

- Use shell registry for supported shells
  ([`623e375`](https://github.com/wpfleger96/ai-rules/commit/623e37544b15dd333baca55dc665d13d53fa8325))


## v0.8.1 (2025-12-04)

### Bug Fixes

- Install should install completions
  ([`6cbb669`](https://github.com/wpfleger96/ai-rules/commit/6cbb669a17121a7f9f1de076a9d11e4e254f3d2d))

### Chores

- Migrate repo to use Just
  ([`b139720`](https://github.com/wpfleger96/ai-rules/commit/b139720729344e12ea1877fdfac4e5b74f5305fa))

### Continuous Integration

- Prevent race condition in release workflow
  ([`9ee9827`](https://github.com/wpfleger96/ai-rules/commit/9ee982700ff78230726e715ae896c8c54e11d4e6))


## v0.8.0 (2025-12-04)

### Bug Fixes

- Detect and handle local wheel installations in upgrade command
  ([`41a9797`](https://github.com/wpfleger96/ai-rules/commit/41a97973cd7385c2124e1bffc309e8ec288380ea))

### Features

- Add shell completions support with auto install
  ([`f8c3bd8`](https://github.com/wpfleger96/ai-rules/commit/f8c3bd84a479d89aa4e83accf8d5bb64f856ef61))


## v0.7.0 (2025-12-03)

### Features

- Auto update statusline script
  ([`fbb4688`](https://github.com/wpfleger96/ai-rules/commit/fbb468850ac943ba37e6a1f162e4278632933f8e))


## v0.6.0 (2025-12-03)

### Documentation

- Update README
  ([`a8b1815`](https://github.com/wpfleger96/ai-rules/commit/a8b18150468d16ddd6a22384125d443192db4655))

### Features

- Auto install status line script
  ([`e09d21c`](https://github.com/wpfleger96/ai-rules/commit/e09d21c3740fdcc5a923431444b79c106db2d76c))


## v0.5.4 (2025-12-02)

### Bug Fixes

- Stop caching wrong symlink path when overrides exist
  ([`8611713`](https://github.com/wpfleger96/ai-rules/commit/86117135c0854acc7b370bc3c1d4325595003845))


## v0.5.3 (2025-12-02)

### Bug Fixes

- Performance improvements during symlink install
  ([`4cc1700`](https://github.com/wpfleger96/ai-rules/commit/4cc170055db596cf067a69d4b56d14f829e6f562))


## v0.5.2 (2025-12-02)

### Bug Fixes

- Symlink to tool install dir instead of uvx cache
  ([`9b9a617`](https://github.com/wpfleger96/ai-rules/commit/9b9a61730912c7378178d6db7c5b338a4481f149))

### Continuous Integration

- Fix publish workflow not running
  ([`3e184d6`](https://github.com/wpfleger96/ai-rules/commit/3e184d6c6fde4a1983a3929d2106ef3d0a1107ef))


## v0.5.1 (2025-12-02)

### Bug Fixes

- Test failures in CI and cleanup
  ([`02211d3`](https://github.com/wpfleger96/ai-rules/commit/02211d3c20c52825af0f9aacf2b90e22aa7fed04))

### Chores

- Add AGENTS.md for project
  ([`b871ea8`](https://github.com/wpfleger96/ai-rules/commit/b871ea8f52177c2c92adadeec50c39d364826b66))


## v0.5.0 (2025-12-02)

### Bug Fixes

- Make sure config files get built into wheel package
  ([`3c92f88`](https://github.com/wpfleger96/ai-rules/commit/3c92f88744705168af7a34ee650cd9be519da430))

### Continuous Integration

- Enable ad-hoc runs of publish workflow
  ([`4388662`](https://github.com/wpfleger96/ai-rules/commit/43886624aca953c8bf6f17bbbc368f08269382f9))

- Fix publish workflow bug
  ([`f09ab45`](https://github.com/wpfleger96/ai-rules/commit/f09ab455e7e6f89dc3db2a83028611aedf17482b))

### Features

- Show full diff for stale cache
  ([`cffabd8`](https://github.com/wpfleger96/ai-rules/commit/cffabd827e9adedc875c1f73a2796fc8aa132ae5))


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
