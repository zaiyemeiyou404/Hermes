# Task Launcher UI 模式参考

本文档记录 task-pulse 启动任务界面的 UI 约定。

## 模型选择器

位于启动按钮右侧的 inline 下拉框，分为三组：

```
├─ 🤖 Hermes (GPT)
│   gpt-5.4, gpt-5.5
├─ 🧠 DeepSeek (OpenCode)
│   deepseek/deepseek-chat, deepseek/deepseek-reasoner
├─ 🔌 其他
│   gpt-4o, gpt-4o-mini, claude-sonnet-4, ...
```

**规则：**
- 必须用 `<select>` 下拉框，不要用文本输入框
- 默认选中 `deepseek/deepseek-chat`（用户最常用）
- 用 `<optgroup>` 分组展示，每组加 emoji 前缀
- 样式：`rounded-full border bg-white/5 text-xs`，与右侧批注标签一致

## 返回首页按钮

任务详情页（`/tasks/[taskId]`）顶部必须有「← 返回首页」按钮：

- 位置：`<main>` 内部、第一个 `<section>` 之前
- 导航目标：`router.push("/tasks")`
- 交互：悬停变色 `hover:bg-cyan-400/10 hover:text-cyan-200`，SVG 箭头向左位移 `group-hover:-translate-x-0.5`
