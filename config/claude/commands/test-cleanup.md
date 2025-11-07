---
description: Perform an audit of the tests in the codebase to see if any can be consolidated, refactored, or removed
model: inherit
---

# Test Cleanup

Perform an audit and review of all tests in the codebase and identify opportunites for tests that can be consolidated, refactored, or removed because they're trivial or unhelpful. Remember we should only have tests for the most critical application functionality or business logic and should never have simple tests that only test the implementation. You should also remove any unused or unnecessary test fixtures. Run all tests when you're done to make sure there's no regression in the remaining tests.
