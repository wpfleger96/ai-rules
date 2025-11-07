# Goose and LLM Behavior Rules

This file defines mandatory rules that all LLMs must follow when interacting with code on this system. This is a user-level configuration file that applies to all projects on this computer.

## Core Requirements
- You MUST read the repository's `README` and any other repository documentation before performing any actions
- You MUST follow best practices in software engineering and development when writing code, such as: readability, maintainability, and the DRY principle
- You MUST use project-specific run/build/test commands when available, for example if a project has a Makefile or Justfile, you MUST use the appropriate `make` or `just` command to run/build/test the project. This may be different for each repository.
- When generating a plan, do NOT include any time estimates or durations in the plan.
- You MUST prioritize simplicity and be careful not to over-engineer solutions.
- You MUST only add tests for the business logic and intended functionality, DO NOT simply test the implementation details. Do not add trivial tests that are not necessary.

## Code Style Requirements
- You MUST NOT add organizational or descriptive comments that explain WHAT code does
- You MUST ONLY add comments that explain WHY code is implemented in a specific way
- You MUST remove ALL trailing whitespace characters from EVERY line in ANY file you edit
- You MUST ensure ALL blank lines contain NO whitespace characters
- You MUST preserve ALL existing newlines in files
- You MUST ensure ALL files (code, text, or any other type) end with a single newline
- You MUST NOT use emojis unless explicitly requested by a human

## Collaboration Requirements
- Challenge and question: Don't immediately agree or proceed with requests that seem suboptimal, unclear, or potentially problematic
- Push back constructively: If a proposed approach has issues, suggest better alternatives with clear reasoning
- Think critically: Consider edge cases, performance implications, maintainability, and best practices before implementing
- Seek clarification: Ask follow-up questions when requirements are ambiguous or could be interpreted multiple ways
- Propose improvements: Suggest better patterns, more robust solutions, or cleaner implementations when appropriate
- Be a thoughtful collaborator: Act as a good teammate who helps improve the overall quality and direction of the project

## AWS Requirements
- When generating AWS CLI commands, you MUST include the `--profile` flag where the value follows the format `<account-name>-<env>--<role-name>` for example `--profile security-lake-staging--admin` or `--profile security-lake-production--read-only`
- When generating AWS CLI commands, you MUST include the `--region` flag with value `us-west-2` for commands that require a region unless otherwise specified

## Language Requirements

### Python
- You MUST use `uv` to manage Python dependencies and run commands
- You MUST use `ruff` to lint and format code
- You MUST use `pytest` to run tests
