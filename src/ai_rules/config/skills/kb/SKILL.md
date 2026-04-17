---
name: kb
description: >-
  This skill should be used when the user asks to "save to knowledge base",
  "write a note", "persist this", "remember this pattern", "update the KB",
  or when the Stop hook instructs the agent to persist session knowledge.
  Also use when asking "search knowledge base", "what do we know about",
  or needing cross-project context from basic-memory.
---

# Knowledge Base (basic-memory)

A persistent markdown knowledge base at `~/basic-memory/` powered by the basic-memory MCP server. Knowledge persists across sessions, repos, and machines via git sync. Searchable with hybrid BM25 + vector search.

## Workflow

1. **Search first** to avoid duplicates: `search_notes(query="topic")`
2. **Read existing** if a related note exists: `read_note(identifier="note-title")`
3. **Write or update**: `write_note(title="...", directory="...", content="...")`
4. **Connect related notes** using `[[wikilinks]]` in the Relations section

## Directory Guide

| Directory | Use for | Example titles |
|-----------|---------|----------------|
| `repos/` | Per-repo commands, gotchas, patterns | "ai-rules", "goosed-slackbot" |
| `patterns/` | Reusable technical knowledge | "uv-run-not-direct-invocation" |
| `decisions/` | ADRs -- why something was chosen | "raw-sql-over-sqlalchemy" |
| `preferences/` | User working style, conventions | "test-docstring-conventions" |
| `references/` | External knowledge, company info | "block-ci-cd-pipeline" |
| `references/block/` | Block/Square-specific knowledge | "service-registry-conventions" |
| `people/` | Teammates, communication context | "tyler-sprout-expert" |
| `feedback/` | Corrections, lessons from mistakes | "no-assertions-without-verification" |
| `projects/` | Multi-repo initiative context | "slackbot-kotlin-migration" |

## Note Format

Every note uses YAML frontmatter + structured observations + relations:

```markdown
---
title: Note Title
type: note
tags: [tag1, tag2]
---

# Note Title

## Observations
- [fact] Concrete, verified information
- [tip] Practical advice for future use
- [method] How to do something specific
- [preference] User's stated preference or convention
- [decision] A choice that was made and why

## Relations
- related_to [[other-note-title]]
- depends_on [[prerequisite-note]]
```

### Observation Categories

- **`[fact]`** -- verified, objective information (e.g., "Uses Gradle wrapper, not Maven")
- **`[tip]`** -- practical guidance (e.g., "Check Justfile before guessing build commands")
- **`[method]`** -- how to do something (e.g., "Run `just check-all` for full validation")
- **`[preference]`** -- user's stated preference (e.g., "Never add docstrings to test functions")
- **`[decision]`** -- a choice with rationale (e.g., "Chose raw SQL for performance over ORM convenience")

### Tags

Use lowercase, hyphenated tags in frontmatter. Common tags: `python`, `kotlin`, `rust`, `block`, `testing`, `ci-cd`, `architecture`, `gotcha`.

### Wikilinks

Connect related notes with `[[note-title]]` in the Relations section. Use typed relations:
- `related_to [[note]]` -- general connection
- `depends_on [[note]]` -- prerequisite
- `supersedes [[note]]` -- replaces older knowledge
- `contradicts [[note]]` -- conflicting information (flag for review)

## When to Write vs Search

**Write a note when:**
- A decision was made about architecture or approach
- A repo-specific gotcha or non-obvious command was discovered
- Company-specific knowledge was learned (Block internals, service names, team conventions)
- The user corrected a previous assumption
- A reusable pattern was identified

**Search instead when:**
- Starting work in an unfamiliar repo -- `search_notes(query="repo-name")`
- Encountering a pattern already seen -- `search_notes(query="topic")`
- Needing cross-project context -- `build_context(url="memory://note-title")`

**Do NOT write:**
- Session-specific ephemeral context (what files were edited this session)
- Information obvious from the codebase (README content, import paths)
- Speculative or unverified information

## MCP Tools Quick Reference

| Tool | Purpose |
|------|---------|
| `search_notes(query, tags?, note_types?)` | Hybrid search across all notes |
| `build_context(url)` | Graph traversal from a note via wikilinks |
| `read_note(identifier)` | Read a specific note by title or permalink |
| `write_note(title, directory, content)` | Create or update a note |
| `edit_note(identifier, find, replace?)` | Partial edit without full rewrite |
| `delete_note(identifier)` | Delete a note (ask user first) |
| `recent_activity(depth?)` | Recently modified notes |
| `list_directory(dir_name?, depth?)` | Browse the folder structure |

## Additional Resources

### Reference Files

For complete note templates with realistic examples for each directory type:
- **`references/note-templates.md`** -- Full templates for repos/, patterns/, decisions/, preferences/, references/, people/, feedback/, projects/
