---
description: Creates or updates PLAN.md based on session - auto-detects create vs update mode
allowed-tools: AskUserQuestion, Bash, Edit, Glob, Grep, Read, TodoWrite, Write
model: sonnet
---

## Context

- Project: !`git rev-parse --show-toplevel 2>/dev/null || echo "NOT_IN_GIT_REPO"`
- PLAN files: !`sh -c 'PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); if [ -z "$PROJECT_ROOT" ]; then echo "NOT_IN_GIT_REPO"; exit 0; fi; cd "$PROJECT_ROOT" && for f in PLAN__*.md; do [ -f "$f" ] && echo "$f" && found=1; done; if [ -z "$found" ]; then [ -f PLAN.md ] && echo "LEGACY_PLAN" || echo "NO_PLAN_FILES"; fi' 2>/dev/null | sed 's/PLAN__//;s/\.md$//' | paste -sd ',' -`
- Directory: !`pwd`
- Last commit: !`git log -1 --format="%h %ai %s" 2>/dev/null || echo "NO_COMMITS"`

# Create or Update Development Documentation

Automatically creates task-specific PLAN files (`PLAN__<TASK>.md`) or updates existing ones by analyzing session activity to track implementation progress. Multiple agents can work simultaneously, each with their own per-task plan file.

## Task-Specific PLAN Files

**Purpose:** Single source of truth for plans and progress across sessions, tracking multi-phase work with status indicators

**Naming Convention:**
- Format: `PLAN__<TASK>.md` (always `PLAN__` with two underscores)
- Task identifier: 1-2 words, uppercase letters only, single underscores between words
- Valid: ✓ `AUTH_FLOW`, ✓ `API_MIGRATION`, ✓ `SLACK_FORMATTING`
- Invalid: ✗ `auth_flow` (lowercase), ✗ `AUTH__FLOW` (double underscore), ✗ `TOO_MANY_WORDS` (>2 words)

## CRITICAL: File Location

**ALWAYS write PLAN files to the git repository root, NEVER to ~/.claude/plans/**

- Target path: `{git_root}/PLAN__<TASK>.md` (e.g., `/Users/user/project/PLAN__AUTH_FLOW.md`)
- Claude Code has an internal plan mode that uses `~/.claude/plans/` - this is SEPARATE and UNRELATED
- If you see a path containing `~/.claude/plans/`, you are using the WRONG location
- The `/dev-docs` command manages repository-local documentation, not Claude Code internals

## Phase 1: Determine Mode

Use pre-executed context to determine mode:

**Check "PLAN files" from Context:**
- `NO_PLAN_FILES` → **Create mode**: Extract plan from ExitPlanMode, generate task name
- `LEGACY_PLAN` → **Legacy migration**: Rename PLAN.md to PLAN__<TASK>.md, continue as update
- Single task (e.g., `AUTH_FLOW`) → **Update mode**: Work with that specific file
- Multiple tasks (e.g., `AUTH_FLOW,API_MIGRATION`) → **Disambiguate**: Determine which task or create new

**Legacy Migration:**
1. Read `PLAN.md`, extract main task theme
2. Generate task name (1-2 uppercase words with underscores)
3. Rename: `mv PLAN.md PLAN__<TASK>.md`
4. Continue as update mode

**Disambiguate (multiple PLAN files):**
1. List available tasks
2. Search recent ExitPlanMode/Write/Edit/TodoWrite for context clues
3. If clear match → proceed with that task
4. If ambiguous → ask user which task to update or create new

## Phase 2: Extract Plan & Evidence

### For Create Mode

⚠️ **ANTI-RECENCY BIAS WARNING**: Recent work dominates attention. The FIRST ExitPlanMode typically has the complete vision. Later calls often refine/narrow focus. You MUST document ALL work (completed, current, AND future).

**Extract plans:**
1. Find ALL ExitPlanMode calls: `"name":"ExitPlanMode","input":{"plan":"..."}`
2. Extract each in chronological order
3. **CRITICAL**: Read FIRST call for complete vision
4. **PRESERVE original structure** - if phases existed, use phases; if flat list, keep flat
5. **DO NOT invent structure** not in original
6. Synthesize complete plan ensuring ALL original items captured
7. Generate task name from main theme (1-2 uppercase words)

**Search for implementation evidence:**
1. Review activity after last ExitPlanMode
2. Find: Write/Edit/NotebookEdit/Bash/TodoWrite calls, completion phrases, confirmations
3. Map tasks to evidence via file paths and keywords

**Assign statuses:**
- Strong evidence (multiple indicators) → [DONE]
- Medium evidence (single indicator) → [IN PROGRESS]
- Weak/no evidence → [TODO]

### For Update Mode

1. Read `PLAN__<TASK>.md`, parse task hierarchy with statuses
2. Search recent activity for implementation evidence
3. Match tasks to evidence, assign status updates
4. Check for plan evolution: ExitPlanMode newer than PLAN file
5. Present findings if any tasks have evidence (skip if all TODO)

## Phase 3: Write or Update File

### Create Mode - Generate File

Structure (preserve original organization from ExitPlanMode):
- **Overview**: 1-2 paragraph summary
- **Scope**: Features, components, files, integrations
- **Purpose**: Problem, value, requirements, context
- **Implementation Details**: Hierarchical tasks with `[STATUS] description`
  - Include file paths/names
  - Nest with 3-space indentation
  - Order: setup → implementation → testing
  - Apply evidence-based statuses

Write to `{git_root}/PLAN__<TASK>.md` (NOT ~/.claude/plans/) and **validate**:
- Compare structure to FIRST ExitPlanMode call
- If original had phases, ensure all phases documented
- If original was flat list, ensure no invented phases
- Count items: original N items should match generated
- Future work documented as [TODO], not omitted
- Task name format valid (1-2 uppercase words, single underscores)

Report: file path, task count, structure type

### Update Mode - Modify Existing

Update `PLAN__<TASK>.md`:
- For each status change, use Edit tool
- Match exact old_string with indentation and status
- Replace with new status
- Preserve hierarchy and formatting

Handle plan evolution if detected:
- Add new areas to existing structure
- Insert new tasks under relevant parents
- Mark deprecated as `[CANCELLED - plan changed]`
- Update Scope/Purpose if changed
- Append to Plan Updates section with timestamp

Report: file path, X tasks completed, Y in progress, Z changes made

## Status Transitions & Evidence Strength

**Evidence Strength:**
- Strong: Multiple indicators → [DONE]
- Medium: Single indicator → [IN PROGRESS]
- Weak/None: Mention only → [TODO]

**Valid Status Labels:**
- [TODO] → Not started
- [IN PROGRESS] → Started not finished
- [DONE] → Completed
- [BLOCKED] → Cannot proceed (include reason)
- [CANCELLED - plan changed] → No longer relevant

## Critical Requirements

**All Modes:**
- Analyze session activity for evidence (tool calls + completion phrases)
- Match ALL tasks to evidence, assign statuses intelligently
- Include evidence-free tasks as [TODO] - never skip planned work
- Use 3-space indentation, preserve hierarchy
- Inform user of mode and target file

**Create Mode:**
- **PREVENT RECENCY BIAS**: Prioritize FIRST ExitPlanMode for complete vision
- **PRESERVE STRUCTURE**: Match original organization exactly
- Document entire plan regardless of implementation progress
- Support both complex multi-phase AND simple flat lists
- Generate valid task name, create `PLAN__<TASK>.md` in git root (NEVER in ~/.claude/plans/)

**Update Mode:**
- Use Edit tool with exact matching
- Handle evolution: add new, mark deprecated as cancelled

**Legacy Migration:**
- Detect `PLAN.md`, generate task name from content
- Rename using Bash `mv`, inform user of migration
