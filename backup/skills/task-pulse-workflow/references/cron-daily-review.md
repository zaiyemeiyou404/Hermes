# Cron 每日审查配置

## 任务名称
`task-pulse-daily-check`

## 调度时间
每天北京时间凌晨 5:00（UTC 21:00）

```
0 5 * * *
```

## 交付方式
`origin` → 通过微信发送到 origin

## 审查项

### 1. 分组名审查
检测以下模式，标记为 **「需改名」**：
- "项目开发"、"默认"、"其他" 等无辨识度名称
- 只含 1 个任务的分组但可合并到其他组
- 命名风格不一致（中英混搭、拼写错误）

### 2. 分类整理检查
检测以下模式：
- category 字段为空或 null → **「缺少分类」**
- category 与标题明显不符 → **「分类疑似错误」**
- 多个任务内容相似可合并 → **「建议合并」**

### 3. 状态异常检查
检测：
- blocked → **「⚠️ 阻塞」**
- approval_required → **「👆 待审批」**
- running 超 1 小时 → **「⏱ 运行超时」**
- failed → **「❌ 失败」**

## 输出格式

### 有异常时

```
📋 每日任务状态 (凌晨5点)

### 分组名审查
✅ task-Pluse 完善 — 正常
⚠️ "杂项" — 建议合并

### 分类整理建议
⚠️ task_xxx "XX" — 缺少分类

### 各分组概况

📁 Hermes 配置备份 (1个) — ✅ 正常
📁 task-Pluse 完善 (N个) — ⚠️ 1个阻塞
...

### 异常任务
- task_xxx「标题」— ⚠️ 阻塞
- task_yyy「标题」— ❌ 失败
```

### 一切正常时

```
✅ 今日一切正常。N个任务，N个分组，无异常。
```

## 常见失败原因

### model 为 null 导致 Codex 报错
```
RuntimeError: Codex Responses request 'model' must be a non-empty string.
```

**原因**：创建 cron job 时没有显式设置 `model` 和 `provider`。当 Hermes 使用 openai-codex provider 时，model 字段不能为空。

**修复**：更新 cron job 时显式指定 model：
```
hermes cron update <job_id> \
  --model gpt-5.4 \
  --provider openai-codex
```
或通过 API：`cronjob(action="update", job_id="xxx", model={"model":"gpt-5.4","provider":"openai-codex"})`

## 注意事项

- Cron job 只做「报告」不做「自动修复」— 如有问题通过日报告知用户决策
- 如要修改 cron 配置：`hermes cron list` → `hermes cron update <job_id>`（记得同时设 model）
- 如要手动触发测试：`hermes cron run <job_id>`
- 创建 cron job 时**必须**显式设置 model 和 provider，不要依赖默认值
