---
description: Remove unnecessary code comments that explain WHAT instead of WHY
allowed-tools: AskUserQuestion, Bash, Edit, Glob, Grep, Read, TodoWrite, Write
model: sonnet
---

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || pwd`
- Primary languages: !`find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.rb" -o -name "*.rs" \) 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -nr | head -5`
- Test files count: !`find . -type f \( -name "*test*" -o -name "*spec*" \) 2>/dev/null | wc -l`
- Total comment lines: !`grep -r "^\s*\(//\|#\|/\*\)" --include="*.js" --include="*.ts" --include="*.py" --include="*.go" 2>/dev/null | wc -l`
- Build/Test command: !`[ -f package.json ] && echo "npm" || [ -f Makefile ] && echo "make" || [ -f pyproject.toml ] && echo "pytest" || echo "unknown"`

# Comment Cleanup

Perform comprehensive cleanup of unnecessary code comments across the codebase, removing comments that explain WHAT the code does (when self-evident) rather than WHY certain decisions were made.

## Decision Framework

For each comment encountered, apply this evaluation in order:

1. **Is it a preserved type?** (Shebang, linter directive, TODO/FIXME, docstring) → **KEEP**
2. **Does it explain WHY?** (Rationale, workaround, warning, performance note) → **KEEP**
3. **Does it explain WHAT?** (Organizational, obvious, implementation detail) → **REMOVE**
4. **Would removing make code harder to maintain?** → **KEEP**

## What to Remove

**Organizational comments**: Section dividers
```python
# --- User Management Functions ---
# Database Operations
```

**Obvious comments**: Restating the code
```javascript
// Create config
const config = createConfig();
// Check if path exists
if (!pathExists(path)) return false;
```

**Implementation detail comments**: Explaining how when it's clear
```go
// Try exact match first
if val, ok := map[key]; ok { return val }
```

**Trivial test comments**: Stating the obvious
```python
# Should be parsed as integer
assert isinstance(result, int)
```

## What to Preserve

**WHY comments**: Explaining decisions, workarounds, warnings
```javascript
// Use deep copy to prevent mutation of shared state object
const result = deepCopy(baseObject);

// Workaround for IE11 - doesn't support fetch API
if (!window.fetch) return xhrRequest(url);

// PERF: Cache compiled regex to avoid recompilation on every call
const cachedPattern = /^[a-z]+$/i;
```

**Documentation comments**: Function/class docs (docstrings, JSDoc, JavaDoc, etc.)

**Directives**: Shebangs (`#!/usr/bin/env`), linter configs (`eslint-disable`, `noqa`, `@ts-ignore`, `#pragma`)

**Action items**: TODO, FIXME, HACK, NOTE with context

## Systematic Process

### Step 1: Prioritized Search Strategy

Use the language information from Context above to focus your search. Map comment patterns by language:
- **JavaScript/TypeScript**: `//`, `/* */`, `/** */` (preserve JSDoc)
- **Python**: `#`, `"""`, `'''` (preserve docstrings)
- **Go**: `//`, `/* */`
- **Shell/Bash**: `#` (preserve shebangs)
- **Ruby**: `#`, `=begin`/`=end`
- **Rust**: `//`, `/* */`, `///` (preserve doc comments)

### Step 2: Execute Search

**Start with highest-density areas** (most trivial comments):
1. Test files (`*_test.*`, `test_*.py`, `*.spec.*`)
2. Implementation files in `src/`, `lib/`, `pkg/`
3. Configuration files

**Search commands** by language:
```bash
# JavaScript/TypeScript
rg "^\s*//" --type js --type ts src/ tests/

# Python
rg "^\s*#(?!\s*(?:!/|pragma|noqa|type:))" --type py

# Multiple languages
rg "^\s*(?://|#)" src/ tests/ --glob '!*.{md,txt}'
```

### Step 3: Review & Categorize

For each file with comments:
1. Apply decision framework to each comment
2. Mark comments for removal vs preservation
3. Look for patterns (e.g., all section dividers)
4. Consider batch removal for repeated trivial patterns

### Step 4: Execute Removals

- Use Edit tool for targeted comment removal
- Maintain code structure and intentional blank lines
- Process files systematically (test files first)
- Keep running count of removals

### Step 5: Validation

Run validation checks:
```bash
# Run tests
npm test  # or pytest, go test, cargo test, etc.

# Run linter/formatter
npm run lint  # or ruff check, golangci-lint, etc.

# Verify no trivial comments remain
rg "^\s*(?://|#)\s*(?:Create|Check|Set|Get|Return|Loop)" src/
```

## Success Criteria

✓ All trivial/obvious comments removed
✓ Code remains self-documenting through clear naming
✓ All tests pass without modification
✓ Linter checks pass
✓ Only WHY comments remain (if any)
✓ Test execution time unchanged
✓ Code coverage metrics maintained

## Common Pitfalls to Avoid

- **Don't remove error suppression**: `// @ts-ignore`, `// eslint-disable`, `# noqa`
- **Don't remove type hints**: `# type: ignore`, `/** @type {string} */`
- **Don't remove legal/license headers**: Usually at file top
- **Don't remove API documentation**: JSDoc, docstrings, doc comments
- **Do preserve context for workarounds**: Even if explaining WHAT, workarounds need WHY

## Reporting

After completion, provide summary:
- Total comments removed: X
- Files modified: Y
- Comment types preserved: [list]
- Test result: PASS/FAIL
- Next steps if issues found
