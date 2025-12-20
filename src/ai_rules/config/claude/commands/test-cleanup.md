---
description: Audit and optimize test suite by removing trivial tests and consolidating valuable ones
allowed-tools: AskUserQuestion, Bash, Edit, Glob, Grep, Read, TodoWrite, Write
model: inherit
---

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || pwd`
- Test framework: !`[ -f package.json ] && grep -E '"(test|jest|mocha|vitest)"' package.json | head -1 || [ -f pytest.ini ] && echo "pytest" || [ -f go.mod ] && echo "go test" || echo "unknown"`
- Test file count: !`find . -type f \( -name "*test*" -o -name "*spec*" \) 2>/dev/null | wc -l`
- Test execution time: !`[ -f package.json ] && npm test -- --listTests 2>/dev/null | wc -l || echo "N/A"`
- Coverage config: !`[ -f .coveragerc ] && echo "Python coverage" || [ -f jest.config.js ] && echo "Jest coverage" || [ -f .nycrc ] && echo "NYC coverage" || echo "No coverage config"`

# Test Suite Optimization

Audit all tests to identify opportunities for consolidation, refactoring, or removal. Maximize test value while minimizing maintenance burden.

## Test Value Framework

**1. Critical (MUST KEEP):** Business logic with branches | Security boundaries (auth, authz, input validation) | Data integrity (transactions, constraints) | User-facing functionality | Integration with external systems | Financial/regulatory logic

**2. Valuable (KEEP):** Error handling for external deps | Edge cases with production impact history | State transitions in complex workflows | API contract validation | Performance regression detection | Cross-cutting concerns (logging, monitoring)

**3. Questionable (EVALUATE):** Simple getters/setters with no logic | Framework functionality (already tested by framework) | Tests with >80% mocking (testing mocks, not code) | Overly coupled to implementation | Duplicate coverage of same behavior

**4. Trivial (REMOVE):** Testing language features ("JS can add numbers") | Testing third-party libraries ("axios makes HTTP") | Always-pass tests (never fail regardless of implementation) | Generated tests with no assertions | Verifying constants/config values

## Systematic Audit Process

### Phase 1: Inventory

Review Context metrics (pre-loaded): framework, file count, coverage config, execution time

**Categorize tests:** Unit (individual functions/classes) | Integration (multiple components) | E2E (full workflows) | Performance | Contract/API

### Phase 2: Analysis

Apply decision framework to each test:

**1. What business rule does this validate?** If "none"/unclear → REMOVE

**2. Has this caught a real bug?** Check git history for test failures in CI. If always passes → QUESTIONABLE

**3. Does this document important behavior?** Would removing make system unclear? → KEEP | Redundant with other tests? → CONSOLIDATE

**4. Would removing increase risk?** High risk (payments, auth, data loss) → KEEP | Low risk (UI formatting, logs) → EVALUATE

**Identify patterns:** Repeated setup → Consolidate into fixtures | Multiple tests same behavior → Merge | Zero assertions → Remove | Mock everything → Reconsider if testing anything real

### Phase 3: Execute Optimizations

**REMOVE candidates:**
1. Verify no unique value
2. Confirm other tests cover behavior (if any)
3. Delete test + unused fixtures/helpers
4. Run suite to confirm no gaps

**CONSOLIDATE candidates:**
1. Identify overlapping coverage
2. Create single comprehensive test for all cases
3. Remove individual redundant tests
4. Verify consolidated test provides same coverage

**REFACTOR candidates:**
1. Extract repeated setup to shared fixtures
2. Replace implementation testing with behavior testing
3. Reduce mocking to essential external deps only
4. Simplify assertions to focus on outcomes, not internals

**KEEP candidates:**
1. Verify maintainable and clear
2. Ensure runs quickly (flag slow >1s)
3. Check has clear failure messages
4. Document why important if non-obvious

**Process:** Start with REMOVE (fastest wins) | Consolidate related tests | Refactor questionable | Run tests after each batch | Monitor coverage for gaps

### Phase 4: Validation & Reporting

**Run checks:**
```bash
npm test             # Full suite
npm run coverage     # Coverage report
npm run lint         # Unused imports/fixtures
npm run type-check   # If applicable
```

**Verify:** Test count reduced | Execution time improved (target: 20-30% faster) | Critical path coverage maintained (≥80% for business logic) | No new failures

**Report summary:**
```
Test Optimization Complete

Metrics:
- Tests removed: X (Y% reduction)
- Tests consolidated: Z groups
- Execution time: Before Xs → After Ys (Z% improvement)
- Coverage: Maintained at N%

Categories removed:
- Trivial tests: X
- Framework tests: Y
- Implementation-only: Z

✓ All tests passing
✓ Coverage maintained
```

## Decision Examples

**Remove:**
```python
# Testing language feature
def test_list_append():
    lst = []; lst.append(1); assert len(lst) == 1  # Python lists work!

# Testing framework
def test_mock_called():
    mock = Mock(); mock(); assert mock.called  # Mocks work!
```

**Keep:**
```python
# Business logic
def test_discount_with_coupon():
    cart = Cart([Item(100)]); cart.apply_coupon("SAVE20"); assert cart.total() == 80

# Security boundary
def test_unauthorized_denied():
    response = api.delete("/user/123", auth=None); assert response.status == 403
```

**Consolidate:**
```python
# Before: 3 separate
def test_user_valid_email(): ...
def test_user_with_name(): ...
def test_user_timestamp(): ...

# After: 1 comprehensive
def test_user_creation():
    user = create_user(email="test@x.com", name="Test")
    assert user.email == "test@x.com" and user.name == "Test" and user.created_at
```

## Pitfalls to Avoid

- Don't remove tests that caught bugs (check git history)
- Don't reduce critical path coverage (<80% business logic)
- Don't remove just because slow (optimize instead)
- Don't delete edge case tests (prevent regression)
- Don't remove integration in favor of unit only (both have value)

## Critical Requirements

**Analysis:** Apply framework to each test | Check git history for value | Identify patterns for consolidation

**Execution:** Process systematically (REMOVE → CONSOLIDATE → REFACTOR → KEEP) | Run tests after each batch | Monitor coverage continuously

**Validation:** Full suite passes | Coverage of critical paths ≥80% | Execution time improved 20-30% | Zero trivial tests remain

**Success Criteria:** Lean suite focused on business logic and integration | Test failures provide actionable errors | Reduced maintenance burden (fewer brittle tests)

Goal: Create valuable test suite protecting against bugs while removing tests providing no real value.
