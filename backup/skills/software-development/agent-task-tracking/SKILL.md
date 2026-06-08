---
name: agent-task-tracking
description: "Use when building, operating, or enforcing workflow around agent task-tracking systems such as Task Pulse. Covers dashboard architecture, live task telemetry, operational restart/debug routines, and the discipline of creating task records before deliverable work starts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [task-tracking, dashboards, task-pulse, workflow, operations, sse, nextjs]
    related_skills: [github-pr-workflow, kanban-orchestrator, writing-plans]
---

# Agent Task Tracking

## Overview

Use this skill for the **class of systems that track agent work as tasks**: task dashboards, runner-backed execution monitors, Task Pulse-style work queues, and the workflow discipline around recording work before it begins.

This umbrella replaces narrower siblings that separately described:
- the **generic dashboard product pattern** for live task monitors,
- the **Task Pulse project-specific ops/debug rules**, and
- the **workflow rule** that deliverable work must be created as a tracked task before execution.

The maintainer-facing principle is simple: treat these as one class of problem — **agent task tracking** — with labeled subsections for architecture, operations, and workflow policy.

## When to Use

Use this skill when the user asks to:
- build a real-time task dashboard for agents, runners, CI-like jobs, or workflow systems
- operate, debug, rebuild, or deploy Task Pulse or a similar Next.js task monitor
- create, group, review, or clean up tracked tasks before doing meaningful work
- add SSE/live logs/status/phase timelines/artifact links/approval states to a task UI
- reason about how tasks should be grouped into big-task / subtask hierarchies

Do not use this for generic project planning without a task-tracking system; use planning or kanban skills instead.

## Class-Level Model

Think of agent task tracking as four layers:

1. **Ingress** — webhook, chat, form, or manual task creation
2. **Runner service** — creates task IDs, launches runners, captures stdout/stderr, updates status
3. **Presentation** — overview page, task detail page, SSE stream, artifact links, filters
4. **Governance** — naming, grouping, review, approval, cleanup, and cron-based audits

A good implementation separates these layers cleanly. Never couple the UI directly to raw CLI output.

## Section A — Building the Dashboard / Product Surface

### Recommended architecture
- Prefer a runner/service layer between UI and the agent CLI.
- Prefer **SSE before WebSockets** for append-only task/event/log streaming.
- Model both **status** and **phase** separately.
  - Example status: `queued | running | blocked | approval_required | done | failed | stopped`
  - Example phase: `queued | triaging | accepted | booting_runner | coding | testing | summarizing | waiting_review | completed | failed`
- Normalize raw output into your own `Task`, `TaskEvent`, `TaskLog`, `TaskArtifact`, and `TaskNotification` schema.

### UI expectations
For refined dashboards, ship an operations-cockpit UX rather than a plain admin table:
- clear hero card on detail page
- explicit back navigation
- phase timeline
- event feed + raw log panel
- quick links to detail/API/artifacts/notifications
- visible hierarchy markers for big task vs subtask
- explicit affordances like `查看详情`, not just implicit click areas

### Live-updating patterns
- Detail page: initial snapshot + SSE stream
- Overview page: polling or explicit refresh if acceptable
- Beware App Router caching; live task pages often need `export const dynamic = "force-dynamic"`
- Artifact links should always resolve to a real route or download path, not placeholder URLs

### Approval-aware task systems
Treat `approval_required` as a first-class task state, not a buried log line:
- surface it in filters/stat cards/status pills
- emit semantic events/notifications
- provide a visible approval action on both dashboard and detail page

## Section B — Operating and Debugging Task Pulse-Like Systems

### Rebuild / restart discipline
For production Next.js task dashboards, rebuild and restart explicitly:
1. kill the old port owner with a reliable tool (`fuser`, not fragile `lsof` one-liners)
2. rebuild the app
3. start the new process
4. verify with direct localhost curl and process/port checks

Never assume a successful start command means the new server is actually serving traffic.

### Failure modes to isolate
- old process still owns the port → stale behavior despite code changes
- build succeeded but server was not restarted
- background process died silently after launch
- reverse proxy points to the wrong port
- route caching makes a successful mutation look broken
- mobile/browser tap targets are too small even when routing technically works

### Data model / persistence principles
A Task Pulse-style system should preserve:
- task metadata and lifecycle state
- append-only events/logs
- artifact metadata and download routes
- notification history
- tombstones/soft-delete state where cross-runtime consistency matters

### Mobile UX rules
- make entire subtask rows clickable, not only title text
- use clear category/status badges on every task row
- ensure non-submit buttons inside forms explicitly use `type="button"`
- verify task interactions on mobile or mobile emulation, not only desktop

## Section C — Workflow Governance: Create the Task Before the Work

### Core rule
If the requested work produces a deliverable and belongs in the tracked system, **create the task first** and only then start the work.

This applies to:
- coding
- testing
- PPT/document generation
- research/analysis
- config backup / operational maintenance
- screenshots, demos, and other project artifacts

Tiny, second-scale edits may be exempt, but new features, multi-file changes, pushes, refactors, and reusable deliverables are not.
### Grouping discipline

Task systems should distinguish:
- **big tasks / groups (大任务)** — durable project lines. These should NOT be split, renamed, or merged arbitrarily.
- **small tasks (小任务)** — concrete work items under those groups. Their **category** (coding/chat/ppt/design/skill) should be corrected when wrong.

Rules:
- **大任务命名，小任务分类** — This is the core rule. Big tasks have stable names and groupings; small tasks have correctable categories.
- prefer reusing an existing parent group when the work clearly belongs there
- create a new group only for a genuinely new project/feature line
- group names must be specific and recognizable, not generic buckets
- when grouping depends on multiple fields (for example category + groupName + repoLink), keep those inputs consistent or the dashboard will split one conceptual group into multiple buckets
- **Do not demolish (拆房) big tasks.** A big task covers a coherent deliverable. Do not split its work into many tiny sibling tasks — that creates duplicate task entries under the same group, duplicates notifications, and corrupts the group signal-to-noise ratio. Add subtasks under the big task for distinct debug/attempt directions, but keep deliverable-scope tasks at a meaningful granularity.
- **Example: user says "完善这个repo"** — correct is 1 task "agent 仓库完善 (用 OpenCode)", not 4 tasks "改README" + "改前端" + "修后端" + "推送".
- **Debugging subtasks are not the same as demolishing:** A debugging session that tries 3 approaches (change params→test, swap component→retry, different protocol→observe) should get 3 subtasks because each is a separate attempt at the same root-cause question. That is tracking, not splitting.
- **Cron job scope:** The daily 5:00 cron must ONLY fix category classifications (ppt→ppt, coding→coding, chat→chat) and groupId consistency (same groupName → same groupId). It MUST NOT split, rename, merge, or restructure big task groups. The LLM agent running the cron should treat group structure as immutable — only correct the metadata that holds the structure together.
### Debugging subtask discipline

For investigation / debugging / troubleshooting sessions (multi-step root-cause analysis):

- **Create a subtask per distinct debug direction**, not just a single task for the whole investigation. Each attempt (change parameter → test, swap component → retry, try different protocol → observe) should have its own tracked subtask.
- Even unsuccessful attempts are worth tracking — they form the history trail for review.
- Close the task record only when the direction is exhausted or the underlying question is answered.
- This prevents the conversation from becoming an untracked trial-and-error session, and gives the user a browsable history of what was tried.

### Review / cleanup discipline

A mature task system benefits from:
- waiting-review stages before final completion
- daily audits for naming/category/state anomalies
- cleanup scripts or cron jobs for metadata repair
- explicit verification after task creation that the task landed in the right group/category

### LLM-powered cron housekeeping pattern

When the user wants a cron job to intelligently organize tasks (rather than simple keyword matching), use an **LLM agent cron** instead of a no_agent script. Set `no_agent=false` — critical for LLM-driven analysis.

**Scope:**

The cron SHOULD:
- Fix category classifications (ppt/coding/chat/design/skill)
- Merge duplicate big task groups (same project → same group name)
- Rename unclear/typo-ridden group names (e.g. "task-Pluse 完善" → "Task Pulse 完善")
- Fix groupId consistency (same groupName + same repoLink → same groupId)
- Clean up stale phase states (e.g. waiting_review + done → completed)

The cron MUST NOT:
- Split an existing, coherent big task group
- Create new tasks
- Delete tasks

**User's rule:** 大任务合并同类 + 命名不清楚的改名 + 小任务分类修正.

**Setup:**
1. Use `cronjob(action="update", no_agent=false)` — critical. `no_agent=true` runs a dumb script; `no_agent=false` lets the LLM read, reason, and write.
2. Set `enabled_toolsets` to `["terminal", "file"]` — the agent needs `file` to write modified JSON files, not just `terminal` for reading.
3. Write a detailed prompt covering: read data source, inspect for duplicates, merge logic, write-back, verify.

### Group merging strategy:
- Ingest all tasks from `~/.task-pulse-data/task_*.json` via `cat` or API.
- Build a map by group name. If the same name appears under different groupIds (e.g. `group_agent-仓库联调` vs `group_agent-仓库联调-https-github-com-...`), merge into the **larger** group (more tasks wins).
- **IMPORTANT: Do NOT update `groupId` directly.** The server computes groupId dynamically from `metadata.groupName + repoLink` via `inferGroupId()`. Instead:
  1. Set `metadata.groupName` to the desired canonical group name
  2. Ensure `repoLink` is consistent across all tasks in the same group (either all have it or none do)
  3. The `groupId` will be auto-computed on next read
- After merge, verify by re-reading the API or data directory to confirm no remnant groups remain.

### Mock-data.ts — the hidden second source of truth

Task Pulse ships with `src/lib/task-pulse/mock-data.ts` containing `INITIAL_TASKS` — demo tasks with hardcoded `metadata.groupName` values. These mock tasks live **in-memory only** (they have no JSON file on disk), but the server mixes them into the API response.

**Pitfall:** Renaming a group in the JSON files but not in `mock-data.ts` leaves stale group names in the API output (e.g. renaming "task-Pluse 完善" to "Task Pulse 完善" everywhere except mock-data.ts).

**Fix:** Whenever renaming groups:
1. Update all `task_*.json` files in `~/.task-pulse-data/`
2. Update `src/lib/task-pulse/mock-data.ts` — search for the old group name and replace
3. Run `npm run build` to regenerate the Next.js production bundle
4. Kill ALL old server processes (see rebuild/restart discipline below)
5. Start fresh server and verify with curl

### The full rebuild + verify loop

When the source code changes (mock-data.ts, store.ts, etc.):

1. `cd ~/task-pulse && npm run build`  (check exit code)
2. Kill the old server: `fuser -k 3000/tcp` — the old `npx next start` spawns 4 processes (bash wrapper, npm exec, sh -c, next-server); `fuser` catches all of them
3. Verify port is free: `ss -tlnp | grep 3000` must return nothing
4. Start fresh: use `terminal(background=true)` with `cd ~/task-pulse && npx next start -p 3000`
5. After 3-4 seconds, verify: `curl -s http://localhost:3000/api/tasks | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['tasks']), 'tasks')"`
6. Check group structure: ensure old stale group names are gone

**Common cron toolset mistakes:**
- `["terminal"]` only — agent can read data but cannot write fixes → reports issues but does nothing.
- Missing `file` tool → agent proposes changes it can't execute. Always include `file` when the agent needs to overwrite JSON data.
- Prompt too vague — must explicitly say "compare group names, merge duplicates into the larger group, then verify no duplicates remain."

**Prompt structure:**
```
[Role] You are a task housekeeping agent.
[Read] cat/all tasks from data directory.
[Analyze] Check: duplicate groups by name, wrong categories, stale states.
[Fix] Use write_file to modify JSON files: groupId, category, phase.
[Verify] Re-read and confirm fixes applied.
[Report] Chinese summary of changes.
```

## Common Pitfalls

1. **Treating dashboard building, Task Pulse ops, and task-creation policy as separate skills.** They are one maintainable class: agent task tracking.
2. **Creating tasks after the work is done.** This defeats the whole tracking purpose.
3. **Using one monolithic state string.** Separate status from phase.
4. **Assuming UI polling or `router.refresh()` is enough.** Cache policy may still be wrong.
5. **Making only titles clickable.** Mobile users will report the detail page as broken.
6. **Failing to verify port ownership after restart.** Old processes commonly survive.
8. **Editing groupId field directly is pointless.** Task Pulse's `registerGroup()` recomputes `groupId` from `metadata.groupName + repoLink` on every file read. To change a task's group, update `metadata.groupName` (and `repoLink` for consistency) in the JSON file — never the `groupId` field itself. The server's `inferGroupId()` function builds the groupId deterministically from the group name and repo link.
9. **Mock-data.ts is an independent source of group names.** Renaming groups requires updating both the data files AND the mock data, then rebuilding.

## Support files

This umbrella keeps absorbed session-specific details in support references:
- `references/agent-task-dashboard.md`
- `references/task-pulse-ops.md`
- `references/task-pulse-workflow.md`

Use those when you need the narrower historical recipes or project-specific examples.

## Verification Checklist

- [ ] The task system has a clear runner/service layer
- [ ] Status and phase are modeled separately
- [ ] Overview/detail pages have explicit live-update behavior
- [ ] Artifact links resolve to real targets
- [ ] Restart/debug instructions include port-owner verification
- [ ] Deliverable work is represented by a created task before execution
- [ ] Grouping and review rules are explicit and verifiable
