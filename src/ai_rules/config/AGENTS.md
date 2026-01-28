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
**Rule:** Create TODO list before multi-step tasks, update as you complete each task.
**Skip:** Single-step trivial tasks.

### Autonomous Coding Workflow

**Trigger:** After completing non-trivial code implementation (new features, bug fixes, refactors affecting behavior), automatically execute this workflow before presenting results to the user.

**Stages:**

| Stage | Action | Proceed when |
|-------|--------|--------------|
| 1. Implement | Write/modify code to meet requirements | Code compiles/runs without errors |
| 2. Test | Invoke `test-writer` skill for changed code | Tests written and passing |
| 3. Review | Invoke `code-reviewer` skill (runs in isolated subagent) | Review findings returned |
| 4. Fix | Address all 🔴 MUST FIX issues, then 🟡 SHOULD FIX issues | All blocking issues resolved |
| 5. Re-review | If fixes were made in Stage 4, return to Stage 3 | Review returns no 🔴 or 🟡 issues |

**Stop condition:** Do NOT automatically invoke `pr-creator`. Wait for explicit user request to create PR.

**Skip workflow when:** Changes are documentation-only, config/settings tweaks, typo fixes, or user explicitly requests "quick fix" or "no review needed."

**Why this workflow:** Catches 40%+ of bugs and security issues before they reach production. The isolated review subagent prevents context pollution while enabling deep codebase analysis.

### Documentation First
**Rule:** Read README.md, CONTRIBUTING.md, docs/, .github/, Makefile/Justfile before actions.

### Project Tooling
**Rule:** Use project commands: Makefile→`make` | Justfile→`just` | package.json→`npm run` | pyproject.toml→`uv`/`poetry`

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

1. **UNDERSTAND:** Requirements clear? Better approaches? Edge cases?
2. **CLARIFY:** Ask specific questions for unclear/suboptimal requests
3. **PROPOSE:** Suggest alternatives with technical justification
4. **IMPLEMENT:** Only after alignment

**Challenge:** Unclear requirements | Security gaps | Performance issues | High maintenance cost
**Don't challenge:** Clear decisions | Style preferences | Decided tech choices

---

## Technical Standards

### Python
**Dependencies:** `uv add pkg`, `uv sync`, `uv run pytest`
**Linting:** `ruff check .`, `ruff format .`
**Testing:** `pytest` (not unittest)

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
