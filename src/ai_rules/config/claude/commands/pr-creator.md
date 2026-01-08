---
description: Creates GitHub pull requests with comprehensive descriptions by analyzing git history and code changes
allowed-tools: AskUserQuestion, Bash, Glob, Grep, Read, TodoWrite
model: sonnet
---

## Context

- Project: !`git rev-parse --show-toplevel 2>/dev/null || echo "NOT_IN_GIT_REPO"`
- Current branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "NO_BRANCH"`
- Base branch: !`git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main"`
- Uncommitted changes: !`git status --porcelain 2>/dev/null | wc -l | xargs`
- Remote status: !`git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "NOT_PUSHED"`
- Commits ahead: !`git rev-list --count @{u}..HEAD 2>/dev/null || echo "0"`

# Create GitHub Pull Request

**Usage:** `/pr-creator` - Create regular PR | `/pr-creator draft` - Create draft PR

Expert software engineer creating high-quality PR descriptions that facilitate efficient code review. All feature changes are committed to local feature branch.

## Pre-flight Checks

**Validate environment:**
1. Check "Project" - if "NOT_IN_GIT_REPO", stop and inform user
2. Check "Current branch" - if "NO_BRANCH", stop and inform user
3. Check "Uncommitted changes" - if > 0, warn user and ask to continue

## Stage 1: Analyze & Generate Draft

### Step 1: Detect Mode & PR Type

**Mode:** Check `$1` equals "draft" → draft PR, else regular PR

**Classify PR type** via `git log origin/{base}..HEAD --format="%s"`:
- **Feature:** feat:, add, implement, create, new functionality
- **Fix:** fix:, bug, resolve, patch
- **Refactor:** refactor:, restructure, clean up
- **Docs:** docs:, changes to *.md
- **Test:** test:, test file changes
- **Chore:** chore:, maintenance, deps, config

### Step 2: Gather Information

**Inspect changes:**
```bash
git log origin/{base}..HEAD
git diff origin/{base}...HEAD --stat
git diff origin/{base}...HEAD
gh issue list --limit 20  # Search for related open issues
```

**Look for:** GitHub issue refs in commits/branch name | Related open issues via `gh issue list` | Breaking changes | New dependencies | Security changes (auth, validation) | Performance implications

### Step 3: Generate Draft Description

**Structure (6-12 lines maximum):**

**Opening (1-2 sentences):** "This PR [enables/adds/fixes/updates]..." | State what changed and value delivered

**Context (1-3 sentences):** Explain problem/"before this" state | Help reviewers understand WHY | Keep brief - reviewers skim descriptions

**Implementation (2-4 bullets, plain `-`):** Focus on WHAT changed and WHY, not HOW it works internally | Include concrete names when relevant (functions, classes, fields) | One line per bullet | Prioritize the most significant changes only

**Review-friendly (only when non-obvious):** Breaking Changes | Security Notes | Performance Impact | Testing Instructions (only if setup is non-trivial)

**Issue refs (REQUIRED if PR addresses an issue):**
Always place at the very end of description, preceded by blank line. Use GitHub keywords to auto-close issues:
```
Resolves #123
```
OR if related but doesn't fully resolve:
```
Relates to #456
```

**Tone/style:** Professional but conversational | Focus on "what" and "why", not "how" | Use specific technical terms | Avoid marketing language | Plain prose (no bold/headers in body) | Plain bullets (`-`)

**Brevity principle:** Every word must earn its place - reviewers skim descriptions | Omit details visible in the diff | Skip obvious implementation details (e.g., "converted methods to async" unless async is the key change) | No complexity metrics or line counts

### Step 4: Present Draft & STOP

Present draft to user and **STOP**. Wait for explicit approval.

When presenting:
- Indicate draft/regular PR mode
- Ask to proceed or revise

## Stage 2: Create Pull Request

**Only after explicit user approval.**

### Verification

**Check for PLAN files:**
```bash
git log origin/{base}..HEAD --name-only --pretty=format: | grep -q "^PLAN" || git ls-files | grep -q "^PLAN"
```

If found: **STOP** - PLAN files are dev docs (from /dev-docs) that shouldn't be in PRs. Provide remediation: Remove PLAN files and amend/rebase OR Create clean branch without PLAN files

**Ensure branch pushed:**
```bash
# If Remote status = "NOT_PUSHED":
git push -u origin HEAD
```

### Create PR

**Extract title** from opening paragraph (50-70 chars)

**Create** (use HEREDOC for formatting):

**Regular:**
```bash
gh pr create --title "Title" --base {base} --body "$(cat <<'EOF'
[Full approved description]
EOF
)"
```

**Draft:**
```bash
gh pr create --title "Title" --base {base} --draft --body "$(cat <<'EOF'
[Full approved description]
EOF
)"
```

**Display PR URL** upon success.

## Critical Requirements

**Approval Gate:** NEVER skip user approval | ALWAYS present draft and wait | Accept revisions | Only proceed after clear approval

**Accuracy:** Inspect actual commits via git | Review code changes via diff | Don't rely solely on commit messages | Verify issue refs exist

**Structure:** Follow 3-section format (opening, context, implementation) | 6-12 lines maximum | Proper issue ref formatting | Add review sections only when non-obvious

**Branch Management:** Verify branch pushed before PR | Use `git push -u origin HEAD` if needed | Confirm base branch correct | Block PRs with PLAN files

**Formatting:** Always use HEREDOC in `gh pr create --body` | Ensure proper line breaks/bullets | Blank line before issue refs

Goal: Create PR descriptions making code review efficient and thorough, providing reviewers all context to understand and evaluate changes quickly.
