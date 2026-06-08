---
# Events, Hooks & Architecture Reference
# Full taxonomy of Hermes Agent's three hook systems + Claude plugin comparison map.
# Covers event signatures, shell-hooks JSON wire format, consent model, and
# all worked examples from the user-facing docs.
---

# Events, Hooks & Architecture Reference

## Overview

Hermes has **three** independent hook systems, plus a **cron** scheduler and
**webhook** subscriptions. All are non-blocking — errors are caught and logged,
never crashing the agent.

```
┌─────────────────────────────────────────────────────────┐
│                     HERMES AGENT                         │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐  │
│  │ AGENT LOOP           │  │ GATEWAY                   │  │
│  │ (CLI + Gateway)      │  │ (async, multi-platform)   │  │
│  │                      │  │                           │  │
│  │  Plugin hooks ───────┼──│── Plugin hooks            │  │
│  │  Shell hooks ────────┼──│── Shell hooks             │  │
│  │  ────────────────    │  │                           │  │
│  │  Cron (durable)      │  │  Gateway hooks ───────────│  │
│  │  Webhook subscriptions│  │  Cron (tick)              │  │
│  └──────────────────────┘  │  Webhook server           │  │
│                            │  BOOT.md pattern           │  │
│                            └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 1. Shell Hooks (config.yaml → subprocess)

Declare shell-script hooks in `~/.hermes/config.yaml`. Runs as subprocesses
whenever the corresponding event fires. Any language (Bash, Python, Go, etc.).

**Runs in:** CLI + Gateway

### Config Schema

```yaml
hooks:
  <event_name>:             # Must be in VALID_HOOKS list (see below)
    - matcher: "<regex>"    # Optional; for pre/post_tool_call only — filters by tool name
      command: "<shell command>"  # Required; runs via shlex.split, shell=False
      timeout: <seconds>    # Optional; default 60, capped at 300

hooks_auto_accept: false    # Skip consent prompt for all hooks
```

Event names outside `VALID_HOOKS` produce a "Did you mean X?" warning and are
skipped. Missing `command` is a skip-with-warning. `timeout > 300` is clamped.

### JSON Wire Protocol

Each time the event fires, Hermes spawns a subprocess for every matching hook
(matcher permitting), pipes a JSON payload to **stdin**, and reads **stdout**
back as JSON.

**stdin — payload the script receives:**

```json
{
  "hook_event_name": "pre_tool_call",
  "tool_name":       "terminal",
  "tool_input":      {"command": "rm -rf /"},
  "session_id":      "sess_abc123",
  "cwd":             "/home/user/project",
  "extra":           {"task_id": "...", "tool_call_id": "..."}
}
```

`tool_name` and `tool_input` are `null` for non-tool events (`pre_llm_call`,
`subagent_stop`, session lifecycle). The `extra` dict carries all event-specific
kwargs. Unserialisable values are stringified.

**stdout — optional response:**

```jsonc
// Block a pre_tool_call (both shapes accepted; normalised internally):
{"decision": "block", "reason":  "Forbidden: rm -rf"}   // Claude-Code style
{"action":   "block", "message": "Forbidden: rm -rf"}   // Hermes-canonical

// Inject context for pre_llm_call:
{"context": "Today is Friday, 2026-04-17"}

// Silent no-op — any empty/non-matching output is fine:
{}
```

Malformed JSON, non-zero exit codes, and timeouts log a warning but never
abort the agent loop.

### Worked Shell Hook Examples

**1. Auto-format Python files after every write**

```yaml
hooks:
  post_tool_call:
    - matcher: "write_file|patch"
      command: "~/.hermes/agent-hooks/auto-format.sh"
```

```bash
#!/usr/bin/env bash
# ~/.hermes/agent-hooks/auto-format.sh
payload="$(cat -)"
path=$(echo "$payload" | jq -r '.tool_input.path // empty')
[[ "$path" == *.py ]] && command -v black >/dev/null && black "$path" 2>/dev/null
printf '{}\n'
```

**2. Block destructive `terminal` commands**

```yaml
hooks:
  pre_tool_call:
    - matcher: "terminal"
      command: "~/.hermes/agent-hooks/block-rm-rf.sh"
      timeout: 5
```

```bash
#!/usr/bin/env bash
payload="$(cat -)"
cmd=$(echo "$payload" | jq -r '.tool_input.command // empty')
if echo "$cmd" | grep -qE 'rm[[:space:]]+-rf?[[:space:]]+/'; then
  printf '{"decision": "block", "reason": "blocked: rm -rf / is not permitted"}\n'
else
  printf '{}\n'
fi
```

**3. Inject `git status` into every turn (Claude-Code UserPromptSubmit equivalent)**

```yaml
hooks:
  pre_llm_call:
    - command: "~/.hermes/agent-hooks/inject-cwd-context.sh"
```

```bash
#!/usr/bin/env bash
cat - >/dev/null   # discard stdin payload
if status=$(git status --porcelain 2>/dev/null) && [[ -n "$status" ]]; then
  jq --null-input --arg s "$status" \
     '{context: ("Uncommitted changes in cwd:\n" + $s)}'
else
  printf '{}\n'
fi
```

**4. Log every subagent completion**

```yaml
hooks:
  subagent_stop:
    - command: "~/.hermes/agent-hooks/log-orchestration.sh"
```

```bash
#!/usr/bin/env bash
log=~/.hermes/logs/orchestration.log
jq -c '{ts: now, parent: .session_id, extra: .extra}' < /dev/stdin >> "$log"
printf '{}\n'
```

### Consent Model

Each unique `(event, command)` pair prompts the user for approval the first time,
then persists to `~/.hermes/shell-hooks-allowlist.json`. Three escape hatches:

1. `--accept-hooks` flag: `hermes --accept-hooks chat`
2. `HERMES_ACCEPT_HOOKS=1` env var
3. `hooks_auto_accept: true` in `config.yaml`

Non-TTY runs (gateway, cron, CI) need one of these.

### The `hermes hooks` CLI

| Command | What it does |
|---------|--------------|
| `hermes hooks list` | Dump configured hooks with matcher, timeout, consent status |
| `hermes hooks test <event> [--for-tool X] [--payload-file F]` | Fire every matching hook against a synthetic payload |
| `hermes hooks revoke <command>` | Remove allowlist entries matching `<command>` |
| `hermes hooks doctor` | Check exec bit, allowlist, mtime drift, JSON validity, execution time |

---

## 2. Plugin Hooks (Python plugins → ctx.register_hook())

Registered inside a plugin's `register(ctx)` function. Run in-process (same
interpreter as the agent loop). Used for tool interception, metrics,
guardrails, and session lifecycle management.

**Runs in:** CLI + Gateway

### Events (VALID_HOOKS list)

These events are shared between Plugin and Shell hooks. Each has a specific
callback signature.

#### `pre_tool_call`

Fires BEFORE every tool execution. Can **veto** (block) the tool call.

```python
def my_callback(tool_name: str, args: dict, task_id: str, **kwargs):
    # Return {"action": "block", "message": "reason"} to block
    # Any other return value → tool proceeds
```

**Context keys:** `tool_name`, `args`, `task_id`, `tool_call_id`

#### `post_tool_call`

Fires AFTER every tool execution returns (including errors).

```python
def my_callback(tool_name: str, args: dict, result: str, task_id: str,
                duration_ms: int, **kwargs):
    pass  # observer only; return value ignored
```

#### `pre_llm_call`

Fires BEFORE the LLM is called — after the user message and tool results are
assembled but before the API request. Can **inject context** into the
conversation.

```python
def my_callback(session_id: str, user_message: str, conversation_history: list,
                model: str, platform: str, **kwargs):
    # Return {"context": "additional text to inject"} to prepend to user message
```

#### `post_llm_call`

Fires AFTER the LLM produces a final response (tool loop exits).

```python
def my_callback(session_id: str, user_message: str, assistant_response: str,
                conversation_history: list, model: str, platform: str, **kwargs):
    pass  # observer only
```

#### `on_session_start`

Fires once per brand-new session (not on continuation).

```python
def my_callback(session_id: str, model: str, platform: str, **kwargs):
    pass
```

#### `on_session_end`

Fires at the very end of every `run_conversation()` call.

```python
def my_callback(session_id: str, completed: bool, interrupted: bool,
                model: str, platform: str, **kwargs):
    pass
```

#### `subagent_stop`

Fires when a `delegate_task` subagent completes (success, error, or timeout).

```python
def my_callback(child_goal: str, child_role: str, summary: str,
                session_id: str, **kwargs):
    pass
```

#### `pre_gateway_dispatch`

Fires **before** a message is dispatched into the agent loop. Only in gateway
mode. Can skip, buffer, rewrite the incoming message.

```python
def my_callback(event, **kwargs):
    # Return {"action": "skip", "reason": "..."}
    #   or {"action": "rewrite", "text": "..."}
    #   or None to let it through
```

**Context keys:** `event` (MessageEvent object with `.text`, `.source.platform`, etc.)

#### `pre_approval_request`

Fires before an approval request is shown to the user (CLI, TUI, gateway, ACP).

```python
def my_callback(command: str, description: str, pattern_key: str,
                pattern_keys: list[str], session_key: str, surface: str, **kwargs):
    pass  # observer only; cannot veto
```

#### `post_approval_response`

Fires after the user responds to an approval prompt (or times out).

```python
def my_callback(command: str, description: str, pattern_key: str,
                pattern_keys: list[str], session_key: str, surface: str,
                choice: str, **kwargs):
    pass  # choice: "once"|"session"|"always"|"deny"|"timeout"
```

#### `transform_tool_result`

Fires after a tool returns, before the result is appended to conversation.
Can **rewrite** the result the model sees.

```python
def my_callback(tool_name: str, arguments: dict, result: str,
                task_id: str | None, **kwargs) -> str | None:
    return new_result or None  # None = pass through unchanged
```

#### `transform_terminal_output`

Fires inside the `terminal` tool pipeline, **before** truncation and ANSI strip.

```python
def my_callback(command: str, output: str, exit_code: int,
                cwd: str, task_id: str | None, **kwargs) -> str | None:
    return new_output or None
```

#### `transform_llm_output`

Fires after the tool loop completes, **before** the response is delivered.
Can rewrite the assistant's final text.

```python
def my_callback(response_text: str, session_id: str, model: str,
                platform: str, **kwargs) -> str | None:
    return new_text or None  # First non-None return wins
```

### Registration

```python
# In your plugin's register() function:
def register(ctx):
    ctx.register_hook("pre_tool_call", my_callback)
    ctx.register_hook("post_tool_call", my_other_callback)
```

### Plugin hook ordering

1. Python plugin hooks run first (in registration order)
2. Shell hooks run second (in config.yaml order)
3. For `pre_tool_call`: first block wins (earliest plugin with `action: block`)
4. For `transform_*`: first non-None return wins
5. For all other events: all hooks fire; return values ignored

---

## 3. Gateway Event Hooks (HOOK.yaml + handler.py)

Dedicated hooks that fire inside the gateway process only. Each hook is a
directory under `~/.hermes/hooks/` with two files:

```text
~/.hermes/hooks/
└── my-hook/
    ├── HOOK.yaml      # Declares which events to listen for
    └── handler.py     # Python handler — must be named `handle`
```

**HOOK.yaml:**
```yaml
name: my-hook
description: Log all agent activity
events:
  - agent:start
  - agent:end
  - agent:step
```

**handler.py:**
```python
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".hermes" / "hooks" / "my-hook" / "activity.log"

async def handle(event_type: str, context: dict):
    """Called for each subscribed event. Must be named 'handle'."""
    entry = {"timestamp": datetime.now().isoformat(), "event": event_type, **context}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**Handler rules:**
- Must be named `handle`
- Receives `event_type` (string) and `context` (dict)
- Can be `async def` or regular `def` — both work

### Gateway Events

| Event | When it fires | Context keys |
|-------|---------------|-------------|
| `gateway:startup` | Gateway process starts | `platforms` (list of active platform names) |
| `session:start` | New messaging session created | `platform`, `user_id`, `session_id`, `session_key` |
| `session:end` | Session ended (before reset) | `platform`, `user_id`, `session_key` |
| `session:reset` | User ran `/new` or `/reset` | `platform`, `user_id`, `session_key` |
| `agent:start` | Agent begins processing a message | `platform`, `user_id`, `session_id`, `message` |
| `agent:step` | Each iteration of the tool-calling loop | `platform`, `user_id`, `session_id`, `iteration`, `tool_names` |
| `agent:end` | Agent finishes processing | `platform`, `user_id`, `session_id`, `message`, `response` |
| `command:*` | Any slash command executed | `platform`, `user_id`, `command`, `args` |

Wildcard matching: `command:*` fires for all `command:model`, `command:reset`, etc.

### BOOT.md Pattern (Community Tutorial)

A popular pattern: drop a checklist at `~/.hermes/BOOT.md`, and have a gateway
hook run it on every gateway startup.

1. Create a gateway hook subscribing to `gateway:startup`
2. The handler spawns `hermes chat -q "Read ~/.hermes/BOOT.md and execute"` 
3. Output suppressed via `[SILENT]` marker if nothing to report

Full tutorial in the user docs.

---

## 4. Webhook Subscriptions (External HTTP → Agent)

Hermes exposes an HTTP endpoint `/webhooks/<name>` for external automation.
Managed via `hermes webhook <verb>` CLI.

```bash
hermes webhook subscribe my-endpoint     # creates route with HMAC secret
hermes webhook list                       # list subscriptions
hermes webhook remove my-endpoint         # remove
hermes webhook test my-endpoint           # send test POST
```

Subscriptions persist to `~/.hermes/webhook_subscriptions.json` and are
hot-reloaded without gateway restart. Each subscription gets:
- A unique route at `/webhooks/<name>`
- HMAC signature validation (secret shown on creation)
- Full agent session (skills, tools, memory — same as any chat)

Enable the webhook platform in `config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "your-global-hmac-secret"
```

For n8n → Hermes → human approval patterns, see
`references/webhook-automation-with-n8n.md`.

---

## 5. Cron (Scheduled Durable Jobs)

Full documentation in the SKILL.md "Durable & Background Systems → Cron"
section. Key architectural facts not covered there:

- **File-based lock** at `~/.hermes/cron/.tick.lock` prevents duplicate ticks
  across processes (`fcntl.flock` on Linux/macOS, `msvcrt` on Windows)
- **3-minute hard interrupt** per job run (thread-level timeout)
- **Prompt injection scanning** catches threats in assembled prompts
  (including runtime-loaded skill content — closes gap from #3968)
- **SILENT marker** `[SILENT]` at start of response suppresses delivery
  (output still saved locally for audit)
- **`script` mode**: `no_agent=True` makes the script the entire job (no LLM
  invocation). Useful for data collection steps.
- **`context_from` chaining**: job B receives job A's output as context,
  enabling pipeline workflows
- **Model overrides**: per-job `model` + `provider` (pass as object, not string)

---

## 6. Claude Plugin Comparison Map

How to map Claude Code plugin concepts onto Hermes equivalents.

| Claude Concept | Hermes Equivalent | Implementation |
|---|---|---|
| `preToolCall` hook | `pre_tool_call` shell hook or plugin hook | `~/.hermes/config.yaml` → `hooks.pre_tool_call:` |
| `postToolCall` hook | `post_tool_call` shell hook or plugin hook | `~/.hermes/config.yaml` → `hooks.post_tool_call:` |
| `onCommand` event | `pre_tool_call` with `tool_name == "terminal"` | Matcher: `terminal` |
| `UserPromptSubmit` event | `pre_llm_call` shell hook (inject context) | Return `{"context": "..."}` on stdout |
| `assistantMessage` event | `post_llm_call` plugin hook or `transform_llm_output` | Register via plugin or `transform_llm_output` |
| Plugin `.claude/settings.json` | `~/.hermes/config.yaml` | Global config (per-project is future work) |
| Plugin `functions:` in plugin.yaml | Hermes custom tools via `tools/*.py` + `registry.register()` | Auto-discovered from `tools/` directory |
| Plugin skill references | `metadata.hermes.related_skills` in SKILL.md frontmatter | Cross-references resolved at load |
| `claude spawn` (subagents) | `delegate_task(goal, context, toolsets)` | Synchronous; parallel via `tasks=[...]` |
| `hookify` event hooks | Shell hooks (`hooks:` in config.yaml) + Plugin hooks | **Strictly more capable** — shell hooks can block |
| CWD-based `.claude/rules/` auto-load | No native equivalent | Future: scan cwd for `.hermes/rules/` or `SKILL.md` |
| Feature-dev workflow | `subagent-driven-development` + `github-pr-workflow` + `writing-plans` | Stack three skills; write a `feature-dev` umbrella skill |

---

## 7. Architecture Quick Reference (Code Locations)

| Component | Source file(s) |
|-----------|---------------|
| Shell hooks dispatcher | `agent/shell_hooks.py` |
| Plugin hooks registry | `model_tools.py` (hook dispatching points) + `plugins/` |
| Gateway hooks loader | `gateway/run.py` → `_register_builtin_hooks()` |
| Gateway hook discovery | `gateway/builtin_hooks/` (empty by default) + `~/.hermes/hooks/` |
| Webhook subscriptions | `hermes_cli/webhook.py` → `~/.hermes/webhook_subscriptions.json` |
| Cron scheduler | `cron/scheduler.py` (tick), `cron/jobs.py` (storage) |
| Tool discovery | `tools/registry.py` (auto-import from `tools/*.py`) |
| Toolset definitions | `toolsets.py` (`TOOLSETS` dict) |
| Hook test coverage | `tests/gateway/test_hooks.py` |
