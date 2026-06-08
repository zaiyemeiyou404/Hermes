---
name: opencode
description: "Delegate coding to OpenCode CLI (features, PR review)."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

Use [OpenCode](https://opencode.ai) as an autonomous coding worker orchestrated by Hermes terminal/process tools. OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.

## When to Use

- User explicitly asks to use OpenCode
- You want an external coding agent to implement/refactor/review code
- You need long-running coding sessions with progress checks
- You want parallel task execution in isolated workdirs/worktrees

## Prerequisites

- OpenCode installed: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- Auth configured: `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)
- Verify: `opencode auth list` should show at least one provider **or** confirm the intended provider key is exported in the shell that launches OpenCode
- Git repository for code tasks (recommended)
- `pty=true` for interactive TUI sessions

### Provider env-var workflow

For non-interactive cloud workers, environment-variable auth is often simpler and more durable than browser login. In practice, OpenCode picks up provider keys from the shell environment, so a common pattern is:

```bash
set -a
source ~/.hermes/.env
set +a
opencode run 'Respond with exactly: OPENCODE_SMOKE_OK' --model deepseek/deepseek-chat
```

Useful defaults discovered in real use:

- `DEEPSEEK_API_KEY=...` works for direct DeepSeek usage
- `OPENAI_API_KEY=...` can be kept as a fallback provider for harder tasks
- If you want a stable wrapper, create a tiny launcher that sources `~/.hermes/.env` before calling `opencode`

When a user prefers a cheaper default model with a stronger fallback, set the default model explicitly on each invocation (for example `--model deepseek/deepseek-chat`) and only override it when escalation is needed.

## CodeGraph Integration

[CodeGraph](https://github.com/colbymchenry/codegraph) is a knowledge-graph tool for codebases that integrates directly with OpenCode (and Claude Code, Codex CLI, Hermes Agent). It builds a local graph of functions, imports, types, and call relationships, then serves it as an MCP server — so AI agents can query code structure without scanning files every time.

**What it configures:** CodeGraph's `install --yes` auto-detects and configures MCP server entries for **all** available agents on the machine — not just OpenCode. In a typical Hermes-hosted environment, it updates `~/.config/opencode/opencode.jsonc` (OpenCode), `~/.claude.json` (Claude Code), `~/.codex/config.toml` (Codex CLI), **and** `~/.hermes/config.yaml` (Hermes Agent). After installation, the next Hermes session will have CodeGraph tools available via MCP.

**Installation** (one-time, per machine):

```bash
npx @colbymchenry/codegraph install --yes
```

The `--yes` flag runs non-interactive, defaulting to `--target=auto --location=global`. It updates OpenCode's config (`~/.config/opencode/opencode.jsonc`) and creates a reference file (`~/.config/opencode/AGENTS.md`).

**Project initialization** (per repo):

```bash
cd your-project
npx @colbymchenry/codegraph init -i
```

This scans all files, builds the graph, and stores it in a local SQLite database (`.codegraph/`). Typical output: 30 files → 392 nodes, 839 edges in ~500ms, ~1 MB DB size.

**What it does for OpenCode:**

- Reduces token consumption by ~59% and cost by ~35%
- Speeds up code queries by ~49%
- Drastically reduces LLM operations (cut by ~70%)
- Enables intelligent Web framework route detection (Django, FastAPI, Express, NestJS, Laravel, Rails, Spring — 13 frameworks)
- All data stays local (no network calls for queries)
- Files are auto-synced on save

**Verify it's working:**

```bash
cd your-project
npx @colbymchenry/codegraph status
# Should show: Index is up to date, with node/edge counts

npx @colbymchenry/codegraph query "YourClassName"
# Should return definition location and references
```

**Pitfalls:**
- macOS requires Xcode CLI tools; without them, CodeGraph falls back to a compatibility mode 5-10× slower
- First `init` on a large project (10k+ files) can take minutes; incremental syncs are fast
- A stale lock file can block indexing — use `npx @colbymchenry/codegraph unlock` to clear it
- CodeGraph v0.9.3 is pre-1.0; expect occasional edge cases with large monorepos

## Binary Resolution (Important)

Shell environments may resolve different OpenCode binaries. If behavior differs between your terminal and Hermes, check:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

If needed, pin an explicit binary path:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## One-Shot Tasks

Use `opencode run` for bounded, non-interactive tasks:

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files with `-f`:

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Show model thinking with `--thinking`:

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

### Shell-safe prompt construction

When the task prompt contains backticks, CSS selectors, shell metacharacters, or filenames with spaces/parentheses, do **not** inline it naively into a shell command. Shell parsing can corrupt the prompt before OpenCode receives it.

Prefer one of these patterns:

```bash
cat >/tmp/opencode-prompt.txt <<'EOF'
Debug and fix rendering in `西小豆 (1).html`.
Check `.sidebar-resize`, `.content-resize`, and markdown rendering.
EOF
opencode run "$(cat /tmp/opencode-prompt.txt)" --model deepseek/deepseek-chat
```

Or, for shorter prompts, avoid backticks and quote dangerous filenames plainly:

```bash
opencode run 'Fix rendering in the file named 西小豆 (1).html. Inspect the selectors .sidebar-resize and .content-resize.'
```

This is especially important when prompts mention literal code spans like `` `foo` `` or paths such as `My File (1).html`.

Force a specific model:

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Interactive Sessions (Background)

For iterative work requiring multiple exchanges, start the TUI in background:

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**Important:** Do NOT use `/exit` — it is not a valid OpenCode command and will open an agent selector dialog instead. Use Ctrl+C (`\x03`) or `process(action="kill")` to exit.

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

### Resuming Sessions

After exiting, OpenCode prints a session ID. Resume with:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue the last OpenCode session |
| `--session <id>` / `-s` | Continue a specific session |
| `--agent <name>` | Choose OpenCode agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--format json` | Machine-readable output/events |
| `--file <path>` / `-f` | Attach file(s) to the message |
| `--thinking` | Show model thinking blocks |
| `--variant <level>` | Reasoning effort (high, max, minimal) |
| `--title <name>` | Name the session |
| `--attach <url>` | Connect to a running opencode server |

## Procedure

1. Verify tool readiness:
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. For bounded tasks, use `opencode run '...'` (no pty needed).
   - Prefer a **foreground** `terminal(command="opencode run ...")` invocation when you need the final summary and want immediate observability.
   - Use background mode for `opencode run` only when you specifically need async execution or want to exercise task/progress plumbing.
3. For iterative tasks, start `opencode` with `background=true, pty=true`.
4. Monitor long tasks with `process(action="poll"|"log")`.
5. If OpenCode asks for input, respond via `process(action="submit", ...)`.
6. After any code-writing run, inspect the repo yourself before finalizing:
   - `git status --short`
   - `git diff --stat`
   - targeted `git diff -- <files>`
   - run verification commands directly instead of trusting the model summary alone
7. Exit with `process(action="write", data="\x03")` or `process(action="kill")`.
8. Summarize file changes, test results, and next steps back to user.

### Bounded repo-editing pattern

For a small repo improvement pass, a reliable sequence is:

1. create/switch to the target branch first
2. run `opencode run` in the repo with a concrete, low-risk change list
3. inspect `git diff` yourself
4. if needed, run a short second `opencode run` for polish/fixes
5. run your own validation commands (`py_compile`, tests, smoke checks, etc.)
6. commit only after direct verification
7. **Create a task-pulse task** recording this work (POST /api/tasks with mode=demo, groupName matching the existing big task, repoLink set). The dashboard is the user's single source of truth for activity — an OpenCode run that leaves no trace in task-pulse is invisible work.

### Task Pulse visibility vs Hermes background jobs

If the user expects the work to appear in **Task Pulse**, do **not** treat a Hermes background OpenCode launch as equivalent.

#### Target-repo workdir rule for Task Pulse launched jobs

When Task Pulse launches OpenCode with `cwd` set to the Task Pulse repo, the agent may accidentally edit **Task Pulse itself** instead of the user’s target repository unless the prompt explicitly forces repo isolation.

Use this pattern for repo-improvement tasks created through Task Pulse:

1. clone the target repo into an allowed subdirectory under the Task Pulse working tree (for example `/home/ubuntu/task-pulse/projects/<repo>-<task>`)
2. create and switch to the requested branch inside that cloned repo before any edits
3. tell OpenCode explicitly **not** to modify the Task Pulse repo
4. require the final output to name the actual working directory and branch so you can verify it independently

Do **not** tell OpenCode to clone into `/tmp` or another external directory unless you know the runner allows it. In live Task Pulse runs, external-directory permission requests may be auto-rejected, causing a fast false-success/failure cycle instead of real repo work.

- `terminal(... background=true, notify_on_complete=true)` gives Hermes-side async execution plus an in-chat completion notification.
- That notification path does **not** automatically create a Task Pulse task entry.
- Task Pulse only shows work that was created through its own task-creation flow (for example its `/api/tasks` endpoint / store layer), which then writes the snapshot data its UI consumes.

Use this rule:

1. If the goal is just to run OpenCode asynchronously, Hermes background execution is fine.
2. If the goal includes **dashboard visibility / live task tracking in Task Pulse**, start the job through Task Pulse's task-creation mechanism instead of launching OpenCode directly from Hermes. OR: after OpenCode completes, create a task-pulse entry via POST /api/tasks with mode=demo, recording what was done.
3. Do this when a task is visible in Task Pulse APIs/snapshot files but the user still says the dashboard is not updating, check for a UI refresh gap before blaming task creation:
   - verify `GET /api/tasks` includes the task
   - verify the snapshot file under `.task-pulse-data/` exists and is updating
   - verify `/api/tasks/<id>/stream` emits SSE updates for the detail page
   - if detail SSE works but the main `/tasks` list stays stale, the dashboard is likely rendered from a server component without client refresh; prefer a low-risk polling wrapper (for example a client component that calls `router.refresh()` on an interval around the existing server-rendered dashboard) instead of refactoring the whole page
   - for a worked pattern on target-repo isolation, see `references/task-pulse-target-repo-isolation.md`
4. When reporting status back to the user, distinguish clearly between:

   - Task Pulse task records / live snapshots

### Verifying Task Pulse feature work

When OpenCode is used to improve **Task Pulse itself** (dashboard, task detail, grouping, launch flow), do not stop at `git diff` or a successful agent summary. Validate the product path end-to-end:

1. run a local compile check yourself (`npm run build`, plus `npx tsc --noEmit` if TypeScript is present)
2. open the live `/tasks` page in the browser tool and confirm the intended UI labels/sections actually render
4. if the change affects task creation, grouping, repo links, or detail-page event flow, create or inspect a real task through Task Pulse's own API/UI flow rather than trusting mock data alone
5. verify the resulting task appears in the expected group and that any repo/action links are clickable from the dashboard/detail view
6. when validating grouping logic backed by persisted snapshots, watch for duplicate or stale groups caused by boot-time reconstruction; confirm the rendered group count matches real task membership
7. if the requested fix touches historical task data, check whether the source lives in a gitignored runtime directory (for example `.task-pulse-data/`). If so, do **not** stop at editing local JSON — implement the durable fix in repo code (migration/normalization/read-path compatibility) so the behavior survives redeploys and can be committed.

This catches a common failure mode where the code compiles but Task Pulse still renders stale groupings or unverified launch-form behavior.

For store-level issues (mock tasks returning 404, groups not loading), see `references/task-pulse-store-boot-stability.md`.
For repo-vs-runtime-data migration guidance, see `references/task-pulse-repo-vs-runtime-data.md`.

### Port / proxy verification — when changes don't appear on the domain

When the user reports "I don't see the changes" after OpenCode finished, the most likely cause is **not** a code bug — it's a stale dev server behind a reverse proxy.

Diagnostic flow:

```bash
# 1. Find which ports have dev servers serving this repo
ss -ltnp | grep -E ':(3000|3001|3002)\\b'

# 2. Check what the reverse proxy points to (Caddy or nginx)
grep -r 'proxy_pass\\|reverse_proxy' /etc/nginx/sites-enabled/ /etc/caddy/ 2>/dev/null

# 3. Curl localhost directly to confirm the new code is on a different port
curl -s http://127.0.0.1:3000/tasks | grep -o '展开小任务' | head -1
curl -s http://127.0.0.1:3002/tasks | grep -o '展开小任务' | head -1

# 4. Kill the old server on the proxied port, start a fresh one
kill <old-pid>
cd /home/ubuntu/task-pulse && PORT=3000 npm run dev
```

Common causes:
- **Multiple dev servers** — `next dev` refuses to start a second instance in the same directory. Killing the old one on the correct port is mandatory.
- **Caddy/nginx proxying to :3000** while the latest code runs on :3001 or :3002.
- **Old process started before code changes** — freezing the pre-change page in the dev server's in-memory module graph. A restart is the fix, not a rebuild.

#### Production mode is more reliable behind Caddy/Docker reverse proxy

`next dev` mode behind Caddy (Docker container) has a known issue: Next.js 16 blocks cross-origin WebSocket HMR connections, logging `Blocked cross-origin request to Next.js dev resource /_next/webpack-hmr from "pulse.zaiyemeiyou.com"`. Even after adding `allowedDevOrigins` to `next.config.js`, the experience can be flaky across browser sessions.

**Prefer production mode** when the site is served through Caddy/nginx:

```bash
cd /home/ubuntu/task-pulse

# 1. Build
npx next build

# 2. Kill ALL old next processes (both dev and start)
pkill -f "next start" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
sleep 2

# 3. Start production server on the proxy port
npx next start --port 3000 &

# 4. Verify
curl -s http://localhost:3000/tasks
```

Production mode eliminates HMR entirely, avoids CORS/WebSocket edge cases, and performs faster page loads over the proxy.

Pitfalls:
- `ss -ltnp` shows PIDs, use `ps -p PID -o pid,lstart,cmd` to match the oldest/newest.
- `readlink -f /proc/PID/cwd` confirms which repo directory the server is rooted in.
- When multiple servers exist, kill the one on the *proxy port*, then start a fresh one on that same port. The others can keep running for side-by-side comparison.
- After `pkill -f "next"`, always confirm with `ps aux | grep -i "[n]ext"` before starting the new server — a leftover PID on the target port will prevent the new server from binding.

## PR Review Workflow

OpenCode has a built-in PR command:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or review in a temporary clone for isolation:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Parallel Work Pattern

Use separate workdirs/worktrees to avoid collisions:

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## Session & Cost Management

For cloud-hosted coding workers where disk is scarce, prefer an **ephemeral repo lifecycle**:

1. clone into a temp dir (`mktemp -d`)
2. run `opencode run ...` in that temp repo
3. push a branch / open a PR / export a patch or bundle
4. delete the temp dir immediately

This keeps the agent installation durable while avoiding long-lived repo copies on the host.

List past sessions:

```
terminal(command="opencode session list")
```

Check token usage and costs:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

For detailed provider/auth/git/prompt-file patterns, see `references/model-provider-fallback.md`.

## Pitfalls

- **React 19: `useState<Set<string>>` does not trigger re-render.** When using `useState` with a `Set`, the updater `setState(prev => new Set(prev))` creates a new Set with the same values. React 19's bailout optimization can skip a re-render because it treats the new Set as structurally equivalent in certain code paths. This manifests as button clicks that register (event fires, state function called) but the DOM never changes. **Fix**: use `Record<string, boolean>` or a plain object pattern instead of `Set`.
- **Next.js 16: `router.refresh()` in a wrapping client component can reset child React state.** A `useEffect` calling `router.refresh()` every N seconds in a parent `"use client"` wrapper will re-render the full server component tree, which can discard `useState` in child components (expand/collapse, filter toggles, form inputs). Prefer granular SSE updates (event streams) or targeted server data refetching over blanket `router.refresh()` intervals. If you must poll, use `router.refresh()` sparingly or debounce it.
- **Next.js 16: buttons without `type="button"` may not fire `onClick`.** HTML `<button>` defaults to `type="submit"`. In React 19 / Next.js 16, this can interfere with event handling even when the button is not inside a `<form>`. Always add `type="button"` explicitly to buttons whose sole purpose is an `onClick` callback.
- **Camofox `browser_snapshot` returns a cached accessibility tree, not the live DOM.** After `browser_click` changes React state, the snapshot may still show the old content. To verify state changes, curl the page HTML directly (`curl -s <url>`) and check for the expected strings, or use `browser_navigate` to force a fresh navigation before snapshotting.
- Interactive `opencode` (TUI) sessions require `pty=true`. The `opencode run` command does NOT need pty.
- In Task Pulse live runs, prompts that say "improve repo X" are not sufficient by themselves when the task `cwd` is still the Task Pulse repo. Without an explicit clone/workdir step, OpenCode may read the GitHub URL and then start editing Task Pulse UI files it sees locally.
- In Task Pulse live runs, cloning into `/tmp` or other directories outside the allowed workspace can trigger `permission requested: external_directory ... auto-rejecting`. Prefer a repo clone under the runner-owned workspace such as `projects/<task-name>`.
- In Task Pulse itself, `.task-pulse-data/` is runtime state and gitignored. If a user asks to "put it in the repo" or the fix must survive redeploys, do not rely on editing snapshot JSON alone; add a repo-level migration/normalization path in store code and commit that instead.
- `/exit` is NOT a valid command — it opens an agent selector. Use Ctrl+C to exit the TUI.
- `--model deepseek` (provider prefix omitted) may print "Invalid model format" and fall back to auto-detection. Always use the full form `--model provider/model` (e.g. `--model deepseek/deepseek-chat`, `--model openrouter/anthropic/claude-sonnet-4`) to avoid ambiguity.
- When the installation binary is at a nonstandard path (e.g. `/home/ubuntu/.hermes/node/bin/opencode` for a user-local npm install), use the explicit path in commands to avoid resolution issues.
- PATH mismatch can select the wrong OpenCode binary/model config.
- **Shell commands that sleep or wait (like `pkill -f ...` followed by `sleep`) can block OpenCode's PTY indefinitely.** If your task instruction tells OpenCode to restart a server with `pkill` + `sleep`, it may hang forever because OpenCode's TUI wraps the shell and the interactive kill signal gets consumed. Prefer telling OpenCode to just write the code change and leave server restart to you, or use a non-blocking command pattern.
- **Free models work without any API key**: `opencode/deepseek-v4-flash-free`, `opencode/nemotron-3-super-free` — these are OpenCode-hosted models. Useful for testing or when no provider credentials are configured. List available free models with `opencode models`.
- **`--model deepseek/deepseek-chat` may fail** with "No access to model: xai/grok-3-mini" (an unrelated model) when credentials are missing. The error message can be misleading — check `opencode providers list` and `DEEPSEEK_API_KEY` env var first.
- If OpenCode appears stuck, inspect logs before killing:
  - `process(action="log", session_id="<id>")`
- **Background `opencode run` may produce zero visible output for 20+ seconds** even when the process is running correctly. The shell wrapper (`bash -lic`) buffers stdout, and the model takes time to generate its first response. Do NOT kill the process prematurely — check `ps aux | grep opencode` to confirm it's actually running with ~200-300MB resident memory. If it's using memory and displaying a full command line with the prompt text, it's processing.
- Avoid sharing one working directory across parallel OpenCode sessions.
- Enter may need to be pressed twice to submit in the TUI (once to finalize text, once to send).
- **Task Pulse live runner may spawn OpenCode but produce zero output.** If `worker.log` is empty and the task transitions to `completed` with no events beyond `task.created`, the spawned OpenCode process probably exited immediately without connecting to the task stream. This can happen when the prompt is too short, the model selection fails silently, or the `cwd` doesn't match the repo OpenCode should edit. Debug: check `cat .task-pulse-data/<id>.worker.log`, verify OpenCode's stderr for model/provider errors, and try running OpenCode directly from the terminal to rule out runner-level issues.

## Verification

Smoke test:

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Success criteria:
- Output includes `OPENCODE_SMOKE_OK`
- Command exits without provider/model errors
- For code tasks: expected files changed and tests pass

## Rules

1. Prefer `opencode run` for one-shot automation — it's simpler and doesn't need pty.
2. Use interactive background mode only when iteration is needed.
3. Always scope OpenCode sessions to a single repo/workdir.
4. For long tasks, provide progress updates from `process` logs.
5. Report concrete outcomes (files changed, tests, remaining risks).
6. Exit interactive sessions with Ctrl+C or kill, never `/exit`.
7. **Delegate code-writing to OpenCode; do not edit code files directly.** When the task is code-related (implementing features, refactoring, patching TypeScript/JS/Python files), write a prompt file to disk and hand it to `opencode run` rather than using `write_file` or `patch` yourself. This applies to any repo, not just the one OpenCode is hosted in. The exception is small config changes or one-line fixes in non-code files (markdown, YAML, JSON config).
