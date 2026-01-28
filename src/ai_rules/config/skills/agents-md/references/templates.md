# AGENTS.MD Templates

## Standard AGENTS.md Structure

```markdown
# AGENTS.md

[1-2 sentence project description]

## Quick Commands

```bash
# Setup
[commands for initial setup - install dependencies, env setup]

# Development
make build          # Build the project
make run            # Run development server
make test           # Run all tests
pytest tests/test_foo.py  # Run specific test file
make lint           # Run linter
make format         # Format code
```

## Project Structure

```
src/
  cli.py            # Main CLI entry point
  api/              # API endpoints
  models/           # Data models
  utils/            # Shared utilities
tests/
  test_*.py         # Test files
config/             # Configuration files
```

## Tech Stack

- Python 3.11
- Framework: FastAPI 0.104
- Database: PostgreSQL 15
- Key libraries: pydantic, httpx, pytest

## Key Patterns

### Pattern Name

✅ Correct usage:
```python
# Example of correct pattern
user_email = get_user_email(user_id)
```

❌ Incorrect usage:
```python
# Example of what NOT to do
e = get_email()  # Unclear variable name
```

### Another Pattern

[Repeat structure: explanation + ✅ example + ❌ example]

## Testing

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_foo.py  # Specific file
pytest -k "test_user"     # Match pattern
pytest --cov=src          # With coverage
```

Test structure:
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Fixtures in `tests/conftest.py`
- Naming: `test_<function>_<scenario>_<expected>`

## Common Gotchas

1. **Array path access:** Use `hooks.Stop[0].cmd` for arrays in JSON paths (not `hooks.Stop.cmd`)
2. **Mock HOME directory:** Need both `os.environ` and `Path.home()` patches for full mocking
3. **Database migrations:** Run `make migrate-test` before tests or DB schema mismatches occur
4. **[Specific gotcha with concrete details]**

## Key Files by Task

| Task | Files |
|------|-------|
| Add CLI command | `src/cli.py`, `src/commands/<name>.py` |
| Add API endpoint | `src/api/routes.py`, `src/api/handlers/<name>.py` |
| Add data model | `src/models/<name>.py` |
| Modify configuration | `config/settings.py` |

## Boundaries (optional)

**✅ Always:**
- Run tests before commit
- Use existing components from `src/components/`
- Follow naming conventions in style guide

**⚠️ Ask first:**
- Adding new dependencies
- Database schema changes
- Breaking API changes

**🚫 Never (breaks things):**
- Commit secrets to git → CI will reject, requires history rewrite
- Modify production config directly → Use staging first
```

## Minimal AGENTS.md (Simple Projects)

For simple projects (<10 files, straightforward workflow):

```markdown
# AGENTS.md

[Project description]

## Quick Commands

```bash
npm install         # Setup
npm test            # Run tests
npm run dev         # Start dev server
```

## Structure

```
src/index.js        # Entry point
src/utils.js        # Utilities
tests/              # Tests
```

## Key Patterns

✅ Use async/await for API calls
❌ Don't use callbacks

## Common Gotchas

1. Run `npm install` after pulling (dependencies change frequently)
2. Set `NODE_ENV=test` for test runs
```

## Optional Boundaries Section

Include only if there are critical constraints:

```markdown
## Boundaries

**✅ Always:**
- Run linter before commit
- Write tests for new features
- Use TypeScript strict mode

**⚠️ Ask first:**
- Adding new dependencies
- Changing build config
- Modifying API contracts

**🚫 Never (critical constraints):**
- Commit `.env` files → Contains secrets
- Push directly to main → Use PRs only
- Modify migration files → Create new ones instead
```

## Quality Checklist

Before finalizing AGENTS.md:

- [ ] Under 100 lines (60 ideal)
- [ ] Commands include exact syntax with flags
- [ ] All patterns have ✅/❌ code examples
- [ ] Gotchas are specific with details
- [ ] Key files mapping is complete
- [ ] No sensitive information (API keys, credentials)
- [ ] Commands are tested and work
- [ ] Versions are specified for language/frameworks

## Examples by Project Type

### CLI Application

```markdown
## Quick Commands

```bash
# Setup
cargo build

# Development
cargo run -- --help        # Show help
cargo run -- serve         # Start server
cargo test                 # Run tests
cargo clippy               # Lint
```

## Key Files by Task

| Task | Files |
|------|-------|
| Add command | `src/cli.rs`, `src/commands/<name>.rs` |
| Add config option | `src/config.rs` |
```

### Web Application

```markdown
## Quick Commands

```bash
# Setup
npm install
cp .env.example .env       # Configure environment

# Development
npm run dev                # Start dev server (localhost:3000)
npm test                   # Run tests
npm run lint               # Lint
npm run build              # Production build
```

## Common Gotchas

1. **Environment variables:** Copy `.env.example` to `.env` before running
2. **Database:** Run `docker-compose up -d postgres` before starting app
3. **Ports:** Dev server uses 3000, API uses 8000, ensure not in use
```

### Python Library

```markdown
## Quick Commands

```bash
# Setup
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv sync

# Development
pytest                     # Run tests
pytest --cov=src           # With coverage
ruff check .               # Lint
ruff format .              # Format
```

## Testing

- Tests in `tests/`
- Fixtures in `tests/conftest.py`
- Use `pytest-mock` for mocking
- Coverage target: 80%+
```
