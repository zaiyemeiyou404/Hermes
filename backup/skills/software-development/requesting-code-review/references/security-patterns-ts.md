# TypeScript / JavaScript Security Patterns

Patterns to flag during review. Distilled from real audit findings.

## Shell Injection via string interpolation

```typescript
// BAD — user-controlled or file-sourced value interpolated into shell
const command = `nohup ${bin} ${taskId} >> ${log} 2>&1 &`;
spawn("bash", ["-lc", command], { ... });

// GOOD — args array, no shell parsing
spawn(process.execPath, [script, taskId], {
  env: { ...process.env, ...vars },
  detached: true,
  stdio: "ignore",
});
```

Flag any `spawn("bash", ...)` or `spawn("sh", ...)` where arguments are built via template string. Even if the value is internally generated today, it's a pattern that degrades.

## Hardcoded credentials / identifiers in mock data

```typescript
// BAD — real user IDs in mock-data.ts or store defaults
target: "weixin:o9cq8070Ill3Nq2HQBoDp8qBgPts@im.wechat"
```

Mock data files should use clearly fake identifiers (`test-user-001`, `demo-target@example.com`). Real IDs should come from environment variables or config.

## Hardcoded server paths

```typescript
// BAD — paths that only work on one machine
const OPENCODE_BIN = "/home/ubuntu/.hermes/node/bin/opencode";
const DEFAULT_CWD = "/home/ubuntu/task-pulse";
```

Flag all absolute paths in source code. Should use `process.env.X || sensibleDefault` pattern.

## Double-write on state mutation

```typescript
addEvent(taskId, "task.retried", ...);  // mark() internally calls writeSnapshotFile()
writeSnapshotFile(ensureTask(taskId));   // writes again — redundant, potential race
```

When a helper like `addEvent`/`setStatus`/`addLog` already persists via `mark()`, the caller should not persist again.

## SSE polling disguised as push

```typescript
const interval = setInterval(() => {
  const nextVersion = getTaskVersion(taskId);  // reads from disk every 1s
  if (nextVersion !== currentVersion) send("task.updated", snapshot);
}, 1000);
```

This is long-polling, not real SSE push. For true push: use EventEmitter in the writer process, `fs.watch` on the data file, or a message bus between writer and server.

## Detached process lifecycle

When `spawn(... { detached: true, stdio: "ignore" })` + `child.unref()` is used, the worker outlives the orchestrator. On orchestrator restart:
- Worker continues running but is unreachable
- Stop/retry controls break (process handle is in lost memory)
- Solution: persist worker PID in the task snapshot, re-read on boot
