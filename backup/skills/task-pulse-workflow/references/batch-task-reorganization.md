# Batch Task Reorganization

当需要批量整改 task-pulse 的分组、分类、仓库链接等元数据时，直接编辑 `.task-pulse-data/*.json` 文件比逐个通过 API 操作更高效。

## 适用场景

- 清理过时的验证/测试任务
- 重新分配任务到正确的分组
- 修复缺失的 category、groupName、repoLink
- 删除冗余任务

## 步骤

### 1. 定义映射

```python
import json, pathlib

DATA_DIR = pathlib.Path("/home/ubuntu/task-pulse/.task-pulse-data")

# 分组映射: task_id -> (groupName, groupId, repoLink, category_fix)
GROUPS = {
    "task_xxxx": ("task-Pluse 完善", "group_task-pluse-完善-...", "https://github.com/user/repo", None),
}

# 要删除的 task ID
STALE_IDS = ["task_xxx", "task_yyy"]
```

### 2. 执行更新

```python
for f in sorted(DATA_DIR.glob("task_*.json")):
    tid = f.stem
    if tid in deleted: continue
    
    data = json.loads(f.read_text())
    task = data["task"]
    
    if tid in STALE_IDS:
        deleted.add(tid)
        f.unlink()  # 删除文件
        continue
    
    mapping = GROUPS.get(tid)
    if mapping:
        group_name, group_id, repo_link, cat_fix = mapping
        task["groupName"] = group_name
        task["groupId"] = group_id
        task["metadata"]["groupName"] = group_name
        task["metadata"]["groupId"] = group_id
        if repo_link:
            task["repoLink"] = repo_link
            task["metadata"]["repoLink"] = repo_link
        if cat_fix:
            task["category"] = cat_fix
        
        (DATA_DIR / f.name).write_text(json.dumps(data, ensure_ascii=False, indent=2))
```

### 3. 更新删除记录

```python
DELETED_FILE = DATA_DIR / ".deleted-task-ids.json"
existing = json.loads(DELETED_FILE.read_text()) if DELETED_FILE.exists() else []
json.dump(sorted(existing + list(newly_deleted)), open(DELETED_FILE, "w"), indent=2)
```

### 4. 重启服务器

```bash
fuser -k 3000/tcp  # 停旧进程
cd /home/ubuntu/task-pulse
npx next build && npx next start -p 3000  # 或直接 start（如果无前端改动）
```

## 注意

- **删除前确认** — 确保 task 确实是过时的验证/测试任务，不是实际的功能开发记录
- **simulation 任务会自动重跑** — demo 模式的 task 重启后会重新走模拟进度，但不影响元数据
- **内存状态 vs 文件状态** — 重启后 `ensureStoreBooted()` 会从 JSON 文件重新加载，内存中的旧状态丢失
- **groupId 一致性** — `groupId` 和 `metadata.groupId` 必须一致，否则 dashboard 分组可能出现重复
