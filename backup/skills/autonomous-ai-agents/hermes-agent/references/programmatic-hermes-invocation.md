# Programmatic Hermes Invocation for Runner Scripts

When embedding Hermes Agent as a child process inside a task-runner
worker script (for dashboards, CI pipelines, or n8n workflows), use
the single-query non-interactive mode:

```bash
hermes chat -q "<prompt>" \
  --model deepseek/deepseek-chat \
  --yolo \
  --quiet \
  --source task-pulse \
  -t terminal,file,web \
  --max-turns 30 \
  --ignore-rules
```

## Key flags

| Flag | Purpose |
|------|---------|
| `-q / --query` | Single-shot, non-interactive. Hermes runs one turn and exits. |
| `--yolo` | Bypass dangerous-command approval prompts (needed for headless runs). |
| `--quiet` | Suppress banner, spinner, and tool previews. Only emit final response and session info to stdout. |
| `--source <tag>` | Session source tag. Use `task-pulse` or `automation` for dashboards/automations so these sessions don't pollute the CLI session list. |
| `-t / --toolsets` | Comma-separated toolset list. For coding/PPT/paper tasks: `terminal,file,web`. For chat: `terminal,web`. |
| `--max-turns <N>` | Cap tool-calling iterations. 30 is a reasonable default for automation tasks. |
| `--ignore-rules` | Skip AGENTS.md/SOUL.md injection from cwd. Useful when the runner and agent share a working directory with different conventions. |

## Environment

The child process needs the same environment as the parent Hermes process, especially:
- `DEEPSEEK_API_KEY` (or the relevant provider key)
- `HOME`, `PATH`, `USER`, `LANG`
- Load from `~/.hermes/.env` if the worker script runs outside a Hermes session.

## Output parsing

Hermes `--quiet` mode writes plain text to stdout. For structured
event/log capture in a dashboard, split stdout by newlines and use
regex/heuristic matching to detect phase transitions:

```javascript
// Example phase detection from stdout lines
if (/analyzing|reading|inspecting|理解|分析/i.test(line)) {
  // → triaging phase, ~15% progress
} else if (/creating|writing|implementing|building|生成|创建|编写/i.test(line)) {
  // → coding phase, ~45% progress
} else if (/testing|validating|lint|测试|运行|检查/i.test(line)) {
  // → testing phase, ~78% progress
} else if (/completed|finished|summary|完成|汇总|总结/i.test(line)) {
  // → summarizing phase, ~92% progress
}
```

## Watchdog

Hermes can run longer than OpenCode for complex tasks — set the idle
watchdog to 5 minutes instead of 2. If Hermes produces no stdout for
5 minutes, mark the task as blocked and send a notification.
