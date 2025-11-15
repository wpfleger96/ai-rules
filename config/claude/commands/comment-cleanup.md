---
description: Remove unnecessary code comments that explain WHAT instead of WHY
model: inherit
---

# Comment Cleanup

Perform a comprehensive cleanup of unnecessary code comments across the codebase. Focus on removing comments that explain WHAT the code does (when it's self-evident from the code itself) rather than WHY certain decisions were made.

## What to Remove

Remove these types of comments:
- **Organizational comments**: Section dividers like "// User-level status" or "// Install symlinks"
- **Obvious comments**: Comments that simply restate what the code does (e.g., "// Create config" right before creating a config)
- **Implementation detail comments**: Comments explaining how code works when it's clear from the code (e.g., "// Try exact match first")
- **Trivial test comments**: Comments in tests like "// Should be parsed as integer" or "// Create existing config"

## What to Preserve

Keep these types of content:
- **WHY comments**: Comments explaining architectural decisions, workarounds, or non-obvious reasoning
- **Documentation comments**: Function/class documentation (docstrings, JSDoc, JavaDoc, etc.)
- **Shebangs**: `#!/usr/bin/env` lines and similar interpreter directives
- **Linter directives**: Tool-specific comments (e.g., `eslint-disable`, `prettier-ignore`, `noqa`, `@ts-ignore`, `#pragma`, etc.)
- **TODO/FIXME**: Action items for future work

## Process

1. **Search for comments**:
   - Use grep/search to find all comments in source files
   - Search patterns depend on language (e.g., `//` for C-style, `#` for shell/Python, `<!-- -->` for HTML/XML)
   - Search all code files across language-specific directories (e.g., `src/`, `lib/`, `tests/`, `pkg/`, etc.)
   - Focus on the primary source file extensions for your project's language(s)

2. **Review and categorize**:
   - For each file with comments, determine which are necessary (WHY) vs unnecessary (WHAT)
   - Most comments explaining implementation details should be removed
   - The code itself should be self-documenting through clear naming

3. **Remove unnecessary comments**:
   - Edit files to remove identified comments
   - For files with many trivial comments, consider batch removal
   - Maintain code structure and blank lines

4. **Verify changes**:
   - Run all tests to ensure no regression
   - Run linter/formatter to ensure code quality
   - Confirm that 0 code comments remain (excluding preserved types above)

## Examples

**Remove** (obvious WHAT):
```
// Load user config
const data = loadConfig(configPath);

// Check if path exists
if (!pathExists(path)) {
    return false;
}

// Create new user
user = new User(name, email);
```

**Keep** (explains WHY):
```
// Use deep copy to prevent mutation of the shared state object
const result = deepCopy(baseObject);

// Workaround for legacy browser compatibility - IE11 doesn't support fetch
if (!window.fetch) {
    return xhrRequest(url);
}

// PERF: Cache compiled regex to avoid recompilation on every call
const cachedPattern = /^[a-z]+$/i;
```

## Success Criteria

- All trivial/obvious comments removed
- Code remains self-documenting through clear variable/function names
- All tests pass
- Linter checks pass
- Only WHY comments remain (if any)
