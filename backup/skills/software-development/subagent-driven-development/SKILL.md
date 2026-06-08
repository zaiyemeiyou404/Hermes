---
name: subagent-driven-development
description: "Execute plans via delegate_task subagents (2-stage review)."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

# Subagent-Driven Development

## Overview

Orchestrate feature development using a 7-phase workflow inspired by Anthropic's Claude plugins: parallel codebase exploration → clarifying questions → parallel architecture design with multiple philosophies → plan → implement (via OpenCode/Claude Code) → parallel quality review (3 agents: simplicity, bugs, conventions) → integration review.

**Core principle:** Hermes handles all cognitive/intelligent phases (exploration, design, review). OpenCode/Claude Code handles only implementation. Fresh subagent per task + two-stage review = high quality, fast iteration.

## When to Use

Use this skill when:
- You're building a new feature (multi-file, multi-step)
- You have requirements but need to explore the codebase first
- Architecture decisions need multiple perspectives (parallel architects)
- Quality is important and independent review is needed
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- You want automated review between tasks

**vs. manual execution:**
- Parallel exploration (faster, more complete understanding)
- Multiple architecture perspectives (better design decisions)
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

**vs. Claude Code's feature-dev plugin:** Hermes achieves the same 7-phase workflow natively via delegate_task subagents and skill orchestration. The key difference: OpenCode/Claude Code handles only implementation (Phase 5), while Hermes handles all cognitive phases (exploration, architecture, review).

## Agent Division of Labor

**Coding tasks belong to OpenCode, not Hermes.** When the task involves writing, editing, or generating code files (`.tsx`, `.ts`, `.py`, `.js`, etc.), delegate to an OpenCode subagent. Hermes (the principal agent) should NOT use `patch`, `write_file`, or `terminal` to directly edit source files for software development. Instead:

1. Write a clear task spec (what to build, where, constraints)
2. Delegate to OpenCode via `delegate_task` or the opencode skill
3. Review the result, not the implementation

**Exceptions where Hermes may write files directly:**
- Configuration files (`.yaml`, `.json`, `.env`, `Caddyfile`)
- Documentation (README, AGENTS.md, SKILL.md)
- Scripts that are thin wrappers (≤50 lines of procedural glue)
- Document generation (pptxgenjs scripts for PPT creation, HTML for web presentations)
- Infrastructure/tooling that runs on the Hermes server itself

**Rule of thumb:** if the file is part of a user's application codebase and would be committed to their project repo, OpenCode should write it. If it's infrastructure glue for the Hermes environment, Hermes can write it.

## Division of Labor: Hermes Orchestrates, OpenCode/Claude Code Implements

This skill follows a **two-layer architecture**:

```
┌────────────────────────────────────────────┐
│            Hermes (orchestrator)           │
│  • Requirements analysis & clarification   │
│  • Codebase exploration (parallel agents)  │
│  • Architecture design (parallel agents)   │
│  • Task planning & decomposition           │
│  • Quality review (parallel agents)        │
│  • Integration review                      │
├────────────────────────────────────────────┤
│    OpenCode / Claude Code (implementer)    │
│  • Write failing test                      │
│  • Write minimal implementation            │
│  • Run tests to verify                     │
│  • Commit                                  │
└────────────────────────────────────────────┘
```

**Hermes** handles all cognitive/intelligent phases (exploration, design, review). **OpenCode/Claude Code** handles only the implementation phase (write code, run tests, commit). When the plan has a clear implementation spec, dispatch the coding executor.

## The Process — Feature Development Orchestration (7-Phase)

For non-trivial feature development (not simple 1-2 file changes), follow this 7-phase workflow inspired by anthropics/claude-plugins-official's feature-dev plugin:

### Phase 0: Pre-flight — Plan or User Request

Either read an existing plan file (from writing-plans skill) or start from user requirements. If no plan exists, create one using the writing-plans skill before proceeding.

### Phase 1: Codebase Exploration (Parallel)

Launch **2-3 parallel code-explorer subagents** to understand the relevant codebase:

```python
delegate_task(tasks=[
    {
        "goal": "Explore codebase for feature: [feature description]",
        "context": f"""
        Your job: explore the codebase and answer:
        1. What are the entry points and core files relevant to this feature?
        2. How does the existing flow work from entry to output?
        3. What patterns, conventions, and architectures exist?
        4. What dependencies are involved?
        5. What files will need to change?

        Return a map of:
        - Essential files to read with their purposes
        - Architecture patterns in use
        - Implementation constraints identified
        """,
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Explore codebase for edge cases and constraints",
        "context": f"""
        Your job: explore the codebase and answer:
        1. What error handling patterns are used?
        2. What edge cases exist in similar features?
        3. What test patterns are used?
        4. What configuration/environment constraints exist?
        5. What would break if we change things incorrectly?

        Return:
        - Edge cases to handle
        - Error handling patterns
        - Test patterns to follow
        - Risk areas
        """,
        "toolsets": ["terminal", "file"]
    },
])
```

**Purpose:** Explorers focus on different aspects (flow vs. edge cases) to get complete coverage without overlap.

### Phase 2: Clarifying Questions

Based on exploration results, identify what's underspecified and ask the user:

```python
# After exploration, present questions to the user
"Based on codebase analysis, I have a few questions before designing:
1. Should the new feature handle [edge case X]?
2. Error handling: log and continue, or fail fast?
3. Is there a preference for [approach A vs approach B]?"
```

**Never skip this phase.** Ambiguous requirements cause rework.

### Phase 3: Architecture Design (Parallel)

Launch **2-3 parallel architect subagents** with different design philosophies:

```python
delegate_task(tasks=[
    {
        "goal": "Design architecture — minimal changes approach",
        "context": f"""
        Design the architecture for: [feature description]

        EXPLORATION FINDINGS:
        [paste from Phase 1]

        FOCUS: Minimize changes to existing code. Reuse existing patterns.
        Output: file-by-file plan with exact changes needed.
        """,
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Design architecture — clean/ideal approach",
        "context": f"""
        Design the architecture for: [feature description]

        EXPLORATION FINDINGS:
        [paste from Phase 1]

        FOCUS: Best possible design, extract when needed.
        Output: file-by-file plan with exact changes needed.
        """,
        "toolsets": ["terminal", "file"]
    },
])
```

**Compare the outputs** and recommend one, or synthesize a hybrid. Present to the user for approval.

### Phase 4: Write Implementation Plan (If Not Already Available)

Use writing-plans skill to create a detailed task-level plan based on the approved architecture.

### Phase 5: Per-Task Implementation (via OpenCode/Claude Code)

For EACH task in the plan, dispatch the coding executor:

```python
delegate_task(
    goal="Implement Task 1: [task description]",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - bcrypt already in requirements.txt
    """,
    # Use terminal-only to force OpenCode runner via delegate_task
    toolsets=['terminal']
)
```

**Key:** Provide the full task spec in context. Don't make the implementer read the plan file.

### Phase 6: Quality Review (Parallel)

After the implementer completes, launch **3 parallel reviewer subagents**:

```python
delegate_task(tasks=[
    {
        "goal": "Review — simplicity and DRY compliance",
        "context": f"""
        FILES TO REVIEW: [list from completed task]
        FOCUS: Is the code simple? Any duplication? Can it be cleaner?
        OUTPUT: Critical/Important/Minor, Verdict: APPROVED or REQUEST_CHANGES
        """,
        "toolsets": ["file"]
    },
    {
        "goal": "Review — bugs and correctness",
        "context": f"""
        FILES TO REVIEW: [list from completed task]
        FOCUS: Any bugs? Edge cases missed? Error handling correct? Logic correct?
        OUTPUT: Critical/Important/Minor, Verdict: APPROVED or REQUEST_CHANGES
        """,
        "toolsets": ["file"]
    },
    {
        "goal": "Review — conventions and standards",
        "context": f"""
        FILES TO REVIEW: [list from completed task]
        FOCUS: Follows project conventions? Test coverage adequate? Naming consistent?
        OUTPUT: Critical/Important/Minor, Verdict: APPROVED or REQUEST_CHANGES
        """,
        "toolsets": ["file"]
    },
])
```

**Confidence scoring:** Only report issues with confidence ≥ 80/100. Include file:line references with concrete fix suggestions.

**If ANY reviewer requests changes:** dispatch a fix subagent, then re-run all three reviewers. Repeat until all three approve.

### Phase 7: Summary & Integration

After ALL tasks pass review:

```python
delegate_task(
    goal="Final integration review of the complete feature",
    context="""
    All tasks are complete and individually reviewed. Review the full
    implementation for:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for PR?
    """,
    toolsets=['terminal', 'file']
)
```

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Push to feature branch (if applicable)
git push origin feature-branch
```

For simpler tasks (1-2 file changes), skip Phases 1-4 and go directly to Phase 5 (implementation) + Phase 6 (review).

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## Red Flags — Never Do These

- Skip codebase exploration before designing architecture
- Skip clarifying questions before design
- Design architecture without at least 2 competing approaches
- Accept the first architecture design without comparing alternatives
- Start implementation without a plan (from writing-plans or user-approved architecture)
- Skip reviews (spec compliance OR code quality — all 3 reviewers)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues
- Have Hermes edit source files directly — always delegate coding to OpenCode/Claude Code

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

## Efficiency Notes

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

## Integration with Other Skills

### With writing-plans

This skill EXECUTES plans created by the writing-plans skill:
1. User requirements → writing-plans → implementation plan
2. Implementation plan → subagent-driven-development → working code

### With test-driven-development

Implementer subagents should follow TDD:
1. Write failing test first
2. Implement minimal code
3. Verify test passes
4. Commit

Include TDD instructions in every implementer context.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

## Example Workflow (Feature Development)

```
[Phase 1: Codebase Exploration]
[Dispatch 2 parallel explorer agents — flow analysis + edge cases analysis]
  Explorer 1: "Entry point: src/auth/login.py. Core files: models/user.py, services/auth.py"
  Explorer 2: "Edge cases: empty email, duplicate email, SQL injection in name field"
[Collate findings into a codebase map]

[Phase 2: Clarifying Questions]
  You: "Edge cases to handle: empty email, duplicate email..."
  User: "Return 400 with descriptive message for empty, 409 for duplicate"

[Phase 3: Architecture Design (Parallel)]
[Dispatch 2 architect agents — minimal change vs clean design]
  Architect 1 (minimal): "Add 3 fields to existing User model, extend validate()"
  Architect 2 (clean): "Extract AuthService class, use Pydantic for validation"
[Compare: User prefers minimal approach → approve]

[Phase 4: Write Implementation Plan]
[Use writing-plans skill → 5 tasks generated]

[Phase 5: Per-Task Implementation via OpenCode]
--- Task 1: Create User model updates ---
[Dispatch OpenCode implementer]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, tests passing, committed.

[Dispatch 3 parallel reviewers]
  Reviewer 1 (simplicity): ✅ APPROVED — clean, no duplication
  Reviewer 2 (bugs): ✅ APPROVED — edge cases handled
  Reviewer 3 (conventions): ✅ APPROVED — follows project patterns

[Mark Task 1 complete]

--- Task 2: Auth validation ---
[Dispatch OpenCode implementer]
  Implementer: No questions, implemented, tests passing.

[Dispatch 3 parallel reviewers]
  Reviewer 1 (simplicity): ✅ APPROVED
  Reviewer 2 (bugs): ❌ Missing: rate limiting for login attempts
  Reviewer 3 (conventions): ✅ APPROVED

[Dispatch fix subagent for rate limiting]
  Fixer: Added rate limiting, 8/8 tests passing.

[Dispatch 3 reviewers again]
  All three: ✅ APPROVED

[Mark Task 2 complete]

... (continue for remaining tasks)

[Phase 7: Integration Review]
[Dispatch final reviewer]
  Integration: ✅ All components work together, no regressions, ready for PR.

[Run full test suite: all passing]
[Push to feature branch]
[Done!]
```

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**

## Further reading (load when relevant)

When the orchestration involves significant context usage, long review loops, or complex validation checkpoints, load these references for the specific discipline:

- **`references/context-budget-discipline.md`** — Four-tier context degradation model (PEAK / GOOD / DEGRADING / POOR), read-depth rules that scale with context window size, and early warning signs of silent degradation. Load when a run will clearly consume significant context (multi-phase plans, many subagents, large artifacts).
- **`references/gates-taxonomy.md`** — The four canonical gate types (Pre-flight, Revision, Escalation, Abort) with behavior, recovery, and examples. Load when designing or reviewing any workflow that has validation checkpoints — use the vocabulary explicitly so each gate has defined entry, failure behavior, and resumption rules.

Both references adapted from gsd-build/get-shit-done (MIT © 2025 Lex Christopherson).
