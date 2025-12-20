---
description: Creates or updates AGENTS.md with comprehensive repo documentation for LLM coding agents
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, TodoWrite
model: sonnet
---

## Context

- Mode: !`[ -f "$(git rev-parse --show-toplevel 2>/dev/null)/AGENTS.md" ] && echo "UPDATE_MODE" || echo "CREATE_MODE"`
- Git root: !`git rev-parse --show-toplevel 2>/dev/null || echo "NOT_IN_GIT_REPO"`
- Project name: !`sh -c 'ROOT=$(git rev-parse --show-toplevel 2>/dev/null); [ -z "$ROOT" ] && echo "UNKNOWN" || (cd "$ROOT" && (grep -m1 "name" package.json 2>/dev/null | sed -E "s/.*\"name\"[[:space:]]*:[[:space:]]*\"([^\"]+)\".*/\\1/" || grep -m1 "^name = " pyproject.toml 2>/dev/null | sed -E "s/name = \"([^\"]+)\"/\\1/" || grep -m1 "^name = " Cargo.toml 2>/dev/null | sed -E "s/name = \"([^\"]+)\"/\\1/" || basename "$ROOT"))'`
- Tooling: !`sh -c 'ROOT=$(git rev-parse --show-toplevel 2>/dev/null); [ -z "$ROOT" ] && echo "NONE" || (cd "$ROOT" && tools=""; [ -f Makefile ] && tools="${tools}make,"; [ -f Justfile ] && tools="${tools}just,"; [ -f package.json ] && tools="${tools}npm,"; [ -f pyproject.toml ] && tools="${tools}python,"; [ -f Cargo.toml ] && tools="${tools}rust,"; [ -f go.mod ] && tools="${tools}go,"; echo "${tools%,}" | sed "s/^$/NONE/")'`
- Primary language: !`sh -c 'ROOT=$(git rev-parse --show-toplevel 2>/dev/null); [ -z "$ROOT" ] && echo "UNKNOWN" || (cd "$ROOT" && (find . -type f -name "*.py" 2>/dev/null | head -1 | grep -q . && echo "Python") || (find . -type f -name "*.js" -o -name "*.ts" 2>/dev/null | head -1 | grep -q . && echo "JavaScript/TypeScript") || (find . -type f -name "*.rs" 2>/dev/null | head -1 | grep -q . && echo "Rust") || (find . -type f -name "*.go" 2>/dev/null | head -1 | grep -q . && echo "Go") || echo "UNKNOWN")'`

# Create or Update AGENTS.md

You are creating documentation to help LLM coding agents work effectively in this repository. Discover and document everything an agent needs: commands, structure, patterns, gotchas, conventions.

**Target audience:** LLM agents starting fresh
**Output:** AGENTS.md at repository root
**Quality:** Under 100 lines, actionable, specific

## Phase 0: Invoke prompt-engineer Skill

**REQUIRED FIRST STEP:** Invoke `prompt-engineer` skill using Skill tool.

**Why:** AGENTS.md is for LLM agents. Applying prompt engineering ensures maximal effectiveness: explicit instructions, important info first (primacy bias), specific over vague ("pytest -v" not "run tests"), examples over explanations.

## Phase 1: Determine Mode

Check "Mode" from Context:

**CREATE_MODE:** AGENTS.md doesn't exist. Inform user you're creating for `{Project name}`, proceed to Phase 2.

**UPDATE_MODE:** AGENTS.md exists. Inform user you're updating, read current file, proceed to Phase 2 (focus on changes/additions).

## Phase 2: Systematic Exploration

Explore repository across all key areas. Use findings to populate AGENTS.md sections.

### Essential Discovery Checklist

**1. Commands (PRIORITY - Document First)**
- Check `Makefile` (`make help`, `grep "^[a-zA-Z]" Makefile`), `Justfile` (`just --list`), `package.json` (scripts), `pyproject.toml` (tool commands)
- Read README.md for Getting Started/Development sections
- Check CI config (.github/workflows/) for canonical commands
- **Document:** Setup, build, run, test (full + file-scoped), lint, format, type check

**2. Project Identity**
- Read README.md for description
- Check package files for name/version/description
- Identify type: library, CLI, web app, service

**3. Project Structure**
- Run `tree -d -L 3` or `ls -R`
- Identify: source (`src/`, `lib/`), tests (`tests/`, `__tests__`), config, docs
- Note monorepo structure if applicable

**4. Tech Stack**
- Language + version
- Framework + major version (React 18, Django 4, etc.)
- Key libraries/dependencies
- Database (check docker-compose.yml, .env examples)
- Build tools, package manager

**5. Key Patterns & Conventions**
- Read 2-3 source files for architecture patterns (MVC, components, services)
- File naming conventions (camelCase, snake_case, test_*.py)
- Import/export patterns
- Base classes/utilities to use

**6. Testing**
- Framework (pytest, jest, vitest, go test)
- Test locations/naming
- Commands: full suite, single file, watch, coverage
- Check CI for test commands

**7. Common Gotchas (HIGH VALUE)**
- Search comments with "NOTE:", "WARNING:", "FIXME:", "HACK:"
- Read existing AGENTS.md/CLAUDE.md for gotchas
- Complex setup (env vars, secrets, external services)
- Version-specific issues
- Git hooks/pre-commit config

**Examples:** "Array path: Use `hooks.Stop[0].cmd` for arrays" | "Mock HOME needs both environ and Path.home patches" | "Run `make migrate-test` before tests"

**8. Key Files by Task**
- Map tasks to files: Add CLI command → which files? | Add API endpoint → which files? | Add component → which files? | Change config → which files?

## Phase 3: Write AGENTS.md

**Structure (under 100 lines total):**

```markdown
# AGENTS.md

[1-2 sentence project description]

## Quick Commands

```bash
# Setup
[commands]

# Development
[build/run/test/lint/format commands]
```

## Project Structure

```
[Directory tree with annotations]
```

## Tech Stack

- [Language + version]
- [Framework + version]
- [Key libraries]
- [Database if applicable]

## Key Patterns

[Conventions, abstractions, architectural patterns - brief with code examples if helpful]

## Testing

```bash
[Test commands]
```

[Test structure notes]

## Common Gotchas

1. [Gotcha with specific details]
2. [Another gotcha]
...

## Key Files by Task

| Task | Files |
|------|-------|
[Task-to-file mapping]
```

**Quality Standards:**
- **Concise:** Under 100 lines (60 ideal, complex repos up to 100)
- **Specific:** Include versions ("React 18"), exact commands (`pytest -v`), actual paths (`src/cli.py`)
- **Examples over prose:** `user_email = get_email()  # Not: e = get_email()`
- **Commands first:** Most used, put early
- **No sensitive info:** No API keys, credentials, tokens

**Optional Boundaries Section (if critical constraints exist):**
```markdown
## Boundaries

**Always:** Run tests before commit | Use existing components from src/components/
**Ask first:** Adding dependencies | Schema changes
**Never:** Commit secrets | Delete tests without replacement
```

## Phase 4: File Operations

### CREATE_MODE
1. Generate complete AGENTS.md
2. Write to `{Git root}/AGENTS.md`
3. Validate: <100 lines, commands first, specific versions, all sections populated, no secrets
4. Report: file path, line count, key sections

### UPDATE_MODE
1. Compare existing vs new findings
2. **Merge:** Preserve user customizations | Add new findings | Update outdated info | Don't remove user content unless obsolete
3. Use Edit tool with exact old_string matching
4. Report: file path, what was added/updated, summary of changes

## Critical Requirements

**File Location:** ALWAYS `{Git root}/AGENTS.md` (root-level only, never subdirectories)

**Exploration:** READ actual files (don't guess), run commands (make --help, just --list), check multiple sources, prefer CI config for canonical commands

**Content:** Specific > vague | Actionable > descriptive | Examples > explanations | Brief > comprehensive | Accurate > complete

**Avoid:** Sensitive info | Duplicating linter rules | Generic advice ("write good code") | Personal opinions | Unnecessary prose

**Update Mode:** Preserve user customizations | Don't remove manual additions | Only update what changed | Maintain user's organizational preferences

**This is for LLM agents, not humans.** Focus on info NOT in README. Commands most important (put first). Gotchas high-value (prominent section).

Your AGENTS.md should enable any LLM coding agent to start contributing within minutes.
