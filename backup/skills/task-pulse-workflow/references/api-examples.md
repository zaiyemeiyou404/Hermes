# Task-Pulse API 实操示例

## 创建任务（Python）

```python
import urllib.request, json

def create_task(title, category="coding", group_name="task-Pluse 完善",
                runner="hermes", mode="demo", repo_link=None,
                model="deepseek/deepseek-chat"):
    """Create a task-pulse task. Returns (task_id, response_dict).
    
    model: 任务启动器（launcher UI）现已支持自定义模型名。
           默认 deepseek/deepseek-chat，可改为 deepseek/deepseek-reasoner,
           gpt-4o, gpt-4o-mini, o3-mini 等。
    """
    payload = {
        "title": title,
        "prompt": title,
        "category": category,
        "runner": runner,
        "model": model,
        "source": "微信",
        "mode": mode,
        "groupName": group_name,
    }
    if repo_link:
        payload["repoLink"] = repo_link

    req = urllib.request.Request(
        "http://localhost:3000/api/tasks",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=10)
    d = json.loads(resp.read())
    return d["task"]["id"], d
```

## 创建任务（curl）

```bash
curl -s -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完善 agent 仓库 README",
    "category": "coding",
    "runner": "opencode",
    "model": "deepseek/deepseek-chat",
    "source": "微信",
    "mode": "live",
    "groupName": "agent 仓库联调",
    "repoLink": "https://github.com/zaiyemeiyou404/agent"
  }'
```

## 查看所有任务

```bash
curl -s http://localhost:3000/api/tasks | python3 -m json.tool
```

## 更新任务状态（直接改文件）

当 mode=demo 或 need 手动标记完成时：

```python
import json
from datetime import datetime, timezone

path = f"/home/ubuntu/task-pulse/.task-pulse-data/{task_id}.json"
with open(path) as f:
    data = json.load(f)

data["task"]["status"] = "done"
data["task"]["phase"] = "completed"
data["task"]["endedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
data["task"]["durationMs"] = int((end - start) * 1000)
data["task"]["progressPercent"] = 100

with open(path, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 需要重启 next server 让内存数据生效
```

## 分组迁移（批量改文件路径）

```python
import json, glob

data_dir = "/home/ubuntu/task-pulse/.task-pulse-data"
new_name = "task-Pluse 完善"
new_id = "group_task-pluse-完善-https-github-com-zaiyemeiyou404-ta"

for fpath in glob.glob(f"{data_dir}/task_*.json"):
    with open(fpath) as f:
        data = json.load(f)
    
    task = data["task"]
    old_group = task.get("metadata", {}).get("groupName", "")
    
    if old_group == "项目开发":
        task["groupId"] = new_id
        task["metadata"]["groupId"] = new_id
        task["metadata"]["groupName"] = new_name
        
        with open(fpath, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

## 常见分组 ID 映射

| 分组名 | groupId |
|--------|---------|
| task-Pluse 完善 | `group_task-pluse-完善-https-github-com-zaiyemeiyou404-ta` |
| agent 仓库联调 | `group_agent-仓库联调` |
| 日常聊天 | `group_日常聊天` |
| 代码开发（默认） | `group_代码开发` |
