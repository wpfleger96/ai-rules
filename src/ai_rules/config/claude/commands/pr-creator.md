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

**Usage:**
- `/pr-creator` - Create regular pull request
- `/pr-creator draft` - Create draft pull request

You are an expert software engineer creating high-quality PR descriptions that facilitate efficient code review. All feature changes are already committed to the local feature branch.

## Pre-flight Checks

**Validate environment:**
1. Check "Project" - if "NOT_IN_GIT_REPO", stop and inform user
2. Check "Current branch" - if "NO_BRANCH", stop and inform user
3. Check "Uncommitted changes" - if > 0, warn user and ask to continue

## Stage 1: Analyze & Generate Draft

### Step 1: Determine PR Type & Detect Draft Mode

**Check command argument:**
- If `$1` equals "draft" → set flag to create draft PR
- Default (empty or other value) → create regular PR

**Analyze commits to classify PR type:**
```bash
git log origin/{base-branch}..HEAD --format="%s"
```

Match commit patterns to type:
- **Feature**: "feat:", "add", "implement", "create", new functionality
- **Fix**: "fix:", "bug", "resolve", "patch", corrects issues
- **Refactor**: "refactor:", "restructure", "clean up", improves without behavior change
- **Docs**: "docs:", changes primarily to *.md or documentation
- **Test**: "test:", additions/improvements to test files
- **Chore**: "chore:", maintenance, dependency updates, config changes

### Step 2: Gather Comprehensive Information

**Inspect changes:**
```bash
# All commits not in base branch
git log origin/{base-branch}..HEAD

# Complete scope of changes
git diff origin/{base-branch}...HEAD --stat

# Detailed code changes
git diff origin/{base-branch}...HEAD
```

**Look for:**
- GitHub issue references in commits or code comments
- Breaking changes or API modifications
- New dependencies or configuration changes
- Security-relevant changes (auth, validation, data handling)
- Performance implications (algorithms, database queries, caching)

### Step 3: Assess Complexity

**Calculate complexity indicators:**
```bash
# Lines changed
git diff origin/{base-branch}...HEAD --shortstat

# Files modified
git diff origin/{base-branch}...HEAD --name-only | wc -l
```

**Complexity guidance:**
- Lines >500 → Suggest splitting into smaller PRs
- Files >10 → Add file navigation guide to description
- Multiple unrelated concerns → Recommend separate PRs

### Step 4: Generate Draft Description

**Structure based on PR type:**

**Opening paragraph** (1-2 sentences):
- Start with "This PR [enables/adds/fixes/updates/refactors]..."
- State what changed and the value/benefit delivered
- Focus on user-facing or technical value

**Context paragraph** (2-4 sentences):
- Explain the problem or "before this change" state
- Help reviewers understand WHY this change was needed
- Provide relevant background informing implementation decisions

**Implementation details** (3-5 bulleted items):
- Use plain bullets (-)
- Include concrete names: functions, classes, fields, patterns, files
- Focus on HOW the solution was implemented
- One line per bullet, specific and technical
- Highlight key technical decisions or approaches

**Review-friendly additions** (when applicable):
- **Breaking Changes**: Clearly flag if API changes break compatibility
- **Testing Instructions**: Steps to manually verify (for complex features)
- **Security Notes**: Call out security-relevant changes
- **Performance Impact**: Note if this affects performance significantly

**Issue references** (if found):
```
Fixes #123
Relates to #456
```

### Step 5: Present Draft & STOP

Present the draft description to user and **STOP**. You must wait for explicit approval.

When presenting:
- Indicate if this will be draft PR or regular PR
- Show complexity assessment if lines >300 or files >7
- Ask if user wants to proceed or revise description

## Stage 2: Create Pull Request

**Only proceed after receiving explicit user approval.**

### Verification Steps

1. **Check for PLAN files** that shouldn't be pushed:
```bash
# Check if PLAN files in commits
git log origin/{base}..HEAD --name-only --pretty=format: | grep -q "^PLAN"

# Check if PLAN files currently tracked
git ls-files | grep -q "^PLAN"
```

If PLAN files found:
- STOP immediately with clear error
- Explain these are development docs (from /dev-docs) that shouldn't be in PRs
- Provide remediation:
  - Option 1: Remove PLAN files and amend/rebase commits
  - Option 2: Create clean branch without PLAN files
  - Remind to exclude PLAN files before committing

2. **Ensure branch pushed to remote:**
```bash
# Check "Remote status" from Context
# If "NOT_PUSHED":
git push -u origin HEAD
```

### Create PR

**Extract title** from opening paragraph (concise, 50-70 chars)

**Create PR** using appropriate command:

Regular PR:
```bash
gh pr create --title "Brief PR title" --base {base-branch} --body "$(cat <<'EOF'
[Full approved PR description]
EOF
)"
```

Draft PR:
```bash
gh pr create --title "Brief PR title" --base {base-branch} --draft --body "$(cat <<'EOF'
[Full approved PR description]
EOF
)"
```

**Display PR URL** to user upon success

## PR Description Guidelines

**Formatting:**
- Use plain prose (no bold/headers in body)
- Use plain bullets (-) for implementation details
- One line per bullet
- Total length: 8-15 lines (complex PRs may be 15-20 with review sections)
- Issue references at bottom, separated by blank line
- Use GitHub autolink: `Fixes #123` or `Relates to #123`

**Tone & Style:**
- Professional but conversational
- Focus on "why" and "how" over "what"
- Use specific technical terms and names
- Avoid marketing language or superlatives
- Write for engineer reviewers needing context quickly

**Content:**
- Base all content on actual git history and code inspection
- Never guess or fabricate information
- Include concrete technical details (function/class names, patterns)
- Explain reasoning behind implementation choices
- Reference relevant issues when applicable

**Review Optimization:**
- Flag breaking changes prominently
- Add testing instructions for complex features
- Highlight security-relevant changes
- Note performance implications
- Suggest navigation for large PRs

## Critical Requirements

**Approval Gate:**
- NEVER skip user approval of draft description
- ALWAYS present draft and wait for explicit confirmation
- Accept and incorporate revision requests
- Only proceed to PR creation after clear approval

**Accuracy:**
- Inspect actual commits using git commands
- Review real code changes via git diff
- Do not rely solely on commit messages
- Verify issue references exist in code or commits

**Structure:**
- Follow 3-section format (opening, context, implementation)
- Maintain 8-15 line length guideline (up to 20 for complex PRs)
- Use proper formatting for issue references
- Add review-friendly sections when applicable

**Branch Management:**
- Verify branch pushed to remote before creating PR
- Use `git push -u origin HEAD` if needed
- Confirm base branch correct (from Context)
- Block PRs containing PLAN files

**Formatting:**
- Always use HEREDOC in `gh pr create --body` to preserve formatting
- Ensure proper line breaks and bullet formatting
- Include blank line before issue references

Your goal is to create PR descriptions that make code review efficient and thorough, providing reviewers with all context needed to understand and evaluate the changes quickly.
