# PLAN.md Templates

## Standard PLAN__TASK Structure

```markdown
# PLAN__TASK_NAME

## Overview

[1-2 paragraph summary of what this plan accomplishes, the architectural approach chosen, and key design decisions with reasoning. This section must provide enough context for a new agent to understand the plan without exploring the codebase.]

## Scope

**Features:**
- [Feature 1]
- [Feature 2]

**Components:**
- [Component 1 modified/created]
- [Component 2 modified/created]

**Files Modified/Created:**
- `path/to/file1.py` - [Role: what this file does in context of the plan]
- `path/to/file2.ts` - [Role: what this file does in context of the plan]

**Integrations:**
- [External system integration 1]
- [External system integration 2]

## Purpose

**Problem:**
[Describe the problem being solved]

**Value:**
[What value this provides]

**Requirements:**
- [Requirement 1]
- [Requirement 2]

**Context:**
[Additional context that helps understand the plan -- include architectural decisions, rejected alternatives with reasoning, and any constraints or assumptions a new agent would need to know]

## Implementation Details

### Phase 1: Setup & Foundation
   [DONE] Task 1 description
   [DONE] Task 2 description
      [DONE] Subtask 2.1
      [IN PROGRESS] Subtask 2.2
   [TODO] Task 3 description -- include approach, target files, and any dependencies on prior tasks

### Phase 2: Core Implementation (depends on: Phase 1)
   [IN PROGRESS] Task 1 description
   [TODO] Task 2 description -- include approach and target files

### Phase 3: Testing & Verification
   [TODO] Test suite for feature X
   [TODO] Integration tests

## Gotchas & Issues Encountered

Capture any pitfalls, constraints, or non-obvious behaviors discovered during implementation. A new agent should not have to re-discover these.

### Issue 1: [Title]
**Problem:** [Description of issue]
**Solution:** [How it was resolved]
**Impact:** [What breaks or goes wrong if this is ignored]
**File:** `path/to/file.py:123`

## Verification

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Documentation updated

## Files Changed Summary

| File | Action | Description |
|------|--------|-------------|
| `path/to/file1.py` | Modify | Added feature X |
| `path/to/file2.ts` | Create | New component for Y |

## Status

- Phase 1: [2/3] Complete
- Phase 2: [1/2] In Progress
- Phase 3: [0/2] Not Started

**Overall:** [3/7] Tasks Complete

## Plan Updates

### 2025-01-15 14:30
- Added Phase 3 after discovering need for integration tests
- Cancelled old approach for Task 2.2, using new pattern instead

### 2025-01-14 09:00
- Initial plan created
```

## Simple Flat List Structure

For straightforward tasks without phases:

```markdown
# PLAN__BUG_FIX

## Overview

Fix authentication bug where users with special characters in email can't log in.

## Scope

- `src/auth/validator.py`
- `tests/test_auth.py`

## Purpose

**Problem:** Email validation rejects valid emails with `+` or `.` characters

**Value:** Users can log in with any valid email format

## Implementation Details

[DONE] Investigate email validation logic in `validator.py`
[DONE] Identify regex pattern issue
[DONE] Update regex to RFC 5322 compliant pattern
[IN PROGRESS] Add unit tests for edge cases
   [DONE] Test email with + character
   [TODO] Test email with multiple dots
[TODO] Update documentation

## Verification

- [x] Existing tests pass
- [ ] New tests added
- [ ] Manual testing with edge case emails
```

## Multi-Phase Complex Structure

For large features with dependencies:

```markdown
# PLAN__API_MIGRATION

## Overview

Migrate REST API from Express to FastAPI, improving performance and type safety while maintaining backward compatibility.

## Scope

**Features:**
- All 15 existing API endpoints
- Authentication middleware
- Error handling
- Request validation

**Components:**
- API server (FastAPI)
- Database layer (SQLAlchemy)
- Authentication (JWT)
- Documentation (OpenAPI)

**Files:**
- New: `src/api/main.py`, `src/api/routes/*.py`
- Modify: `src/database/models.py`
- Delete: `src/server.js`, `src/routes/*.js`

## Purpose

**Problem:**
- Current Express API lacks type safety
- Performance bottlenecks under load
- Inconsistent error handling

**Value:**
- 3x faster response times
- Automatic API documentation
- Compile-time type checking
- Better developer experience

**Requirements:**
- Zero downtime migration
- Backward compatible responses
- Maintain existing auth tokens

## Implementation Details

### Phase 1: Foundation & Setup
   [DONE] Set up FastAPI project structure
   [DONE] Configure SQLAlchemy with existing PostgreSQL
   [DONE] Implement JWT auth middleware
      [DONE] Token validation
      [DONE] User context injection
      [DONE] Test with existing tokens
   [DONE] Set up pytest testing framework

### Phase 2: Core Endpoint Migration
   [IN PROGRESS] Migrate user endpoints
      [DONE] GET /users
      [DONE] GET /users/:id
      [IN PROGRESS] POST /users
      [TODO] PUT /users/:id
      [TODO] DELETE /users/:id
   [TODO] Migrate post endpoints
      [TODO] GET /posts
      [TODO] POST /posts
      [TODO] PUT /posts/:id
      [TODO] DELETE /posts/:id
   [TODO] Migrate comment endpoints

### Phase 3: Advanced Features
   [TODO] Implement request rate limiting
   [TODO] Add caching layer (Redis)
   [TODO] Set up WebSocket support for real-time updates

### Phase 4: Migration & Deployment
   [TODO] Blue-green deployment setup
   [TODO] Database migration scripts
   [TODO] Rollback procedure documentation
   [TODO] Performance benchmarking
   [TODO] Production deployment

## Gotchas & Issues Encountered

### Issue 1: SQLAlchemy Relationship Loading
**Problem:** N+1 query problem with user->posts relationship causing 100+ queries per request
**Solution:** Used `joinedload` and `selectinload` strategically
**File:** `src/database/models.py:45`

### Issue 2: JWT Token Compatibility
**Problem:** Express used different JWT library with incompatible payload structure
**Solution:** Added compatibility layer to read both old and new token formats
**File:** `src/api/auth.py:78`

## Verification

**Phase 1:**
- [x] Auth tests pass (15/15)
- [x] Token compatibility verified with production tokens

**Phase 2:**
- [ ] All endpoints maintain exact response format
- [ ] Performance tests show 3x improvement
- [ ] Integration tests pass

**Phase 3:**
- [ ] Rate limiting tested under load
- [ ] Cache hit rate >80%

**Phase 4:**
- [ ] Zero downtime verified in staging
- [ ] Rollback tested successfully

## Files Changed Summary

| File | Action | Description |
|------|--------|-------------|
| `src/api/main.py` | Create | FastAPI app entry point |
| `src/api/routes/users.py` | Create | User endpoint handlers |
| `src/database/models.py` | Modify | Add SQLAlchemy models |
| `src/server.js` | Delete | Old Express server |

## Status

- Phase 1: [4/4] Complete ✓
- Phase 2: [2/9] In Progress
- Phase 3: [0/3] Not Started
- Phase 4: [0/4] Not Started

**Overall:** [6/20] Tasks Complete (30%)

## Plan Updates

### 2025-01-16 10:00
- Added Phase 3 after realizing need for caching
- Split Phase 2 into user/post/comment endpoints for clearer tracking

### 2025-01-15 14:00
- Added Gotchas section for JWT token compatibility issue
- Updated verification checklist with specific metrics

### 2025-01-14 09:00
- Initial plan created from ExitPlanMode
```

## Status Label Usage

### [TODO]
Not started. Use for:
- Future work
- Planned tasks with no implementation evidence

### [IN PROGRESS]
Partially complete. Use when:
- Single indicator of work (one file edited)
- Task started but not all subtasks done
- Code written but tests missing

### [DONE]
Complete. Use when:
- Multiple indicators (file edited + tests + commit)
- All subtasks completed
- Verification criteria met

### [BLOCKED]
Cannot proceed. Always include reason:
```
[BLOCKED - waiting for API key from ops team] Configure SendGrid integration
[BLOCKED - depends on #2 completing] Add notification tests
```

### [CANCELLED - plan changed]
No longer relevant:
```
[CANCELLED - plan changed] Use Redux for state management
   Reason: Decided on Zustand instead for simplicity
```

## Evidence Strength Guidelines

### Strong Evidence (→ [DONE])
Multiple indicators:
- File written/edited via Write/Edit tool
- Mentioned in completion phrase ("I've implemented X")
- Tests added
- Related TodoWrite marked complete

Example:
```
Session activity:
- Write: src/api/users.py (POST endpoint implementation)
- Write: tests/test_users.py (unit tests for POST)
- "I've implemented the user creation endpoint with validation"

→ [DONE] Implement POST /users endpoint
```

### Medium Evidence (→ [IN PROGRESS])
Single indicator:
- File edited once
- Mentioned in progress phrase ("I'm working on X")
- Partial subtask completion

Example:
```
Session activity:
- Edit: src/api/users.py (added validation function)

→ [IN PROGRESS] Implement POST /users endpoint
```

### Weak/No Evidence (→ [TODO])
- Mentioned in plan but no tool calls
- Future work discussed
- No file changes

## Hierarchical Nesting

Use 3-space indentation for hierarchy:

```markdown
[DONE] Phase 1: Setup
   [DONE] Install dependencies
   [DONE] Configure database
      [DONE] Create migration scripts
      [DONE] Run initial migration
   [IN PROGRESS] Set up authentication
      [DONE] Install JWT library
      [TODO] Implement middleware
```

## File Path References

Always include specific file paths:
```markdown
[DONE] Update user model in `src/models/user.py`
[TODO] Add validation tests in `tests/unit/test_validation.py`
```

Not:
```markdown
[DONE] Update user model
[TODO] Add tests
```

## Task Name Format

Valid (1-2 uppercase words, single underscores):
- `AUTH_FLOW`
- `API_MIGRATION`
- `SLACK_FORMATTING`
- `WEBSOCKET`
- `DATABASE`

Invalid:
- `auth_flow` (lowercase)
- `AUTH__FLOW` (double underscore)
- `TOO_MANY_WORDS` (>2 words)
- `Auth-Flow` (hyphens not underscores)
