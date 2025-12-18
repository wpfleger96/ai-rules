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
- Directory: !`pwd`

# Create or Update AGENTS.md

You are creating comprehensive documentation to help LLM coding agents (Claude Code, Cursor, Goose, etc.) work effectively in this repository. Your goal is to discover and document everything an agent needs to understand the project quickly: commands, structure, patterns, gotchas, and conventions.

**Target audience:** LLM coding agents starting fresh on this codebase
**Output:** AGENTS.md file at repository root with actionable, concise guidance

## Phase 0: Invoke prompt-engineer Skill

**REQUIRED FIRST STEP:** Before proceeding, invoke the `prompt-engineer` skill using the Skill tool.

**Why:** AGENTS.md is documentation for LLM coding agents. Applying prompt engineering best practices ensures the output is maximally effective for its audience.

**Apply these principles from the skill:**
- Use explicit, unambiguous instructions (LLMs interpret literally)
- Structure with clear sections and formatting
- Put most important info first (commands) - LLMs have primacy bias
- Be specific over vague ("pytest -v" not "run tests")
- Use examples over explanations where applicable

## Phase 1: Determine Mode

Check the "Mode" field from Context section:

### CREATE_MODE
AGENTS.md does not exist. You will create a new file from scratch by exploring the repository comprehensively.

**Action:**
1. Inform user you're creating AGENTS.md for `{Project name}`
2. Proceed to Phase 2: Deep Exploration

### UPDATE_MODE
AGENTS.md already exists. You will read the existing file, explore for new information, and merge updates while preserving user customizations.

**Action:**
1. Inform user you're updating existing AGENTS.md
2. Read current AGENTS.md file
3. Proceed to Phase 2: Deep Exploration (focusing on changes/additions)

## Phase 2: Deep Exploration

Explore the repository systematically across all key areas. Use the findings to populate AGENTS.md sections.

### Area 1: Project Identity & Overview

**Goal:** Understand what this project is and what it does

**Explore:**
1. Read README.md for project description and purpose
2. Check package files (package.json, pyproject.toml, Cargo.toml, go.mod) for:
   - Official project name
   - Version
   - Description field
   - Main entry points
3. Identify if this is a library, CLI tool, web app, service, or other

**Document in:** Opening paragraph (1-2 sentences)

### Area 2: Quick Commands (PRIORITY: Document First)

**Goal:** Find all essential build/test/run commands

**Explore (in priority order):**

1. **Makefile** (if exists):
   ```bash
   make help  # Try first
   grep "^[a-zA-Z]" Makefile | head -20  # List targets
   ```

2. **Justfile** (if exists):
   ```bash
   just --list
   ```

3. **package.json** (if exists):
   ```bash
   cat package.json | grep -A 50 '"scripts"'
   ```

4. **pyproject.toml** (if exists):
   - Check for tool commands
   - Look for `[tool.pytest]`, `[tool.ruff]`, etc.
   - Common: `pytest`, `ruff check`, `ruff format`, `mypy`

5. **README.md**:
   - Search for "Getting Started", "Installation", "Development"
   - Extract command examples

6. **CI/CD config** (.github/workflows/, .gitlab-ci.yml):
   - Commands used in CI are canonical

**Critical:** Document the ACTUAL commands agents should run:
- Setup/installation
- Build/compile
- Run locally
- Test (full suite AND file-scoped if different)
- Lint
- Format
- Type check

**Document in:** `## Quick Commands` section (put at top, most important)

### Area 3: Project Structure

**Goal:** Map the directory layout and key modules

**Explore:**
1. Run `tree -d -L 3` or `ls -R` to see directory structure
2. Identify key directories:
   - Source code location (src/, lib/, app/, pkg/)
   - Test location (tests/, test/, __tests__)
   - Config location (config/, .config/)
   - Documentation location (docs/, documentation/)
3. For each major directory, understand its purpose
4. Note any monorepo structure (packages/, apps/)

**Document in:** `## Project Structure` section (tree view or annotated list)

### Area 4: Tech Stack

**Goal:** Document specific technologies with versions

**Explore:**
1. Language and version (from package files or README)
2. Framework (React, Django, Express, etc.) with major version
3. Key libraries/dependencies (check package files)
4. Database (if any - check docker-compose.yml, env examples)
5. Build tools (Webpack, Vite, esbuild, etc.)
6. Package manager (npm, yarn, pnpm, uv, cargo, etc.)

**Be specific:** "React 18 with TypeScript" not just "React"

**Document in:** `## Tech Stack` section (bulleted list)

### Area 5: Key Patterns & Conventions

**Goal:** Discover architectural patterns and coding conventions agents must follow

**Explore:**
1. **Architecture patterns:**
   - Read 2-3 example source files
   - Look for: MVC, component patterns, service layers, repository patterns
   - Check for dependency injection, factories, builders

2. **Code organization conventions:**
   - Naming patterns (camelCase, snake_case, PascalCase for what?)
   - File naming (index.js patterns, _private.py, test_*.py)
   - Import/export patterns

3. **Abstractions to use:**
   - Base classes (check for `Base*`, `Abstract*`)
   - Utilities (lib/, utils/, helpers/)
   - Shared components/modules

4. **Framework-specific patterns:**
   - React: Hook patterns, component structure
   - Python: Class decorators, context managers
   - Go: Interface patterns

**Look at real code examples** to understand conventions

**Document in:** `## Key Patterns` section with brief explanations

### Area 6: Code Style

**Goal:** Document style guidelines NOT covered by linters

**Explore:**
1. Check for style guide docs (CONTRIBUTING.md, docs/style.md)
2. Read linter configs (.eslintrc, .ruff.toml, etc.) for what's enforced
3. Look for patterns in existing code:
   - Comment style (docstrings, JSDoc, inline)
   - Function/method length norms
   - Prefer composition or inheritance?

**Important:**
- Only document what linters DON'T catch
- Use code examples over prose when possible
- Keep brief (linters handle most style)

**Document in:** `## Code Style` section (brief, example-focused)

### Area 7: Testing

**Goal:** How to run tests and where they live

**Explore:**
1. Test framework (pytest, vitest, jest, go test, cargo test)
2. Test file locations and naming
3. Test commands:
   - Full suite
   - Single file
   - Watch mode
   - Coverage
4. CI test commands (check .github/workflows/)
5. Test patterns/conventions (fixtures, mocks, factories)

**Document in:** `## Testing` section

### Area 8: Common Gotchas (HIGH VALUE)

**Goal:** Capture edge cases and traps that cause bugs

**Explore:**
1. Check comments with "NOTE:", "WARNING:", "FIXME:", "HACK:"
2. Read existing AGENTS.md, CLAUDE.md, or similar files for gotchas
3. Look for complex setup (environment vars, secrets, external services)
4. Check for version-specific issues (e.g., "Must use Python 3.11+")
5. Review git hooks (.git/hooks/) or pre-commit config
6. Look for common failure modes in issues/PRs if public repo

**Examples of good gotchas:**
- "Array path notation: Use `hooks.SubagentStop[0].command` for setting arrays"
- "Mocking HOME in tests requires patching both environ and Path.home"
- "Must run migrations before tests: `make migrate-test`"

**Document in:** `## Common Gotchas` section (numbered list)

### Area 9: Key Files by Task

**Goal:** Map tasks to relevant files for faster navigation

**Explore:**
1. Identify common tasks based on project type:
   - Add CLI command → which files?
   - Add API endpoint → which files?
   - Add new component → which files?
   - Change config behavior → which files?
   - Add new agent/plugin → which files?

2. Document the mapping as a table

**Document in:** `## Key Files by Task` section (table format)

## Phase 3: Synthesize Findings

Organize your exploration findings into a well-structured AGENTS.md file.

### Structure Requirements

Use this exact structure (based on research of 2,500+ repositories):

```markdown
# AGENTS.md

[1-2 sentence project description from Area 1]

## Quick Commands

```bash
[Commands from Area 2 - setup, build, test, lint, format]
```

## Project Structure

```
[Directory tree from Area 3 with annotations]
```

## Tech Stack

- [Language + version]
- [Framework + version]
- [Key libraries]
- [Build tools]
- [Database if applicable]

## Key Patterns

[Findings from Area 5 - conventions, abstractions, architectural patterns]

## Code Style

[Findings from Area 6 - brief, with code examples if helpful]

## Testing

```bash
[Test commands from Area 7]
```

[Test structure notes]

## Common Gotchas

1. [Gotcha from Area 8]
2. [Another gotcha]
...

## Key Files by Task

| Task | Files |
|------|-------|
[Mapping from Area 9]
```

### Quality Standards

**Conciseness:**
- Target: Under 60 lines total (up to 100 for complex projects)
- Be specific and actionable, avoid prose
- One line per item where possible
- Put commands early (they're used most)

**Specificity:**
- Include version numbers ("React 18" not "React")
- Use exact commands with flags (`pytest -v` not "run tests")
- Reference actual file paths (`src/cli.py` not "CLI file")

**Examples over explanation:**
```markdown
# Bad
"Use meaningful variable names"

# Good
user_email = get_email()  # Not: e = get_email()
```

**Boundaries (Optional but valuable):**
Consider adding a boundaries section if there are critical constraints:
```markdown
## Boundaries

**Always:**
- Run tests before committing
- Use existing components from src/components/

**Ask first:**
- Adding new dependencies
- Database schema changes

**Never:**
- Commit secrets or credentials
- Delete existing tests without replacement
```

## Phase 4: Write or Update File

### For CREATE_MODE

1. **Generate complete AGENTS.md** using structure from Phase 3
2. Write to: `{Git root}/AGENTS.md`
3. **Validate:**
   - File under 100 lines
   - Commands section is first (after overview)
   - Specific versions included
   - All sections have content (no empty placeholders)
   - No sensitive information included

4. **Report to user:**
   - File path
   - Line count
   - Key sections included

### For UPDATE_MODE

1. **Read existing AGENTS.md** (already done in Phase 1)
2. **Compare** existing content vs. new findings:
   - Identify new commands not documented
   - Identify new gotchas discovered
   - Check if versions are outdated
   - Look for structural improvements

3. **Merge strategy:**
   - **Preserve** user customizations and manual additions
   - **Add** new findings to appropriate sections
   - **Update** outdated information (versions, commands)
   - **Don't remove** user content unless clearly obsolete

4. **Apply updates** using Edit tool:
   - Match exact old_string with proper formatting
   - Add new items to lists/sections
   - Update version numbers where stale

5. **Report to user:**
   - File path
   - What was added/updated
   - Summary of changes (X commands added, Y gotchas updated, etc.)

## Critical Requirements

**File Location:**
- ALWAYS write to `{Git root}/AGENTS.md`
- NEVER write to subdirectories (root-level only)
- Confirm git root from Context section

**Exploration Depth:**
- READ actual files, don't guess content
- Run commands to see real output (make --help, just --list, etc.)
- Check multiple sources for same information
- Prefer CI config for canonical commands

**Content Quality:**
- Specific over vague ("pytest -v" not "run tests")
- Actionable over descriptive
- Examples over explanations
- Brief over comprehensive
- Accurate over complete

**Avoid:**
- Sensitive information (API keys, credentials, tokens)
- Duplicating linter rules in Code Style
- Generic advice ("write good code", "test your changes")
- Personal opinions not grounded in codebase
- Unnecessary prose

**Update Mode:**
- Preserve user customizations
- Don't remove manual additions
- Only update what changed
- Maintain user's organizational preferences

**Documentation:**
- This is for LLM agents, not humans
- Focus on information NOT in README
- Commands are most important (put first)
- Gotchas are high-value (include prominent section)

Your AGENTS.md should enable any LLM coding agent to start contributing effectively within minutes of reading it.
