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
- Recent test failures: !`git log --grep="test\|fix" --oneline -10 2>/dev/null | head -5`

# Test Suite Optimization

Perform comprehensive audit of all tests in the codebase to identify opportunities for consolidation, refactoring, or removal. Focus on maximizing test value while minimizing maintenance burden.

## Test Value Framework

Classify each test using this hierarchy:

**1. Critical (MUST KEEP)**
- Business logic with multiple code paths
- Security boundaries (authentication, authorization, input validation)
- Data integrity checks (transactions, constraints)
- User-facing functionality that directly impacts users
- Integration points with external systems
- Financial calculations or regulatory compliance logic

**2. Valuable (KEEP)**
- Error handling for external dependencies
- Edge cases with production impact history
- State transitions in complex workflows
- API contract validation
- Performance regression detection
- Cross-cutting concerns (logging, monitoring)

**3. Questionable (EVALUATE)**
- Simple getters/setters with no logic
- Framework functionality already tested by framework
- Tests with >80% mocking (testing mocks, not code)
- Overly coupled to implementation details
- Duplicate coverage of same behavior

**4. Trivial (REMOVE)**
- Testing language features (e.g., "JavaScript can add numbers")
- Testing third-party libraries (e.g., "axios makes HTTP requests")
- Tests that never fail (always pass regardless of implementation)
- Generated tests with no assertions
- Tests verifying constants or configuration values

## Systematic Audit Process

### Phase 1: Inventory

**Review metrics from Context above:**
- Test framework, file count, and coverage config are pre-loaded
- Measure execution time using the detected test framework
- Run coverage report if coverage config exists

**Categorize tests:**
- Unit tests (test individual functions/classes)
- Integration tests (test multiple components together)
- E2E tests (test full user workflows)
- Performance tests
- Contract/API tests

### Phase 2: Analysis

Apply decision framework to each test. For every test, ask:

**1. What business rule does this validate?**
- If answer is "none" or unclear → REMOVE

**2. Has this test ever caught a real bug?**
- Check git history for test failures in CI
- If always passes → QUESTIONABLE

**3. Does this test document important behavior?**
- Would removing it make system behavior unclear? → KEEP
- Is it redundant with other tests? → CONSOLIDATE

**4. Would removing this test increase risk?**
- High risk area (payments, auth, data loss) → KEEP
- Low risk area (UI formatting, logs) → EVALUATE

**Identify patterns:**
- Repeated test setup → Consolidate into shared fixtures
- Multiple tests for same behavior → Merge into single comprehensive test
- Tests with zero assertions → Remove
- Tests that mock everything → Reconsider if testing anything real

### Phase 3: Optimization Actions

**For REMOVE candidates:**
1. Verify test provides no unique value
2. Confirm other tests cover the behavior (if any)
3. Delete test and unused fixtures/helpers
4. Run full test suite to confirm no gaps

**For CONSOLIDATE candidates:**
1. Identify overlapping test coverage
2. Create single comprehensive test covering all cases
3. Remove individual redundant tests
4. Verify consolidated test provides same coverage

**For REFACTOR candidates:**
1. Extract repeated setup to shared fixtures
2. Replace implementation testing with behavior testing
3. Reduce mocking to essential external dependencies only
4. Simplify assertions to focus on outcomes, not internals

**For KEEP candidates:**
1. Verify test is maintainable and clear
2. Ensure test runs quickly (flag slow tests >1s)
3. Check test has clear failure messages
4. Document why test is important if non-obvious

### Phase 4: Execute Changes

**Process systematically:**
1. Start with obvious REMOVE candidates (fastest wins)
2. Consolidate related tests (reduce duplication)
3. Refactor questionable tests (improve quality)
4. Run tests after each batch of changes
5. Monitor coverage to ensure no gaps introduced

**Track progress:**
- Count tests before/after
- Measure execution time improvement
- Verify coverage maintained or improved
- Document any intentional coverage gaps

### Phase 5: Validation

**Run comprehensive checks:**
```bash
# Full test suite
npm test

# Coverage report
npm run coverage

# Linter (might catch unused imports/fixtures)
npm run lint

# Type checking (if applicable)
npm run type-check
```

**Verify metrics:**
- Test count reduced by removing trivial tests
- Execution time improved (target: 20-30% faster)
- Coverage of critical paths maintained (≥80% for business logic)
- No new test failures introduced

## Decision Criteria Examples

**Remove:**
```python
# Testing Python language feature
def test_list_append():
    lst = []
    lst.append(1)
    assert len(lst) == 1  # Python lists work!

# Testing framework functionality
def test_mock_called():
    mock = Mock()
    mock()
    assert mock.called  # Mocks work!
```

**Keep:**
```python
# Testing business logic
def test_discount_calculation_with_coupon():
    cart = Cart(items=[Item(price=100)])
    cart.apply_coupon("SAVE20")
    assert cart.total() == 80  # Business rule: 20% discount

# Testing security boundary
def test_unauthorized_access_denied():
    response = api.delete("/user/123", auth=None)
    assert response.status == 403  # Security: require auth
```

**Consolidate:**
```python
# Before: 3 separate tests
def test_user_creation_with_valid_email(): ...
def test_user_creation_with_name(): ...
def test_user_creation_stores_timestamp(): ...

# After: 1 comprehensive test
def test_user_creation_with_all_fields():
    user = create_user(email="test@example.com", name="Test")
    assert user.email == "test@example.com"
    assert user.name == "Test"
    assert user.created_at is not None
```

## Common Pitfalls to Avoid

- **Don't remove tests that caught bugs in the past**: Check git history
- **Don't reduce coverage of critical paths**: Maintain ≥80% for business logic
- **Don't remove tests just because they're slow**: Optimize instead
- **Don't delete edge case tests**: They often prevent regression
- **Don't remove integration tests in favor of unit tests**: Both have value

## Success Metrics

After optimization, verify:
✓ Test suite runs 20-30% faster
✓ Zero trivial tests remain (language features, framework tests)
✓ Critical path coverage maintained (≥80%)
✓ All remaining tests have clear purpose
✓ Test failures provide actionable error messages
✓ Reduced maintenance burden (fewer brittle tests)

## Reporting

Provide summary after completion:
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
- Implementation-only tests: Z

All tests passing: ✓
Coverage maintained: ✓
```

Your goal is to create a lean, valuable test suite that focuses on critical business logic and system integration while removing tests that provide no real protection against bugs.
