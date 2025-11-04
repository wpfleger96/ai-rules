#!/usr/bin/env bash

set -o errexit  # quit on first error
set -o nounset

echo "Syncing dependencies"
uv sync

echo "Running formatting"
uvx ruff format .

echo "Running linter"
uvx ruff check . --fix