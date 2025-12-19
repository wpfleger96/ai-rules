---
description: Automatically updates project documentation by analyzing recent commits and detecting changes
allowed-tools: AskUserQuestion, Bash, Edit, Glob, Grep, Read, TodoWrite, Write
model: sonnet
---

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || pwd`
- Current branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "NO_BRANCH"`
- Recent commits: !`git log --oneline -10 2>/dev/null || echo "NO_COMMITS"`
- Documentation files: !`find . -maxdepth 3 -type f \( -name "README*" -o -name "ARCHITECTURE*" -o -name "CONTRIBUTING*" \) 2>/dev/null | head -10`
- Last commit message: !`git log -1 --format="%s" 2>/dev/null || echo "NO_COMMITS"`

# Update Project Documentation

**Usage:**
- `/update-docs` - Analyze recent commits and update all relevant documentation

Automatically updates project documentation after code changes by intelligently analyzing recent commits, detecting what changed, and updating relevant documentation files while preserving existing style and structure.

## Six-Phase Methodology

### Phase 0: Invoke doc-writer Skill

**REQUIRED FIRST STEP:** Before proceeding, invoke the `doc-writer` skill using the Skill tool.

**Why:** This command updates technical documentation. Applying doc-writer best practices ensures updates are concise, scannable, and maintain documentation quality.

**Apply these principles from the skill:**
- Compact over comprehensive (every sentence earns its place)
- Readers scan, not read (front-load key info)
- Code examples over prose where applicable
- Cut ruthlessly (no placeholders, no redundant sections)
- Match existing style while improving clarity

### Phase 1: Change Analysis & Scope Detection

**Explore recent commit history:**
1. Review "Recent commits" from Context above
2. Identify the most recent logical grouping of related changes

**Commit Grouping Heuristics:**

Use these indicators to determine which commits form a cohesive logical unit:

**Related commits (include in same group):**
- Commit messages with same feature prefix (e.g., "add auth flow", "fix auth bug", "test auth")
- High file overlap (>50% of changed files appear in multiple commits)
- Temporal proximity (commits within same day or few hours)
- Sequential references to same feature, issue number, or component

**Separate logical units (stop grouping):**
- Different feature/component prefixes in messages
- No file overlap between commits
- Large time gaps (days or weeks apart)
- Clearly distinct functional areas

**Example decision:**
```
Commits:
1. "add config set-default-profile command" (1h ago, modified: cli.py, config.py)
2. "add config file persistence" (50min ago, modified: config.py, README.md)
3. "add tests for default profile" (45min ago, modified: test_config.py)
4. "fix typo in help text" (40min ago, modified: cli.py)
5. "update dependencies" (2 days ago, modified: requirements.txt)

→ Group commits 1-4 as "default profile feature"
→ Exclude commit 5 (different feature, time gap)
```

**Analyze combined changes:**

Once scope determined, get full diff for the commit group:
```bash
# For single commit
git show <commit-hash>

# For multiple commits (e.g., last 4)
git log -4 --format="%h %s"
git diff HEAD~4..HEAD
```

**Detect change patterns using this table:**

| Pattern in Code | Feature Type | Documentation Impact |
|-----------------|--------------|---------------------|
| `@click.command()`, `@app.command()` | CLI command | CLI reference, examples |
| `argparse.add_argument()`, `add_parser()` | CLI argument | CLI reference, usage |
| `@app.route()`, `@router.get()` | API endpoint | API reference, integration guide |
| `FastAPI()`, `APIRouter()` | API changes | API docs, OpenAPI spec |
| Function signature changed | Breaking change | Migration guide, changelog |
| New YAML/TOML/JSON keys in schema | Configuration | Config reference, examples |
| `deprecated`, `@deprecated` | Deprecation | Deprecation notice, migration path |
| New class in public API | New feature | API reference, examples |
| Removed public function/class | Breaking change | Migration guide, what to use instead |

**Parse commit messages for type:**
- `feat:`, "add", "implement", "create" → New feature
- `fix:`, "bug", "resolve", "patch" → Bug fix
- `refactor:`, "restructure", "clean up" → Refactoring
- `breaking:`, "BREAKING CHANGE:" → Breaking change
- `docs:` → Documentation only (skip updating docs for docs changes)

### Phase 2: Documentation Discovery

**Auto-discover documentation files:**

Search for documentation using these patterns (prioritized):

1. **Root-level user docs** (highest priority):
   - `README.md`, `README.rst`, `README.txt`
   - `GETTING_STARTED.md`, `QUICKSTART.md`

2. **Root-level developer docs**:
   - `ARCHITECTURE.md`, `DESIGN.md`
   - `CONTRIBUTING.md`, `DEVELOPMENT.md`
   - `CHANGELOG.md`, `CHANGES.md`

3. **Documentation directories**:
   - `docs/*.md`, `doc/*.md`
   - `docs/api/*.md`, `docs/cli/*.md`
   - `.github/*.md`

4. **Project-specific** (if they exist):
   - `PLAN*.md` (but check if used for development planning)
   - Any files mentioned in commit messages

**Check Context above for "Documentation files"** - these are pre-discovered.

**Prioritize by documentation type:**
1. User-facing (README, getting started) - most critical
2. CLI/API reference sections - document interfaces
3. Developer docs (ARCHITECTURE, CONTRIBUTING) - technical details
4. Examples and tutorials - illustrate usage

### Phase 3: Impact Analysis

**Map detected changes to documentation sections:**

Use this decision table to determine what needs updating:

| Change Type | README | ARCHITECTURE | CONTRIBUTING | docs/ | Priority |
|-------------|--------|--------------|--------------|-------|----------|
| New CLI command | CLI reference, Quick start | - | - | CLI guide | CRITICAL |
| New CLI argument | CLI reference, Usage | - | - | CLI guide | CRITICAL |
| New API endpoint | API overview | API architecture | - | API reference | CRITICAL |
| Breaking change | Upgrade notes, Breaking changes section | System changes | - | Migration guide | CRITICAL |
| New config option | Configuration section | Config system | - | Config reference | IMPORTANT |
| Deprecated feature | Deprecation notice | - | - | Migration guide | IMPORTANT |
| Performance improvement | Changelog, Performance section | Implementation | - | - | IMPORTANT |
| Bug fix (behavior change) | Changelog | - | - | - | IMPORTANT |
| Bug fix (no behavior change) | Changelog only | - | - | - | SKIP |
| Internal refactor | - | - | - | - | SKIP |

**Build update plan:**
1. List all documentation files needing updates
2. For each file, identify specific sections to modify
3. Prioritize by CRITICAL → IMPORTANT → SKIP

### Phase 4: Style-Preserving Documentation Updates

**Before making any changes:**

For each documentation file to update:

1. **Analyze existing style** (read first 500 lines):
   - Tone: Formal/technical vs casual/accessible
   - Structure: Heading levels (# ## ###), section organization
   - Formatting: Code block language tags, list style (-, *, 1.), table usage
   - Example patterns: Inline examples vs separate files, comment style in code blocks

2. **Identify update strategy**:
   - **Insert**: Add new section for new feature (preserve structure)
   - **Update**: Modify existing section (match formatting)
   - **Append**: Add to list (match list style: -, *, or numbered)
   - **Replace**: Outdated info (preserve tone and format)

**Make minimal invasive edits:**

For each update, use the Edit tool to:
- Insert new content into existing sections (don't restructure)
- Update examples to match new behavior (preserve example format)
- Preserve cross-references and internal links
- Match existing writing style, tone, and voice
- Keep same heading hierarchy and conventions

**Examples of style matching:**

```markdown
# Existing style (casual, emoji, short sentences)
## Commands

Use these commands:
- 🚀 `app start` - Start the app
- 🛑 `app stop` - Stop it

# Match this style when adding:
- ⚙️ `app config` - Configure settings
```

```markdown
# Existing style (formal, technical, detailed)
### Command Reference

#### start
Initializes the application server and begins listening for incoming requests on the configured port (default: 8080).

# Match this style when adding:
#### configure
Modifies application configuration settings, persisting changes to the local configuration file (~/.app/config.toml). Accepts key-value pairs via command-line arguments.
```

**What NOT to do:**
- Don't add features not requested or clearly necessary
- Don't restructure existing documentation
- Don't change the tone (formal → casual or vice versa)
- Don't add verbose descriptions if existing docs are concise
- Don't remove existing content unless it's deprecated/wrong

### Phase 5: Verification & Summary

**Verify completeness:**

After all updates, check:
- [ ] All significant changes from Phase 1 are documented
- [ ] Deprecated features removed or marked as deprecated
- [ ] All examples updated to match new behavior
- [ ] Cross-references still valid (no broken links to removed sections)
- [ ] Consistent style maintained throughout each file
- [ ] No orphaned sections (sections referencing removed features)

**Generate summary report:**

Provide user with:
```
Documentation Updated - Summary

Scope Analyzed:
- Commits: <N> commits from <oldest> to <newest>
- Feature: <brief description of logical grouping>
- Changes detected: <list of key changes>

Files Updated:
- <file1>: <what was updated>
- <file2>: <what was updated>

Verification:
✓ All new features documented
✓ Examples updated
✓ Style preserved
✓ Cross-references valid

Review changes: git diff
```

## Prioritization Framework

Use this framework to decide what to document:

**Critical (Must Document)**:
- New user-facing features (CLI commands, API endpoints)
- Breaking changes requiring migration
- Security-related changes (authentication, authorization, data handling)
- Changed behavior for existing features
- New required configuration

**Important (Should Document)**:
- New optional configuration
- Performance improvements with visible user impact
- Behavior-changing bug fixes (even if fixing a bug)
- New developer-facing features (build tools, dev commands)
- Enhanced error messages that users will see

**Skip (Don't Document)**:
- Internal refactoring with no external impact
- Test additions or modifications
- Code style or formatting changes
- Dependency updates (unless they cause breaking changes)
- Trivial bug fixes (typos, off-by-one with no behavior change)
- Documentation-only changes (don't update docs for docs commits)

## Critical Requirements

**Change Detection:**
- Explore recent commits to identify logical grouping (not just HEAD)
- Use commit message patterns, file overlap, and timestamps
- Make autonomous decision about scope
- Analyze combined diff for the identified group

**Documentation Discovery:**
- Auto-discover using intelligent patterns (README*, ARCHITECTURE*, docs/)
- Check pre-executed Context for available files
- Prioritize user-facing docs > API/CLI reference > developer docs

**Style Preservation:**
- **ALWAYS** analyze existing style before updating
- **MUST** match tone (formal vs casual)
- **MUST** preserve formatting (code blocks, lists, tables)
- **MUST** maintain heading hierarchy
- Make minimal invasive changes only

**Update Strategy:**
- Use Edit tool with exact string matching
- Insert into existing sections (don't restructure)
- Update examples in-place (preserve format)
- Remove deprecated content explicitly

**Accuracy:**
- Base all updates on actual code changes (git diff)
- Don't guess or fabricate features
- Include concrete technical details (function names, command syntax)
- Verify examples match actual implementation

**Completeness:**
- Document all CRITICAL changes (user-facing features, breaking changes)
- Document IMPORTANT changes (config, behavior changes)
- Skip internal changes with no external impact
- Generate verification summary for user

**DO:**
- Analyze commit history to find logical groupings
- Detect changes using pattern matching table
- Preserve existing documentation style and tone
- Make minimal edits (insert into existing structure)
- Update all examples affected by changes
- Report what was changed in final summary

**DO NOT:**
- Rigidly analyze only HEAD commit (explore recent history)
- Restructure existing documentation
- Change tone or writing style
- Add features or improvements beyond what changed
- Skip documenting breaking changes or new user features
- Remove content without confirming it's deprecated

Your goal is to keep documentation accurate and up-to-date with code changes while respecting project conventions and minimizing disruption to existing docs structure.
