---
description: Remove unnecessary code comments that explain WHAT instead of WHY
model: inherit
---

# Comment Cleanup

Perform a comprehensive cleanup of unnecessary code comments across the codebase. Focus on removing comments that explain WHAT the code does (when it's self-evident from the code itself) rather than WHY certain decisions were made.

## What to Remove

Remove these types of comments:
- **Organizational comments**: Section dividers like "# User-level status" or "# Install symlinks"
- **Obvious comments**: Comments that simply restate what the code does (e.g., "# Create config" right before creating a config)
- **Implementation detail comments**: Comments explaining how code works when it's clear from the code (e.g., "# Try exact match first")
- **Trivial test comments**: Comments in tests like "# Should be parsed as integer" or "# Create existing config"

## What to Preserve

Keep these types of content:
- **WHY comments**: Comments explaining architectural decisions, workarounds, or non-obvious reasoning
- **Docstrings**: All triple-quoted function/class documentation
- **Shebangs**: `#!/usr/bin/env python` and similar
- **Linter directives**: Comments like `# type:`, `# noqa`, `# pragma:`, `# fmt:`, `# pylint:`, `# mypy:`
- **TODO/FIXME**: Action items for future work

## Process

1. **Search for comments**:
   - Use grep/search to find all comments in source files
   - Pattern: `^\s*#` (lines starting with #, with optional whitespace)
   - Search Python files: `*.py` in `src/`, `tests/`, etc.

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
```python
# Load user config
with open(config_path) as f:
    data = yaml.load(f)

# Check if path exists
if not path.exists():
    return False
```

**Keep** (explains WHY):
```python
# Use deep copy to prevent mutation of the base dictionary
result = copy.deepcopy(base)

# Workaround for Python 3.8 compatibility issue with pathlib
if sys.version_info < (3, 9):
    path = Path(str(path))
```

## Success Criteria

- All trivial/obvious comments removed
- Code remains self-documenting through clear variable/function names
- All tests pass
- Linter checks pass
- Only WHY comments remain (if any)
