---
name: task-pulse-workflow
description: 使用 task-pulse 管理所有操作任务 — 创建、分组、标记、跟踪。所有有明确产出的工作必须先创建 task-pulse 任务。
---

# Task Pulse 任务管理工作流

## 核心规则（必须遵守）

1. **先建任务，再动手** — 用户说"做"/"完善"/"帮我XX"必须先 POST `/api/tasks` 创建任务，不能事后补
2. **分类要准** — task-pulse 相关任务归 "task-Pluse 完善" 组，agent 仓库归 "agent 仓库联调"，严禁通用分组
3. **标题要明白** — "完善一下"不行，要 "agent 仓库 README 补全" 这种一眼看懂
4. **标签要正确** — coding/ppt/chat/paper 分类必填，SubTaskRow 自动显示 📊💻💬 标签

## 触发条件
- 用户要求做任何有明确产出的工作（改代码、生成 PPT、跑测试、做调研等）
- 用户说"做一下"/"完善一下"/"帮我XX"等操作请求
- 用户主动提及 task-pulse
- 任何需要后续跟踪或回顾的工作

## 步骤

### 1. 先建任务，再动手

通过 `POST /api/tasks` 创建任务，**然后**再开始工作。

```
POST http://localhost:3000/api/tasks
{
  "title": "清晰的标题（必须写明白）",
  "prompt": "任务详细描述",
  "category": "coding|ppt|chat|paper",
  "runner": "opencode|hermes",
  "model": "deepseek/deepseek-chat",
  "source": "微信|控制台|手动",
  "mode": "live|demo",
  "groupName": "正确的分组名称",
  "repoLink": "关联仓库URL"
}
```

### 2. 分组规则（重要）

- **task-pulse 相关任务** → 归入 `"task-Pluse 完善"` 组
- **agent 仓库相关任务** → 归入 `"agent 仓库联调"` 组
- **其他项目** → 按项目名创建对应分组
- **严禁**随意扔到"项目开发"等通用分组
- ❌ 反例：PPT 是关于 task-pulse 的，却放到 "项目开发" 组
- ✅ 正例：PPT 是关于 task-pulse 的，放在 "task-Pluse 完善" 组

### 3. 标题规范

- 必须写明白，一眼能看出任务内容
- ❌ 反例："完善一下"、"改个东西"
- ✅ 正例："agent 仓库 README 补全"、"任务详情页增加自动滚动"

### 4. 分类标签

任务创建时必须指定正确的 `category`：
- `coding` — 写代码（💻 写代码）
- `ppt` — 生成 PPT（📊 生成PPT）
- `chat` — 聊天/问答（💬 聊天）
- `paper` — 论文/研究

dashboard 的 SubTaskRow 会自动显示分类标签。

### 5. 任务状态跟踪

创建任务后可通过 GET `/api/tasks` 查看最新状态。SSE 实时流在详情页自动连接。

### 陷阱

- **不要跳过建任务直接干活** — 用户强调所有操作走 task 方便管理
- **非代码工作不豁免** — PPT 生成、文档撰写、截图、调研分析、配置备份等 Hermes 手动操作同样必须建任务。
- **先建任务再干活，不是干完再补** — 任务应该以 queued 状态出现在 dashboard 上，等做完再更新状态。
- **分组名要准确** — 检查已有任务的 groupName，保持一致
- **关于 task-pulse 本身的任务（PPT、文档、UI 改进、配置备份等）必须归到 task-Pluse 完善 组**，不能放 项目开发 或其他通用分组。
- **大任务标题要写明白** — 不能"完善一下""改个东西"，要"agent 仓库 README 补全"这样的清晰标题
- **demo 模式的任务会自动跑完**（模拟进度），real 模式需要 runner 进程
- **修改任务文件后需要重启 next server**（或等 demo simulation 完成）
