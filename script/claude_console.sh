#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${ANTHROPIC_CONSOLE_KEY:-}" ]]; then
    echo "Error: ANTHROPIC_CONSOLE_KEY environment variable not set"
    echo "Set it in your shell config: export ANTHROPIC_CONSOLE_KEY='sk-ant-...'"
    exit 1
fi

ANTHROPIC_API_KEY="$ANTHROPIC_CONSOLE_KEY" exec claude --model opusplan "$@"
