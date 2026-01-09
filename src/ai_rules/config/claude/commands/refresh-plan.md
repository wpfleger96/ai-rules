---
description: Refreshes plan file after session confusion - removes completed items, keeps only TODO
allowed-tools: Bash, Edit, Glob, Grep, Read, TodoWrite
model: inherit
---

## Context

- Plan files: !`ls -t ~/.claude/plans/*.md 2>/dev/null | head -3 || echo "NO_PLAN_FILES"`
- Current plan content: !`cat "$(ls -t ~/.claude/plans/*.md 2>/dev/null | head -1)" 2>/dev/null | head -50 || echo "NO_PLAN_CONTENT"`

# Refresh Plan - Reconcile Completed Work

<critical_context>
You called ExitPlanMode with items that were ALREADY COMPLETED earlier in this session. This happens in long sessions with multiple plan/implement cycles. The plan file contains stale items that should not be presented for approval again.
</critical_context>

## Problem

Your plan file at `~/.claude/plans/` contains items already done. Each ExitPlanMode call should only present REMAINING work, not re-list completed items.

## Required Actions

### Step 1: Identify What's Actually Done

Cross-reference these sources to find completed work:

1. **Your TODO list** - items marked `completed` are DONE
2. **Session history** - Edit/Write/Bash tool calls show implementation
3. **Git changes** - `git status` and `git diff` show modified files
4. **User confirmations** - explicit "that's done" or "looks good" responses

### Step 2: Audit Plan Against Reality

Read the plan file (see "Current plan content" above):

| Plan Item | Evidence of Completion | Status |
|-----------|----------------------|--------|
| (list each item) | (tool calls, TODO state, git changes) | DONE or TODO |

### Step 3: Update Plan File

Use Edit tool to modify `~/.claude/plans/*.md`:

**Remove or strike through:**
- Items with clear completion evidence
- Items matching `completed` TODO entries
- Items user confirmed as done

**Keep as-is:**
- Items with no implementation evidence
- Items still marked TODO/pending
- Future work not yet started

### Step 4: Report & Confirm

After updating, tell the user:

```
Removed from plan (already completed):
- [item 1]
- [item 2]

Remaining TODO:
- [item A]
- [item B]

Ready to proceed with remaining work?
```

## Critical Rules

<constraints>
- NEVER present completed work as TODO - wastes user time and causes confusion
- ALWAYS cross-reference TODO list state - it tracks actual session progress
- ALWAYS check git status for implementation evidence
- When completion status is unclear, ASK the user rather than guess
- Each subsequent ExitPlanMode in a session should contain FEWER items, not the same items
</constraints>
