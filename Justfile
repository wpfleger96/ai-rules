# Settings
set dotenv-load := false

# Default recipe: quick quality check without tests
default: sync type-check lint-check format-check

# Setup & Dependencies
sync:
    uv sync

install-hooks:
    @echo "Installing git hooks..."
    git config --local core.hooksPath .hooks
    @echo "Git hooks installed successfully"

setup: sync install-hooks
    @echo "Development environment setup complete"

# Code Quality - Check variants
type-check:
    uv run mypy .

lint-check:
    uvx ruff check .

format-check:
    uvx ruff format . --check

# Code Quality - Fix variants
lint:
    uvx ruff check . --fix

format:
    uvx ruff format .

# Composite quality checks
check: sync type-check lint-check format-check
    @echo "Quick quality checks passed"

check-all: check test
    @echo "All quality checks and tests passed"

pre-commit: sync type-check lint format test
    @echo "Pre-commit checks passed"

# Testing
test:
    uv run pytest

test-fast:
    uv run pytest -m 'not performance' -n auto

test-unit:
    uv run pytest -m unit

test-integration:
    uv run pytest -m integration

test-nocov:
    uv run pytest -o addopts='-n auto -m "not performance"'

# Performance Benchmarking
benchmark-compare:
    uv run pytest -m performance -o addopts='-v' --benchmark-compare

benchmark-save:
    uv run pytest -m performance -o addopts='-v' --benchmark-autosave

benchmark-record:
    uv run pytest -m performance -o addopts='-v' --benchmark-compare --benchmark-autosave

benchmark-list:
    @if [ -d .benchmarks ]; then echo "Saved benchmarks:"; ls -lh .benchmarks/*/; else echo "No saved benchmarks found"; fi

benchmark-clean:
    @if [ -d .benchmarks ]; then echo "Removing all saved benchmarks..."; rm -rf .benchmarks/; else echo "No saved benchmarks found"; fi

# Build & Package
build: sync
    uv build

clean-build:
    rm -rf dist/ build/ *.egg-info

rebuild: clean-build build

# CI workflow (matches CI steps)
ci: sync type-check lint-check format-check test
    @echo "CI checks passed"
