# LLM Behavioral Rules

## Quick Reference Checklist

**Before completing tasks:**
☐ Read README & docs | ☐ Create TODO list (multi-step) | ☐ Explore before implementing | ☐ Security checklist (external input) | ☐ Use project tooling (make/just/npm) | ☐ DRY & single responsibility | ☐ WHY comments only | ☐ Remove trailing whitespace | ☐ File ends with newline | ☐ Test behavior not implementation | ☐ AWS: --profile & --region | ☐ Keep simple | ☐ Ask clarifying questions

---

## Core Principles

### Security-First Code Generation
**Rule:** For code handling external input, auth, or sensitive data:
**Stage 1:** Implement functional requirements
**Stage 2:** Security checklist: Input validation | SQL injection prevention (parameterized queries) | XSS blocking (output encoding) | Auth/authz checks | Rate limiting | Sanitized errors | No secrets | Audit logging

**Why:** 40%+ of LLM code has vulnerabilities without security prompting.

### Workflow Management
**Rule:** Create TODO list before starting tasks, update as you complete each task.

### Autonomous Coding Workflow

**Trigger:** After completing non-trivial code implementation (new features, bug fixes, refactors affecting behavior), execute this workflow before presenting results to the user.

**Stages:**

| Stage | Action | Proceed when |
|-------|--------|--------------|
| 1. Implement | Write/modify code to meet requirements | Code written |
| 2. Quality Checks | Run format, lint, test via project tooling (`just check` or individually) | All checks pass (fix any issues found) |
| 3. Write Tests | Invoke `test-writer` skill for new/changed code paths | Tests written and passing |
| 4. Review | Invoke `code-reviewer` skill (runs in isolated subagent) | Review findings returned |
| 5. Fix | Address all 🔴 MUST FIX issues, then 🟡 SHOULD FIX issues | All blocking issues resolved |
| 6. Re-verify | If fixes made: re-run stages 2-4 until clean | All checks pass, no new issues |
| 7. Draft Commit | Generate conventional commit message for the changes | Message ready for user review |

**Stop condition:** Do NOT stage files, commit, or create PR. Present the draft commit message and wait for user instruction.

**Skip workflow when:** Changes are documentation-only, config/settings tweaks, typo fixes, or user explicitly requests "quick fix" or "no review needed."

**Project tooling priority:** Always check for Justfile/Makefile first. Use `just <task>` or `make <task>` when available. See "Project Tooling" section for fallback commands.

**Why this workflow:** Catches 40%+ of bugs and security issues before they reach production. The isolated review subagent prevents context pollution while enabling deep codebase analysis.

### Documentation First
**Rule:** Read README.md, CONTRIBUTING.md, docs/, .github/, Makefile/Justfile before actions.

### Project Tooling (CRITICAL - Check BEFORE Running Commands)

**Rule:** ALWAYS check for project-specific tooling files BEFORE executing any build/test/lint command.

**Mandatory check sequence (in order):**
1. **Justfile exists?** → Use `just <task>` commands (e.g., `just test`, `just format`, `just lint`)
2. **Makefile exists?** → Use `make <task>` commands
3. **package.json exists?** → Use `npm run <task>` commands
4. **pyproject.toml exists?** → Use `uv run <tool>` (NEVER direct tool invocation)
5. **Cargo.toml exists?** → Use `cargo <command>`

**Common mistakes that MUST be avoided:**

| ❌ WRONG (bypasses tooling) | ✅ CORRECT (uses tooling) |
|------------------------------|---------------------------|
| `ruff .` or `ruff check .` | `just lint` or `uv run ruff check .` |
| `pytest` | `just test` or `uv run pytest` |
| `black .` | `just format` or `uv run black .` |
| `cargo test` | Check Justfile first → `just test` if exists, else `cargo test` |

**Why:** Direct tool invocation bypasses project configuration and environment management. Usage data shows this is the #1 mistake agents make.

### Software Engineering Standards

**DRY Principle:** Extract repeated blocks (3+ occurrences)
**Single Responsibility:** One concern per function/class
**Clear Naming:** `get_user_by_email(email: str)` not `func1(x)`
**Error Handling:** At boundaries only, specific exceptions
**Input Validation:** Validate ALL user input and external API responses at system boundaries

**Why:** Reduces bugs 60%, improves maintainability.

### Explore Then Implement
**Rule:** Before new functionality, explore codebase for existing code to extend/reuse.

1. Search for similar patterns/abstractions
2. Extend existing (80%+ coverage) vs create new
3. Document why if truly novel

```python
# ❌ New endpoint duplicating logic
def fork_session(sid, mid): # 50 lines duplicating validation/state mgmt

# ✅ Extend existing
def edit_message(mid, content, fork=False): # Reuses validation, adds param
```

**Why:** LLMs create "clean" new code vs integrating. Causes duplication, maintenance burden.

### Simplicity Over Engineering
**Rule:** Prioritize simplicity, avoid over-engineering.

Three similar lines > premature abstraction | No helpers for one-time ops | Only requested features | Design for NOW

```python
# ✅ Simple: for p in payments: validate(p); charge(p)
# ❌ Over-engineered: class PaymentProcessor with factory/strategy patterns for single use
```

### Collaboration Protocol

**Rule:** Verify before assuming. Ask before guessing.

**Workflow:**
1. **UNDERSTAND** — Are requirements clear? Are there better approaches? What are the edge cases?
2. **VERIFY** — Can I confirm all assumptions? (See verification rules below)
3. **CLARIFY** — Ask specific questions for anything unclear, unverifiable, or suboptimal
4. **PROPOSE** — Suggest alternatives with technical justification
5. **IMPLEMENT** — Only after alignment on approach

**Verification rules (MUST follow):**
- **External APIs:** NEVER assume an external/closed-source API supports a feature. Verify via documentation, official references, or ask the user for confirmation.
- **Third-party behavior:** NEVER assume how third-party services, libraries, or tools behave without checking docs or testing.
- **User environment:** NEVER assume user's local setup, installed tools, or configurations. Ask or check.
- **Business logic:** NEVER assume business rules or domain constraints. Ask for clarification.

**When uncertain, ask.** Format questions specifically:
- ❌ "Should I proceed?" (too vague)
- ✅ "The Stripe API docs don't mention webhook retry limits. Do you know the retry policy, or should I implement exponential backoff as a safe default?"

**Challenge when you see:** Unclear requirements | Security gaps | Performance concerns | Unverifiable assumptions | High maintenance cost

**Do NOT challenge:** Clear decisions already made | Style preferences | Technology choices already decided

**Why:** LLMs confidently generate plausible-sounding but incorrect assumptions. Explicit verification prevents wasted work and builds trust through transparency.

---

## Technical Standards

### Python
**Tooling:** Follow Project Tooling hierarchy above. Fallbacks if no Justfile/Makefile:
- Dependencies: `uv add <pkg>`, `uv sync`
- Linting: `uv run ruff check .`
- Formatting: `uv run ruff format .`
- Testing: `uv run pytest`

**NEVER use direct tool invocation** (e.g., `ruff .`, `pytest`, `black .`) — always prefix with `uv run` or use project tooling.

**Testing framework:** `pytest` (not unittest)

### Rust
**Tooling:** Follow Project Tooling hierarchy above. Fallbacks if no Justfile/Makefile:
- Build: `cargo build`
- Test: `cargo test`
- Format: `cargo fmt`
- Lint: `cargo clippy`

### Testing Standards
**Rule:** Test behavior, NOT implementation.

**Test:** Business logic with branches | Error conditions | Integration points | Security controls | Public APIs
**Skip:** Getters/setters | Framework code | Trivial types | Private details

```python
# ✅ Behavior
def test_duplicate_email_fails():
    db.save(User(email="test@x.com"))
    result = register_user("test@x.com", "pass")
    assert not result.success and "exists" in result.error

# ❌ Implementation
def test_calls_hash_password():
    mock = Mock(); register_user("a", "b"); mock.assert_called() # Who cares?
```

**Structure:** Arrange-act-assert | Names: `test_<scenario>_<result>` | Independent | Deterministic

### AWS CLI
**Rule:** `--profile <account>-<env>--<role> --region us-west-2`
**Format:** `--profile data-lake-staging--admin` (✅) not `--profile staging-admin` (❌)
**Regex:** `^[a-z-]+-(dev|staging|production)--[a-z-]+$`

### GitHub Integration
**Rule:** Use `gh` CLI: `gh pr view 123` | `gh pr create` | `gh issue list --label bug` | `gh pr checks`

### Commit Messages
**Rule:** Subject states WHAT changed. Body explains WHY -- the problem, motivation, or design decision. Never narrate what's visible in `git show --stat` or the diff itself.

**Subject line:** `<type>(<optional-scope>): <imperative verb> <specific change>` (50-72 chars)

**Type accuracy:**

| Type | Use when | NOT when |
|------|----------|----------|
| `feat:` | Genuinely new functionality or capability | Moving existing code to new files |
| `fix:` | Correcting broken behavior | Refactoring that doesn't fix a bug |
| `refactor:` | Restructuring without behavior change | Adding new features during restructure |
| `docs:` | Documentation-only changes | Code changes with doc updates (use primary type) |
| `chore:` | Dependencies, CI, config, tooling | Anything touching application logic |

**Body (2-4 lines, skip if subject is self-explanatory):**
- Describe the problem or motivation driving the change
- Note design decisions, trade-offs, or alternatives considered
- Mention relationship to larger effort when part of a series
- Call out non-obvious side effects or included bug fixes

**Test:** Does the body add information a reviewer can't get from the diff? YES → keep it. NO → cut it.

```
# ❌ PROHIBITED - Narrates the diff
feat: extract DatabaseService from cli.py

Extract db_stats command (lines 920-1017) into DatabaseService.
Created services/database_service.py with get_stats() method.
Added DatabaseStats schema to services/schemas.py.
Updated CLI db_stats command to use service.
Added 5 unit tests in tests/unit/test_database_service.py.
All 421 tests pass (gained 5 new tests).

# ✅ CORRECT - Explains WHY and provides context
refactor: extract db_stats logic into DatabaseService

cli.py mixed business logic with display formatting, making queries
untestable in isolation. First step in service layer extraction --
establishes typed Pydantic return schema pattern.
```

```
# ❌ PROHIBITED - Method inventory, test count, marketing language
feat: extract SessionService from cli.py

Extract session business logic into SessionService with 6 methods
covering list/show/delete/enable/disable/resolve operations.
Service layer complete with full test coverage.
[...12 more lines listing every method and schema...]

# ✅ CORRECT - Problem, decision, noteworthy side-effect
refactor: extract session operations from cli.py into SessionService

Session commands had 300+ lines of inline raw SQL and ORM queries
interleaved with click.echo formatting. Preserves raw SQL approach
for complex filtered queries rather than converting to ORM. Fixes
None-safety bug in statistics display (obstructive_apneas > 0
crashed when value was None).
```

```
# ❌ PROHIBITED - CI status in commit message
feat: implement LTTB downsampling utility

Add Largest Triangle Three Buckets (LTTB) algorithm for time-series
downsampling. Created services/lttb.py with lttb_downsample() function.
Added 12 comprehensive unit tests in tests/unit/test_lttb.py.
All 416 tests pass, type check and lint pass.

# ✅ CORRECT - Motivation and technical context
feat: add LTTB downsampling for waveform rendering

CPAP waveforms have ~720k points per 8-hour session at 25Hz.
LTTB (Steinarsson 2013) reduces to ~2000 points while preserving
visual peaks and valleys. Required by upcoming WaveformService.
```

**Why:** Commit messages are permanent documentation. `git show --stat` already shows files changed. `git log --oneline` shows only the subject. The body's job is to capture context that will be lost once the author's working memory fades -- the problem, the reasoning, the trade-offs.

---

## Style & Formatting

### Code Comments
**Rule:** Only WHY comments explaining non-obvious rationale. NEVER WHAT comments restating code.

```python
# ❌ PROHIBITED - Restates what code already says
managed_plugins = self.load_managed_plugins()  # Load managed plugins
orphaned = (installed - desired) & managed  # Get orphaned plugins
for plugin in orphaned:  # Loop through orphaned plugins
    managed.discard(plugin)  # Remove from managed set

# ✅ CORRECT - Self-documenting code needs no comments
managed_plugins = self.load_managed_plugins()
orphaned = (installed_keys - desired_keys) & managed_plugins
for plugin in orphaned:
    managed_plugins.discard(plugin)

# ✅ REQUIRED - Explains WHY (non-obvious context)
delay = 2 ** retry_count  # Exponential backoff for Stripe rate limits
managed.discard(plugin)  # Prevent re-pruning user-installed plugins
```

**Ask:** Can a developer understand this by reading the code? If yes, no comment. If no, explain WHY.

### Whitespace
Remove ALL trailing whitespace | Blank lines have NO whitespace | Files end with single newline

### Emojis
Plain text only unless explicitly requested.

---

## Model-Specific Optimizations

**Claude 4.5:** Extremely explicit instructions, XML tags (`<context>`, `<constraints>`), positive framing, WHY context for requirements
**GPT-5:** Literal precision, JSON mode for structured output, few-shot (3-5 examples)
**Reasoning (o3, DeepSeek):** Zero-shot ONLY, simple/direct, NO "think step by step", trust 30+ sec thinking
**Context Window:** Critical info at START/END, use XML/structured markers (LLMs have "lost in middle" problem)

---

## Planning
When generating plans, omit time estimates. Focus on what needs doing, not when.

---

## Critical Constraints (End-of-Context Reinforcement)

These rules are frequently ignored due to context window limitations. Placing them here leverages recency bias.

### Code Comments - MANDATORY

**NEVER add comments that:**
1. Explain WHAT code does (the code already says that)
2. Use "Step 1", "Step 2", "Step N" patterns (code reads sequentially)
3. Narrate function flow (readers can follow the code)

❌ PROHIBITED patterns:
- `// Step 1: Set up the configuration`
- `// Step 2: Process the request`
- `plugins = load_plugins()  # Load plugins`
- `for item in items:  # Loop through items`
- `// Initialize the client`
- `// Return the result`

✅ ONLY write comments explaining WHY (non-obvious decisions):
- `delay = 2 ** n  # Exponential backoff for Stripe rate limits`
- `cache.clear()  # Prevent stale data after config reload`

**Test:** Can a developer understand by reading the code? YES → No comment.

### Test Quality - MANDATORY

**NEVER write trivial tests.** Apply Test Value Framework:
- **CRITICAL:** Business logic, security boundaries, data integrity
- **SKIP:** Language features, framework code, implementation details

### Commit Messages - MANDATORY

**Body explains WHY, not WHAT.** The diff shows what changed. The body's job is context that will be lost: the problem, the motivation, the design decision.

**NEVER include in commit messages:**
1. Test/lint/format pass status (passing is a prerequisite, not an accomplishment)
2. File names or line counts (`git show --stat` exists)
3. Method/function/class inventories (the diff shows these)
4. "Comprehensive", "complete", "full coverage" (marketing, not information)

**ALWAYS use correct type prefix:**
- `refactor:` when moving/restructuring existing code (NOT `feat:`)
- `feat:` only for genuinely new functionality

**Test:** Does the body help a developer understand WHY this change was made 6 months from now? YES → keep. NO → cut.
