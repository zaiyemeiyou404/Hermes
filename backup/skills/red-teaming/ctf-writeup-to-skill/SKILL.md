---
name: ctf-writeup-to-skill
description: "Use when a user gives a CTF challenge, writeup, repo, or walkthrough and wants the solve path reproduced, generalized, and distilled into reusable CTF skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ctf, security, writeup, reproduction, skill-distillation, web, pwn, reverse, crypto, forensics, osint]
    related_skills: [hermes-agent, requesting-code-review, task-pulse-workflow]
---

# CTF Writeup → Skill Distillation

## Overview

Use this skill when the user gives you a **CTF题目、附件、writeup、博客链接、题解仓库、复现记录** and wants more than a one-off solve. The goal is to turn challenge-specific material into a reusable workflow:

**input artifact → reproduce solve path → verify the key exploit/solve chain → strip challenge-specific noise → extract reusable method → propose or update one or more CTF skills**

This skill is intentionally **meta**. It does not replace topic skills like `ctf-web` or `ctf-pwn`; instead it tells Hermes how to learn from a solved or partially solved challenge and convert that experience into durable procedural knowledge.

## Mandatory First Step: Create Task Pulse Task

**Before any CTF writeup processing begins**, create a task in Task Pulse:

```bash
curl -s -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CTF Writeup 处理 — 清晰说明处理范围",
    "prompt": "处理哪些 writeup、来自什么比赛、预期输出什么技能",
    "category": "skill",
    "runner": "hermes",
    "model": "deepseek/deepseek-chat",
    "source": "微信",
    "groupName": "CTF Writeup 分析"
  }'
```

The task is created BEFORE reading, analyzing, or distilling any writeup. After completion, update the task via review API to mark it done.

**Why this matters**: skipping the task means the user has no visibility into what Hermes is doing in the Task Pulse dashboard. This was a real correction in a production session — the user asked "为什么一开始不用taskPluse?"

**Pitfall**: do NOT create one task per writeup if processing a batch — create ONE umbrella task for the whole batch, then update it when done. If individual writeups merit separate tracking, add sub-steps to the task's event log rather than creating separate tasks. This keeps the dashboard clean and avoids flooding the group with 33 nearly-identical tasks. Only break into separate tasks if the work spans multiple sessions or produces independent deliverables (e.g. one task for "read all writeups" and another for "create skills").

Trigger when the user:
- Says “把这题复现一下，然后总结成 skill”
- Sends a writeup/blog/repo and wants reusable方法论, not just a summary
- Wants Hermes to learn from a finished solve path
- Wants challenge-specific notes separated from reusable techniques
- Wants a batch of writeups normalized into a small skill library

Do **not** use this skill when:
- The user only wants a quick summary of the writeup
- The material cannot be reproduced and the user only wants speculation
- The result would be a single stale fact rather than a reusable workflow

## Core Principle

A good output from this skill always separates two layers:

1. **Reproduction record** — what happened in this exact challenge
2. **Reusable method** — what general technique, trigger, or workflow should be preserved

Never store the whole writeup as memory. Never create a skill that is just “this exact challenge but in SKILL.md form”. The point is to preserve the **method**, not the artifact.

Also treat skills as **execution contracts**, not prompt bundles. A reusable CTF skill should explicitly capture:
- applicability / trigger signals
- execution strategy
- verification points
- stop conditions / boundaries

If one of these is missing, the output is probably still a note, not a good skill.

## Operating Modes

| Input type | What to do |
|---|---|
| Raw challenge + attachment/service | Triage the challenge, solve or partially solve it, then distill the reusable parts |
| Full writeup | Reproduce the key chain from the writeup, verify each decisive step, then abstract |
| Repo of solutions | Identify clusters of repeated techniques; propose 1 umbrella skill or a small skill set |
| Multiple writeups | Group by technique first, not by event/year/platform |
| Incomplete writeup | Reconstruct the missing assumptions explicitly before abstraction |
| **Large batch (10+ writeups)** | **Use parallel intake + mapping pattern (see below)** |

## Large Batch Processing Pattern (10+ Writeups)

When the user sends 10+ writeups (e.g. a full CTF repo), do NOT read them sequentially — use `delegate_task` to parallelize by category.

### Pattern: Parallel Intake + Central Mapping

```
User: 27 writeups from MiniLCTF 2026 repo
  ↓
1. Create ONE umbrella Task Pulse task for the whole batch
2. Group writeups by challenge family (Crypto/Web/Pwn/Reverse/Misc)
3. For each group, launch a subagent via delegate_task:
     - Provide: existing skill descriptions, raw writeup URLs
     - Goal: read all writeups in that group, extract technique + solve method + key insight
     - Toolsets: [terminal] (for curl)
4. After all subagents complete:
     - Analyze their output for skill gaps vs existing skills
     - Categorize each writeup: already covered / needs patch / needs new skill
     - Summarize the gap analysis in a table
5. Present the analysis to the user before applying
6. Apply patches/skill creations only after user confirms (unless user said "改" = proceed)
```

### Why this works
- Subagents read in parallel (3 at a time via max_concurrent_children=3), dramatically reducing total time
- Each subagent focuses on one category, producing coherent analysis without context switching
- Central aggregation catches cross-cutting patterns and prevents duplicate skill proposals
- The user gets one cohesive proposal rather than 27 individual notifications

### Heuristics from real usage (MiniLCTF 2026, 27 challenges)
- ~80% map to existing skills (patch only)
- ~15% require new skills
- ~5% are already fully covered (no action)

### Pitfalls
- If a subagent's curl requests fail (raw.githubusercontent.com timeout), use browser_navigate to the file on github.com instead, then read via browser_console
- Set subagent timeout to at least 120s for categories with 5-6 writeups
- Some writeups are PDFs — note this in subagent context so it handles them differently

## Phase 1 — Intake and Classification

Before doing any abstraction, classify the material.

### 1.1 Determine artifact type

Record which of these you received:
- challenge statement
- binary / pcap / image / archive
- live service / URL / nc endpoint
- writeup markdown/blog
- solve script / exploit code
- source code
- screenshots / terminal logs

### 1.2 Determine challenge family

Pick the dominant category:
- web
- pwn
- rev
- crypto
- forensics
- osint
- misc

If unclear, say so and list the top 2 candidates with the evidence behind each.

### 1.3 Decide whether you are extracting:
- a **single-solve technique** (e.g. ret2libc with a single leak)
- a **triage workflow** (e.g. first 20 minutes of web recon)
- a **verification workflow** (e.g. how to prove the leak is real)
- an **anti-pitfall pattern** (e.g. writeup assumed a libc version that was never verified)

## Phase 2 — Reproduce Before Abstracting

Never jump directly from writeup to skill. First reproduce the critical path.

### Minimum reproduction bar

You should verify as many of these as the material allows:
- the challenge setup is understood
- the decisive primitive is real
- the exploit/solve chain is coherent end-to-end
- the final result or an equivalent intermediate artifact can be reproduced
- claims in the writeup that matter to the solve are validated, not merely repeated

### Reproduction checklist

1. Extract the exact sequence of pivotal steps from the writeup.
2. Mark each step as one of:
   - observed directly
   - reproduced locally
   - reproduced remotely
   - inferred but not reproduced
3. Identify the **first irreversible insight** in the solve path.
   - Example: the point where it becomes clear that SSTI exists
   - Example: the first stable libc leak
   - Example: the first recovered XOR keystream segment
4. Identify the **minimum solve chain**.
   - Remove decorative detours, retries, or author-specific tooling preferences.
5. Identify any hidden assumptions.
   - fixed libc version
   - challenge-specific path names
   - server clock behavior
   - preinstalled packages
   - architecture assumptions

### Non-negotiable rule

If you cannot reproduce a decisive claim, label it clearly. Do not turn an unverified writeup into a “reusable truth”.

## Phase 3 — Distill the Reusable Method

After reproduction, extract the reusable parts.

### 3.1 Pull out the signals

What clues should make Hermes suspect this path next time?

Examples:
- `render_template_string` + reflected output → SSTI candidate
- `checksec` shows NX/PIE on, no canary + format string reachable → leak-then-ROP candidate
- repeated short ciphertexts with nonce reuse → keystream-recovery candidate
- suspicious image/container + metadata mismatch → carving/stego workflow candidate

### 3.2 Pull out the preconditions

When does this method actually apply?

Examples:
- requires controllable template context
- requires one stable memory disclosure
- requires small public exponent and known plaintext structure
- requires writable user-controlled file path

### 3.3 Pull out the decisive workflow

Convert the solve into ordered, reusable steps:
- what to check first
- what to verify before proceeding
- what evidence confirms you are on the right path
- what common branches or alternatives exist

### 3.4 Pull out the failure modes

A strong skill must preserve where the method breaks.

Examples:
- leak is partial and not symbol-aligned
- the writeup's payload only works because ASLR was off locally
- the JWT issue was actually an authz bug, not a signature bug
- the patch “worked” only because the author skipped integrity checks

## Phase 4 — Choose the Right Skill Shape

Do **not** create one new skill per challenge by default. Pick the smallest durable abstraction that is still useful.

### Library Size Discipline

More skills is not automatically better. As the skill library grows, bad retrieval and fuzzy overlap become more likely. Prefer:
- fewer, higher-quality skills
- clear boundaries between neighboring skills
- patching an existing skill when the new lesson is a pitfall, signal, or verification refinement
- introducing a new skill only when it represents a genuinely reusable technique or workflow

Heuristic:
- if this lesson only adds one missing verification rule to an existing method, **patch**
- if this lesson defines a distinct exploit/solve pattern with different triggers or preconditions, **create**
- if this lesson is too bespoke or under-verified, keep only a reproduction note

### Good outcomes
- new narrow skill for a repeated technique
- patch to an existing CTF skill with a new pitfall or verification step
- umbrella skill + reference note for a family of similar writeups
- challenge note kept separate, with only the reusable workflow promoted into skill form

### Bad outcomes
- `buuoj-2021-web-42-skill`
- copying long payload dumps into SKILL.md
- preserving event-specific facts as if they were general rules
- writing a “workflow” with no verification points

## Skill Selection Heuristics

| Situation | Best outcome |
|---|---|
| One challenge demonstrates a common exploit cleanly | New technique skill |
| Writeup mostly confirms an existing workflow | Patch existing skill |
| Multiple writeups repeat the same triage pattern | New umbrella workflow skill |
| Challenge is highly bespoke | Keep as reproduction note; extract only a pitfall/checklist |

## Invocation Strategy Guidance

When this framework eventually sits inside a larger CTF skill library, do not assume one invocation mode fits all situations.

### Prefer explicit invocation when:
- the task is high-risk or high-cost to get wrong
- the model is small or weak at routing
- the technique has strict preconditions
- the user already knows the likely category (e.g. “this is ret2libc”)

### Prefer hybrid invocation when:
- the task is longer and exploratory
- multiple related skills might apply
- the model is strong enough to do coarse semantic triage but still benefits from a narrowed candidate set

### Avoid pure fuzzy invocation when:
- skill descriptions overlap heavily
- the library has grown without clear boundaries
- the solve path needs strict reproducibility

In short: **simple or safety-critical flows should bias toward explicit skill choice; broader exploratory work can use hybrid retrieval.**

## Suggested Output Contract

When the user asks for this workflow, structure the answer like this:

### A. Reproduction Summary
- challenge type
- source artifacts used
- decisive primitive
- minimum solve chain
- what was reproduced vs inferred
- final result / current blocker

### B. Reusable Method
- when to use
- signals
- preconditions
- ordered workflow
- verification points
- common pitfalls
- boundaries / non-applicability

### C. Skill Action
- create new skill / patch existing skill / defer
- exact proposed skill name(s)
- why this abstraction level is appropriate

## One-Shot Recipe (Single Writeup)

When the user sends a single writeup and asks to learn from it:

1. **Create Task Pulse task** (see Mandatory First Step above).
2. Read the artifact fully.
3. Summarize the solve chain in 5-10 bullets.
4. Mark each bullet as reproduced / observed / inferred.
5. Identify the first decisive insight.
6. Reduce the chain to the minimum reusable workflow.
7. Separate challenge-specific facts from general technique.
8. Decide whether to:
   - create a new skill,
   - patch an existing one,
   - or keep only a reproduction note.
9. If creating or patching, write the skill in reusable language with strong verification steps.
10. **Update Task Pulse task** to mark it done.

## Recipe for Large Batch (10+ Writeups)

1. **Create ONE umbrella Task Pulse task** (not one per writeup).
2. **Group writeups by challenge family** (crypto/pwn/web/reverse/misc).
3. **Launch parallel subagents** via `delegate_task` (max 3 concurrent):
   - Each subagent reads all writeups in its category via `curl` or `browser_navigate`
   - Provides: existing skill descriptions for mapping
   - Outputs: per-writeup technique summary + skill mapping recommendation
4. **Aggregate results** — build a skill gap table.
5. **Present analysis to user** with clear action items (which skills to patch, which to create).
6. **Proceed to apply** only after user confirms (or if user says "改"/"干" = proceed).
7. **Update Task Pulse task** to mark done.

Use `references/distillation-checklist.md` as the extraction checklist and `templates/reproduction-note.md` for the challenge-specific note format.

## Common Pitfalls

1. **Abstracting too early.**
   If you have not reproduced the decisive step, you are extracting vibes, not method.

2. **Confusing challenge facts with reusable workflow.**
   A leaked path, offset, constant, hostname, or flag format is usually not a skill.

3. **Creating one skill per writeup.**
   This bloats the library and destroys retrieval quality.

4. **Omitting preconditions.**
   A technique without applicability boundaries becomes misleading.

5. **Skipping verification points.**
   “Try payload X” is weaker than “Try payload X, and expect signal Y if the hypothesis is correct.”

6. **Preserving author tooling instead of the underlying method.**
   The reusable fact is usually the exploit logic, not the fact that one author used a specific wrapper script.

7. **Promoting bespoke solve chains into generic skills.**
   Some challenges are too custom. Save the note, not a fake generalization.

8. **Letting the model self-generate skills without review.**
   Drafting is fine; autonomous promotion is not. Skills should be treated like code: reviewed, bounded, and justified by reproduced evidence.

9. **Using fuzzy routing to paper over poor skill boundaries.**
   If neighboring skills overlap too much, fix the library design instead of hoping retrieval will guess correctly.

## Verification Checklist

- [ ] Input artifact type was explicitly classified
- [ ] Challenge family was explicitly identified (or ambiguity stated)
- [ ] Decisive solve primitive was isolated
- [ ] Reproduced vs inferred steps were distinguished
- [ ] Minimum solve chain was extracted
- [ ] Challenge-specific facts were separated from reusable method
- [ ] Proposed skill shape (new / patch / defer) was justified
- [ ] Resulting skill includes signals, preconditions, workflow, verification, pitfalls, and boundaries

## User Preferences (for this user)

- **Language**: 中文输出 CTF 分析。技术 + 解法 + 关键洞察 三段式。
- **Format**: 每题三行——技术名、解法概要、一句话关键洞察。不用长篇复述。
- **Action mode**: "改"/"1"/"干" = 直接执行，不用再问确认。
