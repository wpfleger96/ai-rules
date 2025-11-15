#!/usr/bin/env bash

set -euo pipefail

echo "Syncing dependencies"
uv sync

echo "Running linter"
uvx ruff check . --fix

echo "Running formatting"
uvx ruff format .
