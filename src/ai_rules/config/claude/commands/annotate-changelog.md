---
description: Annotates auto-generated changelog entries with detailed descriptions
allowed-tools: AskUserQuestion, Bash, Edit, Glob, Grep, Read, TodoWrite
model: sonnet
---

## Context

- Changelog file: !`find . -maxdepth 1 -name "CHANGELOG*" -type f | head -1`
- Recent commits: !`git log --oneline -20 2>/dev/null || echo "NO_COMMITS"`
- Git repo root: !`git rev-parse --show-toplevel 2>/dev/null || pwd`

# Annotate Changelog

**Usage:**
- `/annotate-changelog` - Add detailed descriptions to terse auto-generated changelog entries

Enhances auto-generated changelogs (from semantic-release, conventional commits, etc.) by adding user-facing descriptions beneath terse commit messages. Gathers context from git diffs, commit messages, and PR descriptions to explain what changed and why it matters.

## Workflow

### Phase 1: Parse Changelog

1. **Read CHANGELOG.md** (from Context above)
2. **Identify entries needing annotation:**
   - Look for terse commit messages ("Cc perms", "Still flaky", "Llms are dumb")
   - Short descriptions without explanation of impact
   - Entries with just commit SHA links but no detail
3. **Extract commit information:**
   - Parse version sections (e.g., `## [0.10.3] - 2024-12-05`)
   - Find commit SHAs in links (e.g., `[9dd366c]`)
   - Note existing structure (bullets, sections like "### Added")

### Phase 2: Gather Context

For each entry needing annotation:

1. **Get full commit message:**
   ```bash
   git log -1 --format="%B" <sha>
   ```
   The full body often has more detail than the subject line.

2. **Get commit diff summary:**
   ```bash
   git show --stat <sha>
   ```
   Shows which files changed, gives technical context.

3. **Search for related PR:**
   ```bash
   gh pr list --search "<sha>" --state merged --json number,title
   ```
   Find if this commit was part of a pull request.

4. **If PR found, get description:**
   ```bash
   gh pr view <pr_number> --json body --jq .body
   ```
   PR descriptions often have better user-facing explanations.

5. **If context is insufficient** (all sources are terse or unclear):
   - Use AskUserQuestion tool
   - Show the commit SHA and message
   - Ask: "What was the user-facing change in this commit?"

### Phase 3: Generate Annotations

For each entry:

1. **Analyze context gathered:**
   - What files changed? (from diff)
   - What's the user-facing impact?
   - Why did this change happen? (bug fix, new feature, breaking change)

2. **Write annotation:**
   - Focus on user-facing impact, not implementation details
   - Explain WHAT changed for users, not HOW it was implemented
   - Keep it concise (1-2 sentences)
   - Match existing changelog tone/style

3. **Format:**
   ```markdown
   - Terse commit message ([commit_sha])
     > Detailed annotation explaining user-facing impact
   ```

### Phase 4: Update Changelog

1. **Preserve structure:**
   - Keep version headers intact
   - Maintain section organization (Added, Fixed, etc.)
   - Keep commit SHA links as-is
   - Don't remove or replace original entries

2. **Add annotations:**
   - Insert description as blockquote below entry
   - Use `>` for blockquote formatting
   - Maintain consistent indentation

3. **Present changes:**
   - Show diff before applying
   - Explain how many entries were annotated
   - Give user chance to review

4. **Apply edits:**
   - Use Edit tool to update CHANGELOG.md
   - Make one edit per entry or batch similar entries

## Example Transformation

**Before:**
```markdown
## [0.10.3] - 2024-12-05

### Bug Fixes

- Cc perms ([9dd366c])
```

**After:**
```markdown
## [0.10.3] - 2024-12-05

### Bug Fixes

- Cc perms ([9dd366c])
  > Fixed Claude Code permissions in settings.json to allow the doc-writer skill
```

**Before:**
```markdown
### Added

- Doc-writer skill for claude code ([e293e4c])
```

**After:**
```markdown
### Added

- Doc-writer skill for claude code ([e293e4c])
  > Added new Claude Code skill that provides guidance for writing compact, effective technical documentation including README, ARCHITECTURE, and API docs
```

## Key Principles

**Focus on user impact:**
- "Added X feature that lets users do Y"
- "Fixed bug where Z would fail"
- NOT: "Updated function foo() to call bar()"

**Be concise:**
- 1-2 sentences max
- Don't repeat obvious information from commit message
- Add value, don't just restate

**Preserve changelog structure:**
- Don't change version numbers, dates, or commit links
- Don't reorganize sections
- Don't remove entries (even if trivial)

**Match style:**
- Use same tone as existing entries
- Follow Keep a Changelog format if present
- Consistent formatting (blockquotes for annotations)

## Critical Requirements

**Context gathering:**
- MUST try git diffs first, then commit messages, then PR descriptions
- MUST use AskUserQuestion if all sources are unclear
- DON'T fabricate or guess at changes

**Annotations:**
- MUST focus on user-facing impact
- MUST be concise (1-2 sentences)
- MUST NOT repeat implementation details already in diff

**Structure preservation:**
- MUST keep all original entries intact
- MUST preserve commit SHA links
- MUST maintain version structure and dates
- MUST use blockquote format (`>`) for annotations

**Approval:**
- MUST show diff before applying changes
- MUST explain how many entries were annotated
- DON'T apply changes without user seeing what will change

Your goal is to make auto-generated changelogs more useful by adding context about what changed from a user's perspective, while preserving the automated structure and commit traceability.
