# Task Pulse Store Boot Stability

When OpenCode modifies `src/lib/task-pulse/store.ts`, the `ensureStoreBooted()` function is critical — it loads INITIAL_TASKS (mock data) and persisted live snapshots into the in-memory TASKS Map on first call.

## Common Failure: Silent Task Loss

`ensureStoreBooted()` calls `registerGroup(snapshot)` on each loaded snapshot. If `registerGroup` throws (e.g. due to missing fields, a category not in `AUTO_GROUP_MAP`, or a malformed `inferGroupId` result), the `forEach` loop stops for the current batch — **all subsequent tasks are silently skipped**.

**Symptom**: Mock tasks like `task_demo_live` return 404 from `GET /tasks/{id}`, but the `/tasks` list shows fewer tasks than expected. The server log has no error.

**Fix**: Wrap each `registerGroup()` call in `try/catch`:

```typescript
INITIAL_TASKS.forEach((snapshot) => {
  if (DELETED_IDS.has(snapshot.task.id)) return;
  const copy = deepClone(snapshot);
  TASKS.set(copy.task.id, copy);                    // Save first — survives register failure
  versions.set(copy.task.id, copy.version ?? 0);
  try {
    registerGroup(copy);                             // Group is non-critical metadata
  } catch {
    // Group registration is cosmetic — task data is already loaded
  }
});
```

The same pattern applies to the `persisted` (live snapshot) loop.

## When to Verify

After any OpenCode change to:
- `src/lib/task-pulse/types.ts` (Task interface, TaskCategory, AUTO_GROUP_MAP)
- `src/lib/task-pulse/mock-data.ts` (INITIAL_TASKS structure)
- `src/lib/task-pulse/utils.ts` (inferGroupId, inferGroupName)
- `src/lib/task-pulse/store.ts` (ensureStoreBooted, registerGroup, readSnapshotFile)

Verify with:
```bash
# All mock tasks load
curl -s http://127.0.0.1:3000/api/tasks | python3 -c "import json,sys; tasks=json.load(sys.stdin); print(f'Loaded {len(tasks)} tasks')"

# Specific task that was previously 404
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/tasks/task_demo_live

# All groups render in the UI
curl -s http://127.0.0.1:3000/tasks | grep -c '展开小任务'
```
