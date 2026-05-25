---
name: task-pulse-workflow
description: "Use when the user requests any actionable work (coding, PPT, research, testing, config backup) that produces a deliverable. Creates a task-pulse task record before execution, properly grouped and tracked."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [task-pulse, workflow, tracking, productivity, task-management]
    related_skills: [github-pr-workflow, kanban-orchestrator]
---

# Task Pulse 任务管理工作流

## Overview

所有有明确产出的操作（改代码、生成 PPT、文档撰写、跑测试、配置备份、做调研等）必须先通过 task-pulse 创建任务记录，再动手执行。任务完成后更新状态。

即时问答、简单查询、秒级操作不需要建任务（避免刷屏）。

**核心原则：先建任务，再动手。不是干完再补。**

## 触发条件

- 用户说"做一下"/"完善一下"/"帮我XX"等操作请求
- 用户要求改代码、生成文档/PPT/图片
- 用户要求跑测试/验证/调研
- 任何需要后续跟踪或回顾的工作
- **Hermes 主动发起的操作**（如配置备份、系统改进）同样需要建任务

不触发：简单问答、状态查询、秒级操作。

## 步骤

### 1. 创建任务

通过 `POST /api/tasks` 创建任务，**然后**再开始工作。

```python
import urllib.request, json

payload = {
    "title": "清晰的标题（必须写明白）",
    "prompt": "任务详细描述",
    "category": "coding|ppt|chat|paper",
    "runner": "opencode|hermes",
    "model": "deepseek/deepseek-chat",
    "source": "微信|控制台|手动",
    "mode": "live|demo",       # live=启动runner, demo=模拟进度
    "groupName": "正确的分组名称",
    "repoLink": "关联仓库URL"
}

req = urllib.request.Request(
    "http://localhost:3000/api/tasks",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=10)
d = json.loads(resp.read())
task_id = d["task"]["id"]
```

或用 curl：
```bash
curl -s -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"...","category":"coding","runner":"opencode","groupName":"task-Pluse 完善"}'
```

### 2. 分组规则

分组名必须有辨识度，**严禁使用"项目开发"等通用名称**。

| 项目 | 分组名 |
|------|--------|
| task-pulse / 任务面板相关 | `task-Pluse 完善` |
| agent 仓库相关 | `agent 仓库联调` |
| Hermes Agent 配置备份 | `Hermes 配置备份` |
| 新项目 | 按项目名创建有辨识度的分组名 |

- ❌ 反例：把 PPT/备份/测试随意扔到"项目开发"
- ✅ 正例：task-pulse 的 PPT → `task-Pluse 完善`，agent 仓库改进 → `agent 仓库联调`
- 如果不确定分组名，先 GET `/api/tasks` 检查已有任务有哪些组，选最接近的
- HIGH GROUP: 分组是**大任务**的标识，决定了 dashboard 上的展示结构

### 3. 标题规范

- 标题必须写明白，一眼能看出任务内容
- ❌ 反例："完善一下"、"改个东西"
- ✅ 正例："agent 仓库 README 补全"、"任务详情页增加自动滚动"
- 大任务标题尤其要清晰，因为它是分组的展示名称

### 4. 分类标签

任务创建时必须指定正确的 `category`：

| 分类 | 代码 | 图标 |
|------|------|------|
| 写代码 | `coding` | 💻 |
| 生成 PPT | `ppt` | 📊 |
| 聊天/问答 | `chat` | 💬 |
| 论文/研究 | `paper` | 📄 |

dashboard 的 SubTaskRow 会自动显示分类标签。

### 5. 任务状态跟踪

创建任务后可通过 `GET /api/tasks` 查看最新状态。SSE 实时流在详情页自动连接。

状态流转：`queued` → `running` → `done|failed|stopped|blocked|approval_required`

## 与其他 Hermes 功能的关系

- **Hermes Kanban** (`kanban-orchestrator`, `kanban-worker`): 与 task-pulse 是互补关系。Kanban 管理 Hermes 自身的多 agent 编排；task-pulse 管理面向用户的产出任务。当用户直接要求做事时走 task-pulse；当 Hermes 需要拆分子任务给 agent 时走 Kanban。
- **GitHub PR Workflow** (`github-pr-workflow`): task-pulse 中的 coding 类任务通常会触发 PR 流程。建议先建 task-pulse 任务，再走 PR 流程。

## References

加载本 skill 后，`skill_view(name='task-pulse-workflow', file_path='references/api-examples.md')` 查看更多实操示例。

## Common Pitfalls

1. **跳过建任务直接干活** — 用户强调所有操作走 task 方便管理。即使操作很简单也必须建。
2. **非代码工作不豁免** — PPT 生成、文档撰写、截图、调研分析、配置备份等 Hermes 手动操作同样必须建任务。
3. **先建任务再干活，不是干完再补** — 任务应该以 `queued` 状态出现在 dashboard 上，等做完再更新状态。
4. **分组名太通用** — "项目开发"太笼统，必须用有辨识度的名字。不确定时先查已有分组。
5. **大任务标题模糊** — "完善一下"不行，要"agent 仓库 README 补全"这样清晰的。
6. **demo 模式任务会自动跑完** — 模拟进度，real 模式才需要 runner 进程。
7. **修改任务文件后需要重启 next server** — 或者等 demo simulation 完成。

## Verification Checklist

- [ ] 任务已通过 POST `/api/tasks` 创建并返回 task ID
- [ ] 分组名有辨识度，不是"项目开发"等通用名
- [ ] 标题清晰可读，一眼能看懂
- [ ] 分类标签正确（coding/ppt/chat/paper）
- [ ] 实际工作已执行
- [ ] 任务状态已更新为 done（如适用）
- [ ] 用户能在 pulse.zaiyemeiyou.com 看到任务
