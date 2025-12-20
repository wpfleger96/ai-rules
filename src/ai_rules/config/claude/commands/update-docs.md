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
- Last commit: !`git log -1 --format="%s" 2>/dev/null || echo "NO_COMMITS"`

# Update Project Documentation

**Usage:** `/update-docs` - Analyze recent commits and update relevant documentation

Automatically updates documentation after code changes by analyzing commits, detecting what changed, and updating docs while preserving existing style.

## Phase 0: Invoke doc-writer Skill

**REQUIRED FIRST STEP:** Invoke `doc-writer` skill using Skill tool.

**Apply principles:** Compact over comprehensive | Readers scan (front-load key info) | Code examples > prose | Cut ruthlessly | Match existing style

## Phase 1: Change Analysis

### Determine Scope
Review "Recent commits" from Context. Group related commits by:
- **Related:** Same feature prefix ("add auth", "fix auth", "test auth"), high file overlap (>50%), temporal proximity (hours/days), same issue number
- **Separate:** Different prefixes, no file overlap, large time gaps, distinct areas

**Example:** Commits 1-4 ("add config", "persist config", "test config", "fix typo" within hours) = group. Commit 5 ("update deps" 2 days ago) = exclude.

### Analyze Changes
```bash
git log -N --format="%h %s"  # N = grouped commit count
git diff HEAD~N..HEAD --stat
git diff HEAD~N..HEAD
```

### Detect Patterns
| Code Pattern | Feature | Docs Impact |
|--------------|---------|-------------|
| `@click.command()`, `@app.command()` | CLI command | CLI reference, examples |
| `@app.route()`, `@router.get()` | API endpoint | API reference, integration |
| Function signature changed | Breaking change | Migration guide |
| New YAML/JSON keys | Config option | Config reference |
| `deprecated`, `@deprecated` | Deprecation | Migration path |
| Removed public function | Breaking change | Migration guide |

### Classify PR Type
**Match commits to:** feat/add → New feature | fix/bug → Bug fix | refactor → Refactor | docs → Skip (docs only) | breaking/BREAKING CHANGE → Breaking change

## Phase 2: Documentation Discovery

**Search for docs (prioritized):**
1. Root user docs: README.md, GETTING_STARTED.md, QUICKSTART.md
2. Root dev docs: ARCHITECTURE.md, CONTRIBUTING.md, CHANGELOG.md
3. Docs directories: docs/*.md, docs/api/*.md, docs/cli/*.md
4. Project-specific: Check commits for mentioned files

**Check Context "Documentation files"** for pre-discovered files.

## Phase 3: Impact Analysis

Map changes to documentation sections:

| Change | README | ARCHITECTURE | CONTRIBUTING | docs/ | Priority |
|--------|--------|--------------|--------------|-------|----------|
| New CLI command/arg | CLI ref, Quick start | - | - | CLI guide | CRITICAL |
| New API endpoint | API overview | API arch | - | API ref | CRITICAL |
| Breaking change | Breaking section | System changes | - | Migration | CRITICAL |
| New config option | Configuration | Config system | - | Config ref | IMPORTANT |
| Deprecated feature | Deprecation notice | - | - | Migration | IMPORTANT |
| Bug fix (behavior change) | Changelog | - | - | - | IMPORTANT |
| Internal refactor / trivial fix | - | - | - | - | SKIP |

**Build update plan:** List files + sections to modify, prioritize CRITICAL → IMPORTANT → SKIP.

## Phase 4: Update Documentation

**For each file to update:**

1. **Analyze existing style** (read first 500 lines):
   - Tone: Formal/technical vs casual/accessible
   - Structure: Heading levels, section organization
   - Formatting: Code blocks, list style (-, *, 1.), tables
   - Examples: Inline vs separate, comment style

2. **Update strategy:**
   - **Insert:** New section for new feature
   - **Update:** Modify existing section
   - **Append:** Add to list (match style: -, *, or numbered)
   - **Replace:** Outdated info

3. **Make minimal edits:**
   - Insert into existing sections (don't restructure)
   - Update examples to match new behavior (preserve format)
   - Preserve cross-references and links
   - Match existing tone/voice
   - Keep heading hierarchy

**Example - Match existing style:**
If existing style is casual with emoji:
```markdown
- 🚀 `app start` - Start the app
```
Match it:
```markdown
- ⚙️ `app config` - Configure settings
```

If formal/technical:
```markdown
#### configure
Modifies configuration settings, persisting to ~/.app/config.toml.
```

**Don't:** Add unasked features | Restructure docs | Change tone | Add verbose descriptions if docs are concise | Remove content unless deprecated/wrong

## Phase 5: Verification & Summary

**Verify:**
- All significant changes documented
- Deprecated features marked
- Examples updated to match new behavior
- Cross-references valid
- Style consistent

**Generate summary:**
```
Documentation Updated

Scope: N commits from <oldest> to <newest>
Feature: <brief description>
Changes: <key changes list>

Files Updated:
- <file1>: <what changed>
- <file2>: <what changed>

✓ New features documented
✓ Examples updated
✓ Style preserved

Review: git diff
```

## Prioritization

**Critical (Must Document):**
- New user-facing features (CLI, API)
- Breaking changes requiring migration
- Security-related changes
- Changed behavior for existing features
- New required configuration

**Important (Should Document):**
- New optional configuration
- Performance improvements with user impact
- Behavior-changing bug fixes
- New dev features (build tools)
- Enhanced error messages

**Skip (Don't Document):**
- Internal refactoring (no external impact)
- Test changes
- Code style/formatting
- Trivial bug fixes (typos, off-by-one no behavior change)
- Documentation-only changes

## Critical Requirements

**Change Detection:** Explore recent commits for logical grouping (not just HEAD) | Use commit patterns, file overlap, timestamps | Analyze combined diff

**Style Preservation:** ALWAYS analyze existing style first | MUST match tone (formal vs casual) | MUST preserve formatting | MUST maintain heading hierarchy | Minimal invasive changes only

**Accuracy:** Base updates on actual code changes (git diff) | Don't guess/fabricate | Include concrete details (function names, command syntax) | Verify examples match implementation

**Completeness:** Document CRITICAL changes (user-facing, breaking) | Document IMPORTANT changes (config, behavior) | Skip internal changes | Generate verification summary

**DO:** Analyze commit history for logical groupings | Detect changes using pattern matching | Preserve docs style/tone | Make minimal edits | Update affected examples | Report changes in summary

**DON'T:** Only analyze HEAD (explore recent history) | Restructure docs | Change tone/style | Add features beyond what changed | Skip breaking changes or new user features | Remove content without confirming deprecated

Keep documentation accurate and up-to-date with code while respecting project conventions and minimizing disruption.
