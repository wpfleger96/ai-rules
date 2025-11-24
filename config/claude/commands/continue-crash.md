---
description: Continues after a session crash while working on a task
model: inherit
---

## Context

- Git status: !`git status --porcelain 2>/dev/null | head -20 || echo "NOT_IN_GIT"`
- Recent commits: !`git log --oneline -5 2>/dev/null || echo "NO_COMMITS"`
- Modified files: !`git diff --name-only 2>/dev/null | head -10 || echo "NONE"`
- Current branch: !`git branch --show-current 2>/dev/null || echo "UNKNOWN"`
- TODO files: !`ls -la PLAN__*.md TODO.md 2>/dev/null || echo "No TODO files found"`

# Continue After Crash

Our session crashed. Use the context above to recover and continue where we left off.

## Recovery Process

1. **Analyze context** from pre-executed commands above:
   - Review git status to see uncommitted work
   - Check recent commits to understand what was completed
   - Look for TODO/PLAN files documenting the task

2. **Reconstruct and resume**:
   - Identify the task from the evidence
   - Create or update TODO list based on actual progress
   - Fix any test failures before continuing
   - Continue from the interruption point

## Important

- Base reconstruction only on the evidence provided in Context
- If context is unclear from the data above, ask for clarification
- Don't duplicate completed work - verify what's done in git history
- Maintain the original task direction and intent

Resume work from where it was interrupted.
