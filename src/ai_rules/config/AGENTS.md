# LLM Behavioral Rules and Instructions

Instructions organized by priority level to ensure critical requirements are never compromised.

---

## Priority 1: Core Operating Principles

### Security-First Code Generation
**Rule:** For ALL code handling external input, authentication, or sensitive data, apply this two-stage approach:

**Stage 1:** Implement functional requirements
**Stage 2:** Security hardening checklist:
- Validate input at boundaries | Prevent SQL injection (parameterized queries) | Block XSS (output encoding) | Verify authentication | Check authorization | Rate limit APIs | Sanitize error messages | No hardcoded secrets | Audit log sensitive operations

**Why:** 40%+ of LLM-generated code contains vulnerabilities when security isn't explicitly prompted.

### Workflow Management
**Rule:** Create TODO list before multi-step tasks, keep updated as you complete each task.
**Why:** Ensures systematic completion, prevents missed steps, provides visible progress tracking.
**When to skip:** Single-step trivial tasks.

### Documentation First
**Rule:** Read repository's README and documentation before any actions.
**Implementation:** Start by reading: README.md, CONTRIBUTING.md, docs/, .github/, Makefile/Justfile.
**Why:** Prevents violating conventions, using wrong commands, missing context.

### Project-Specific Tooling
**Rule:** Use project-specific commands when available.
**Examples:** Makefile→`make` | Justfile→`just` | package.json→`npm run` | pyproject.toml→`uv`/`poetry`
**Why:** Encapsulates complexity, ensures consistency, prevents common mistakes.

### Software Engineering Standards

Apply these practices to all code:

**1. DRY Principle:** Extract repeated blocks (3+ occurrences) into functions
**2. Single Responsibility:** Each function/class handles ONE concern
**3. Clear Naming:**
```python
# ✅ Good
def get_user_by_email(email: str) -> User: pass
# ❌ Bad
def func1(x): pass
```

**4. Error Handling at Boundaries:**
```python
# ✅ Good - specific errors
try:
    response = external_api.call()
except ConnectionError as e:
    logger.error(f"API failed: {e}")
    raise ServiceUnavailableError("Payment service unavailable")
# ❌ Bad - bare except
except: pass
```

**5. Input Validation:** Validate ALL user input and external API responses at system boundaries.

**Why:** Reduces bugs 60%, improves maintainability, makes code reviewable.

### Explore Before Implement
**Rule:** Before implementing new functionality, explore the codebase for existing code that can be extended or reused.

**Mandatory Exploration Phase:**
1. Search for similar endpoints, functions, or patterns in the codebase
2. Identify existing abstractions that handle related concerns
3. Evaluate if requirements can be met by extending existing code vs. creating new

**Decision Framework:**
| Scenario | Action |
|----------|--------|
| Existing endpoint can handle the use case with minor changes | Extend existing code |
| Existing abstraction covers 80%+ of requirements | Add to existing, don't duplicate |
| Truly novel functionality with no overlap | Create new (document why) |

**Example:**
```python
# ❌ Bad: Created new /fork_session endpoint with duplicate logic
def fork_session(session_id, from_message_id):
    # 50 lines duplicating message handling, validation, state management

# ✅ Good: Extended existing edit_message to support forking
def edit_message(message_id, content, fork=False):
    # Reuses existing validation, state management, adds fork parameter
```

**Why:** LLMs tend to implement "clean" new solutions rather than integrate with existing code. This creates duplication, increases maintenance burden, and misses opportunities to leverage battle-tested implementations.

**Relationship to Simplicity:** This rule complements "Simplicity Over Engineering" - both avoid unnecessary code. Simplicity says "don't over-abstract NEW code"; this rule says "don't ignore EXISTING code that already solves the problem."

### Simplicity Over Engineering
**Rule:** Prioritize simplicity, avoid over-engineering.
**Guidelines:** Three similar lines beats premature abstraction | No helpers for one-time ops | Only add requested features | Design for current requirements | Only add configurability when needed NOW.

**Example:**
```python
# ✅ Simple
def process_payments(payments):
    for p in payments: validate(p); charge(p); notify(p)

# ❌ Over-engineered
class PaymentProcessor:
    def __init__(self, validator_factory, charger_strategy, notifier_adapter):
        # ...when you only ever use one validator/charger/notifier
```

**Why:** Over-engineering wastes time, adds complexity, often needs removal later.

### Planning Without Timelines
**Rule:** When generating plans, omit time estimates.
**Why:** Estimates are often wrong, not your decision, distract from technical requirements.

### Collaboration Protocol

**Rule:** Improve code quality through constructive collaboration.

**Decision Framework:**
1. **UNDERSTAND:** Are requirements clear? Better approaches? Maintenance implications? Edge cases?
2. **CLARIFY:** Ask specific questions for unclear/suboptimal requests
3. **PROPOSE:** Suggest alternatives with technical justification when you see better approaches
4. **IMPLEMENT:** Only proceed after alignment

**Example:**
```
User: "Loop through all users and check each one"
You: "I notice we're checking all users. Alternative: O(n) check all 100k users vs
O(log n) database index query - 1000x faster. Should I use indexed approach?"
```

**Challenge:** Unclear requirements | Security vulnerabilities | Performance issues | High maintenance cost | Missing error handling
**Don't challenge:** Clear decisions | User's style preferences (unless violate rules) | Tech choices already made

**Why:** Catches issues early, prevents technical debt, produces better outcomes.

---

## Priority 2: Technical Implementation Standards

### Python Requirements
**Dependency management:** `uv add pkg`, `uv sync`, `uv run pytest`
**Linting & formatting:** `ruff check .`, `ruff format .`
**Testing:** `pytest` (not unittest)
**Why:** Specified in project config, significantly faster (uv is 10-100x faster than pip), standard for this environment.

### Testing Standards
**Rule:** Test business logic and intended functionality, NOT implementation details.

**Write tests for:** Business logic with multiple paths | Error conditions & edge cases | Integration points | Security controls | Public API contracts
**Skip tests for:** Simple getters/setters | Framework code | Trivial types | UI styling | Private implementation details

**Example:**
```python
# ✅ Tests behavior
def test_user_registration_fails_with_duplicate_email():
    existing_user = User(email="test@example.com")
    db.save(existing_user)
    result = register_user(email="test@example.com", password="pass123")
    assert not result.success and "already exists" in result.error_message

# ❌ Tests implementation
def test_register_user_calls_hash_password():
    with patch('auth.hash_password') as mock:
        register_user(email="test@example.com", password="pass123")
        mock.assert_called_once()  # Who cares if it was called?
```

**Structure:** Arrange-act-assert | Names describe scenario: `test_<scenario>_<result>` | Independent (no shared state) | Deterministic
**Parametrize similar scenarios:** Use `@pytest.mark.parametrize` when testing the same logic with different inputs.
**Why:** Testing implementation makes tests brittle. Testing behavior ensures functionality works regardless of how it's implemented.

### AWS CLI Requirements
**Rule:** Include `--profile <account>-<env>--<role>` and `--region us-west-2` (unless region-agnostic).

**Format:** `--profile security-lake-staging--admin` (✅) not `--profile staging-admin` (❌)
**Validation:** Profile matches `^[a-z-]+-(dev|staging|production)--[a-z-]+$` | Region is `us-west-2`
**Example:** `aws s3 ls s3://bucket --profile data-lake-staging--admin --region us-west-2`
**Why:** Targets correct account, prevents accidental production changes, consistent deployment, clear audit trail.

### GitHub Integration
**Rule:** Use `gh` CLI commands: `gh pr view 123` | `gh pr create --title "..." --body "..."` | `gh issue list --label bug` | `gh pr checks`
**Why:** Consistent tooling, better formatting, handles auth automatically, integrates with local git.

---

## Priority 3: Style & Formatting Guidelines

### Code Comment Standards
**Rule:** ONLY add comments explaining WHY, NOT WHAT. Never add code comments that simply restate what the code does.

**Prohibited - Comments that restate code behavior (WHAT):**
```python
counter += 1  # Increment counter by 1
for user in users:  # Loop through users
result = calculate_total(items)  # Calculate the total from items
```

**Required - Comments that explain reasoning or context (WHY):**
```python
# Use exponential backoff to avoid Stripe API rate limiting
delay = 2 ** retry_count

# Sort DESC to show newest first (PM requirement ticket #482)
results.sort(key=lambda x: x.timestamp, reverse=True)

# Must validate BEFORE database query to prevent SQL injection
sanitized = validate_and_sanitize(user_input)
```

**Why:** Code should be self-explanatory via naming. Comments that restate what code does become outdated and add noise. Comments explaining WHY preserve critical context (business rules, security requirements, performance considerations) not visible in the code itself.

### Whitespace Standards
**Rule:** Remove ALL trailing whitespace | Ensure blank lines have NO whitespace | Preserve existing newlines | All files end with single newline
**Why:** Prevents git diff noise, maintains consistency, required by linters/pre-commit hooks.

### Emoji Policy
**Rule:** Use plain text without emojis unless explicitly requested.
**Why:** Professional standards, encoding issues, accessibility, not appropriate for production code.

---

## Model-Specific Behavioral Adaptations

| Model Type | Key Traits | Optimization Strategies |
|------------|------------|------------------------|
| **Claude** | Requires EXPLICIT instructions, literal interpretation, excels at multi-step procedures | Use XML tags for structure, request extended thinking (4.5+), break into numbered steps, state all constraints |
| **GPT** | Literal interpretation, structured output | JSON mode for structured output, complete format examples, system messages for constraints |
| **Reasoning (o3, DeepSeek)** | Built-in reasoning, zero-shot best | Do NOT use few-shot examples, allow 30+ sec thinking, ask for reasoning shown, focus on problem definition |

---

## Context Window Optimization

Structure prompts for large codebases:
```
<critical_context>Most important: current task, key constraints</critical_context>
<background>Supporting info: codebase structure, related systems</background>
<requirements>Restate key points from critical_context</requirements>
```
**Why:** LLMs have highest attention at beginning (primacy), end (recency), and tagged sections.

---

## Quick Reference Checklist

Before completing tasks:
☐ Read README & docs | ☐ Create TODO list (multi-step) | ☐ Explore codebase before implementing new features | ☐ Apply security checklist (external-facing code) | ☐ Use project tooling (Makefile/Justfile) | ☐ Follow DRY & single responsibility | ☐ Add only WHY comments | ☐ Remove trailing whitespace | ☐ File ends with newline | ☐ Test behavior not implementation | ☐ AWS has --profile & --region | ☐ Keep simple, avoid over-engineering | ☐ Ask clarifying questions

---
