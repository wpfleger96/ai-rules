#!/usr/bin/env bash
# Commit + push knowledge base changes after a basic-memory write.
# Called by PostToolUse hook on mcp__basic-memory__* tools.
WIKI_DIR="${BASIC_MEMORY_HOME:-$HOME/basic-memory}"
[ -d "$WIKI_DIR/.git" ] || exit 0
cd "$WIKI_DIR"
git add -A
git diff --cached --quiet && exit 0
git commit -m "auto: update knowledge base"
nohup git push >/dev/null 2>&1 &
exit 0
