# Task Pulse Mock Data Reference

`src/lib/task-pulse/mock-data.ts` ships 4 demo tasks with hardcoded group names:

| Mock Task ID | Hardcoded `metadata.groupName` | Last Known Fix |
|---|---|---|
| `task_demo_live` | "Task Pulse 完善" | Was "task-Pluse 完善" — fixed Jun 4 |
| `task_done_metrics` | "Task Pulse 完善" | Was "task-Pluse 完善" — fixed Jun 4 |
| `task_approval_cmd` | "Task Pulse 完善" | Was "task-Pluse 完善" — fixed Jun 4 |
| `task_blocked_approval` | `AUTO_GROUP_MAP.chat` → "日常聊天" | ✅ already correct |

These tasks exist **only in memory** (no `task_*.json` file on disk). They are loaded during `ensureStoreBooted()` and mixed into API responses via `listTasks()`.

**When renaming a group, update all 3 places:**
1. `~/.task-pulse-data/task_*.json` files (if the group has persisted tasks)
2. `src/lib/task-pulse/mock-data.ts` (search for the old groupName string)
3. `npm run build` + full server restart (the new bundle must reflect the source change)

**To find all hardcoded group names:**
```bash
grep -n 'groupName' src/lib/task-pulse/mock-data.ts
```
