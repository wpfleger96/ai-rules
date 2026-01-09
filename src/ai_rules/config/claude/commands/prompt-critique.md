---
description: Analyze your historical Claude Code prompts and get personalized feedback on how to improve your prompting technique
allowed-tools: Bash, Glob, Grep, Read, Write, Skill, AskUserQuestion
model: sonnet
---

# Prompt Critique Workflow

You are an expert prompt engineering coach analyzing the user's historical Claude Code prompts to provide personalized, actionable feedback.

## Context

- User home: !`echo $HOME`
- Projects dir: !`ls -d ~/.claude/projects 2>/dev/null || echo "NOT_FOUND"`
- Current date: !`date -u +"%Y-%m-%dT%H:%M:%SZ"`
- Arguments: `${ARGS}` (depth: quick|thorough, optional custom output path)

## Argument Parsing

Parse `${ARGS}` to extract:
1. **depth**: First argument, defaults to `quick`
   - `quick`: 5-10 prompts from 3-4 projects
   - `thorough`: 20-30 prompts from 5-6 projects
2. **output-path**: Second argument (optional), defaults to `~/.claude/reports/prompt-critique-[timestamp].md`

## Phase 0: Invoke prompt-engineer Skill

**REQUIRED FIRST STEP:** Invoke the `prompt-engineer` skill using the Skill tool to load prompt engineering best practices knowledge.

This gives you access to evaluation criteria:
- Framework selection (Architecture-First, CO-STAR, ROSES)
- Model-specific anti-patterns (Claude 4 explicitness, reasoning model zero-shot)
- Validated techniques vs debunked myths
- Context window optimization
- Security prompting patterns
- Completeness checklists

## Phase 1: Session Discovery

**Goal**: Find recent, diverse sessions across multiple projects

### Step 1: List Project Directories
Use Bash to list project directories sorted by modification time:
```bash
ls -lt ~/.claude/projects/ | grep '^d' | head -20
```

### Step 2: Select Projects
Based on depth argument:
- **quick**: Select 3-4 most recently active projects
- **thorough**: Select 5-6 most recently active projects

Ensure diversity - avoid selecting multiple sessions from the same project unless necessary.

### Step 3: Find Session Files
For each selected project directory, find the most recent JSONL file:
```bash
ls -t ~/.claude/projects/<project-dir>/*.jsonl | head -1
```

## Phase 2: Prompt Extraction

**Goal**: Parse JSONL session files and extract user prompts and detect model used

For each selected session file:

### Step 1: Read Session File
Use Read tool to read the entire JSONL file.

### Step 2: Detect Model Used in Session
Scan for assistant messages to determine which model was used:
- Look for `type: "assistant"` entries
- Extract `message.model` field (e.g., `claude-sonnet-4-5-20250929`, `claude-opus-4-5-20251101`)
- Parse to friendly name:
  - `claude-sonnet-4-5-*` → "Claude Sonnet 4.5"
  - `claude-opus-4-5-*` → "Claude Opus 4.5"
  - `claude-haiku-4-5-*` → "Claude Haiku 4.5"
- Track the model for this session

### Step 3: Get Session Timestamp
Determine when the session ended:
- Use file modification time: `stat -f "%Sm" -t "%Y-%m-%d %H:%M" <file.jsonl>`
- OR extract `timestamp` from the last entry in the JSONL file
- Format as: `YYYY-MM-DD HH:MM` (local time)

### Step 4: Parse JSON Lines for User Prompts
Process each line as a separate JSON object. Filter for user messages with these criteria:

**Include if**:
- `type: "user"`
- `message.content` is not empty
- Does NOT contain `[Request interrupted by user for tool use]`
- `isSidechain` is false or not present

**Extract these fields**:
```python
{
  "content": message.content,  # Handle string or list[dict] format
  "timestamp": timestamp,
  "sessionId": sessionId,
  "project": <decode project name from directory>,
  "model": <detected model from Step 2>,
  "sessionTimestamp": <session end time from Step 3>,
  "uuid": uuid
}
```

**Important**: `message.content` can be:
- A string: `"my prompt text"`
- A list of content blocks: `[{"type": "text", "text": "my prompt"}, ...]`

When it's a list, concatenate all text from blocks with `type: "text"`.

### Step 5: Decode Project Names
Project directory names are encoded (e.g., `-Users-wpfleger-Development-Personal-ai-rules`).
Decode by:
1. Remove leading `-`
2. Replace remaining `-` with `/`
3. Extract project name (last path component)

## Phase 3: Prompt Sampling

**Goal**: Select representative prompts for analysis

### Selection Criteria

1. **Length**: Prefer longer, substantive prompts (>50 characters)
2. **Diversity**: 2-3 prompts per project
3. **Variety**: Mix of different prompt types:
   - Questions ("How do I...", "What is...")
   - Requests ("Please add...", "Can you...")
   - Follow-ups ("Also...", "Now...")
   - Complex instructions (multi-part prompts)

### Target Counts
- **quick**: Total 5-10 prompts
- **thorough**: Total 20-30 prompts

### Sampling Strategy
1. Sort prompts by timestamp (most recent first)
2. For each project, select 2-3 diverse prompts
3. Skip very short prompts (<20 chars) unless no better options
4. Skip duplicate/similar prompts from the same session

## Phase 4: Analysis

**Goal**: Evaluate prompts against prompt engineering best practices

For each sampled prompt, analyze across these dimensions:

### Evaluation Dimensions

| Dimension | What to Check | Examples |
|-----------|---------------|----------|
| **Explicitness** | Are requirements explicit vs implied? Claude 4 needs extreme clarity | Vague: "make it better" vs Explicit: "Add error handling for network timeouts" |
| **Framework Use** | Would a framework help structure this prompt? | Architecture-First for code, CO-STAR for writing, ROSES for decisions |
| **Context Positioning** | Is critical info at start/end? (avoids lost-in-middle) | Bad: buried in middle. Good: key requirement in first sentence |
| **Completeness** | Are constraints, edge cases, error handling specified? | Missing: no mention of auth. Complete: "validate user is authenticated" |
| **Anti-patterns** | Uses debunked techniques? | Role prompts ("act as expert"), $200 tip, excessive politeness |
| **Security Awareness** | For code prompts: is security mentioned? | Missing for input handling. Present: "sanitize user input to prevent XSS" |
| **Technique Match** | Could validated techniques help? | Complex task without CoT, reasoning task with few-shot examples |
| **Specificity** | Specific vs vague language? | Vague: "comprehensive", "good quality" vs Specific: "handle null values" |

### Identify Patterns
Look for recurring issues across multiple prompts:
- Pattern frequency (found in X/Y prompts)
- Impact level (High/Medium/Low)
- Specific examples to illustrate

### Prioritize High-Impact Improvements
Focus on:
1. **Security gaps** in code prompts (highest priority)
2. **Claude 4 explicitness** issues (very common, high impact)
3. **Framework opportunities** (substantial improvement)
4. **Debunked anti-patterns** (easy to fix, immediate benefit)

### Model-Specific Advice

When providing recommendations, consider which model(s) the user employed:

**Claude Sonnet 4.5 Characteristics:**
- Requires extreme clarity and explicit requirements
- Literal interpretation - won't infer or fill in gaps
- Best for: Fast iteration, well-defined tasks, structured workflows
- Common issues: Vague prompts, implicit requirements, assuming context

**Claude Opus 4.5 Characteristics:**
- More capable of inferring intent and nuanced understanding
- Better at handling ambiguous or complex reasoning tasks
- Best for: Open-ended tasks, complex analysis, creative work
- Common issues: Over-specification that constrains creative solutions

**Tagging Recommendations:**
- Tag advice as `[Sonnet 4.5]`, `[Opus 4.5]`, or `[All models]`
- If user used Sonnet for a task better suited to Opus (or vice versa), note it
- Example: `[Sonnet 4.5] Be more explicit about edge cases - Sonnet needs every requirement spelled out`
- Example: `[Opus 4.5] Consider giving Opus more creative freedom rather than prescribing exact implementation`
- Example: `[All models] Add security requirements for input validation`

## Phase 5: Report Generation

**Goal**: Create actionable markdown report

### Report Structure

```markdown
# Prompt Critique Report

- **Generated**: [ISO timestamp, e.g., 2025-01-09T17:30:00Z]
- **Sessions Analyzed**: [count] sessions
  - `[project-name]` - Session `[session-id-short]` ([Model]) - [session-timestamp]
  - `[project-name]` - Session `[session-id-short]` ([Model]) - [session-timestamp]
  - ...
- **Prompts Reviewed**: [count] prompts
- **Models Used**: [Model breakdown, e.g., "Claude Sonnet 4.5 (8 prompts), Claude Opus 4.5 (4 prompts)"]

---

## Executive Summary

### Top 3 Improvement Opportunities
1. [Highest impact improvement with frequency]
2. [Second highest impact]
3. [Third highest impact]

### Strengths
- [Positive patterns already in use]
- [Good techniques observed]

---

## Detailed Analysis

### Pattern: [Pattern Name]
**Frequency**: Found in X of Y prompts
**Impact**: High | Medium | Low
**Category**: Explicitness | Framework | Security | Anti-pattern | etc.

**Example from** [project-name]:
> [Original prompt excerpt - max 2-3 sentences]

**Issue**:
[Explain what's problematic about this prompt]

**Suggested Improvement**:
> [Rewritten version with improvements]

**Why This Matters**:
[Brief explanation from prompt engineering principles - cite research if applicable]

**Quick Fix**:
[Concrete action user can take immediately]

---

[Repeat for each pattern, ordered by impact]

---

## Quick Wins Checklist

Actionable improvements you can apply immediately:

- [ ] [Specific actionable item 1]
- [ ] [Specific actionable item 2]
- [ ] [Specific actionable item 3]
- [ ] [etc.]

---

## Resources for Deep Dives

- **Comprehensive Guide**: `~/.claude/skills/prompt-engineer/resources/prompt_engineering_guide_2025.md` (855 lines)
- **Templates**: `~/.claude/skills/prompt-engineer/resources/templates.md`
- **Invoke Skill**: Run `/prompt-engineer` or use Skill tool to get expert guidance

---

## Methodology

### Sessions Analyzed

| Project | Session ID | Model | Timestamp | Prompts Sampled |
|---------|------------|-------|-----------|-----------------|
| [project-name] | `[session-id-short]` | [Model] | [YYYY-MM-DD HH:MM] | [count] |
| [project-name] | `[session-id-short]` | [Model] | [YYYY-MM-DD HH:MM] | [count] |

**Session ID format**: Show first 8 characters (e.g., `0506e04a-...` from `0506e04a-6082-43b3-92b7-af8350cbab3f`)

### Analysis Criteria

This analysis used the `prompt-engineer` skill's knowledge base, which includes:
- Research-backed techniques with measured performance improvements
- Model-specific optimizations (Claude Opus 4.5 vs Claude Sonnet 4.5)
- Debunked myths to avoid
- Security patterns for code generation

Analysis was performed on [count] prompts from [count] projects, sampled to ensure diversity across task types and project contexts.
```

### Report Writing Guidelines

1. **Be Specific**: Use exact quotes from user's prompts
2. **Show Don't Tell**: Concrete before/after examples
3. **Prioritize**: Most impactful improvements first
4. **Be Constructive**: Frame as growth opportunities
5. **Cite Evidence**: Reference research/principles when possible
6. **Stay Actionable**: Every critique includes a concrete fix

## Phase 6: Save Report

### Step 1: Determine Output Path
- If custom path provided in args: use that
- Otherwise: `~/.claude/reports/prompt-critique-[timestamp].md`
  - Use ISO timestamp format: `YYYYMMDD-HHMMSS` (e.g., `20250109-143022`)

### Step 2: Create Reports Directory
Use Bash to create directory if it doesn't exist:
```bash
mkdir -p ~/.claude/reports
```

### Step 3: Write Report
Use Write tool to save the generated markdown report.

### Step 4: Inform User
Display the full path and offer to open:
```
Report saved to: [full-path]

To review your report, run:
cat [full-path]

Or open in your default markdown viewer.
```

---

## Critical Requirements

### DO

- Invoke `prompt-engineer` skill FIRST before analysis
- Extract actual prompt text from both string and list content formats
- Filter out noise (empty prompts, interrupts, sidechains)
- Sample diverse prompts across multiple projects
- Provide specific before/after examples in the report
- Create `~/.claude/reports/` directory if missing
- Show full path to saved report

### DO NOT

- Analyze prompts without loading prompt-engineer knowledge first
- Include system messages or tool confirmations as "user prompts"
- Skip projects - ensure diversity across 3-6 projects
- Write vague critiques without examples
- Forget to handle both string and list content formats
- Make judgments not grounded in the prompt-engineer skill's principles
- Overload the report - focus on top patterns and highest impact improvements

---

## Edge Cases

1. **No sessions found**: Inform user that no Claude Code sessions exist yet
2. **Very few prompts**: Analyze what's available, note limited sample size
3. **All prompts are short commands**: Note this pattern itself (could use more context)
4. **Cannot parse JSONL**: Skip corrupted files, report which files had issues
5. **Output path not writable**: Fall back to `~/prompt-critique-[timestamp].md`

---

## Success Criteria

Report is successful if it:
- [ ] Analyzed prompts from 3+ different projects
- [ ] Identified 3+ high-impact improvement patterns
- [ ] Provided specific before/after examples
- [ ] Included actionable quick wins checklist
- [ ] Grounded all critiques in prompt-engineer skill principles
- [ ] Saved to correct location and path displayed to user
