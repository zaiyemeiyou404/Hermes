---
name: sci-fi-novel-pipeline
category: creative
description: AI-assisted hard sci-fi novel writing pipeline — world-building, outline generation, chapter-by-chapter production. Supports 三体/基地-style storytelling for 番茄小说 and other platforms.
trigger: User wants to write or generate a sci-fi novel, short story, or content pipeline — especially hard sci-fi (Three Body Problem/Foundation style).
---

# Hard Sci-Fi Novel Pipeline

AI-assisted novel writing pipeline for hard sci-fi (similar to Three Body Problem / Foundation) and adjacent large-scale space opera. Supports world-building → outline generation → chapter-by-chapter production.

## Mode Selection

Before drafting, classify the novel direction so the structure matches the user's intent:

### A. Hard sci-fi / concept-first mode
Use when the book is driven by one or more scientific or philosophical ideas (e.g. 黑暗森林, entropy, first contact paradoxes, civilization traps).

Deliverables:
- `world/current-setting.md` centered on 1-3 core concepts
- 30-chapter outline where each chapter carries a science/philosophy concept
- chapter prose that prioritizes thought, scale, and cold precision

### B. Space-opera / civilization-first mode
Use when the user wants multiple civilizations, political systems, fleet classes, planets, hierarchy, and a protagonist who rises through institutions.

Deliverables:
- `world/current-setting.md` with civilization blocs, political logic, world types, military ladder, and protagonist arc
- `outline/<title>.json` with multi-arc advancement (frontier → fleet → diplomacy → governance → expedition works well)
- companion world-bible docs under `world/`, for example:
  - `角色与体系细化-<title>.md`
  - `制度与军政设定-<title>.md`
  - `星球与联邦设定-<title>.md`

For richer long-form projects, proactively produce additional world-bible docs under `world/` beyond the base three. Common high-value companions are:
- `人类谱系与起源设定-<title>.md` — human lineage, migration history, phenotypic branches, and political arguments over who counts as properly human.
- `外星文明设定-<title>.md` — 3-5 major alien civilizations with origin, body plan, senses, social structure, values, and human conflict points.
- `外星舰船设定-<title>.md` — alien ship design language, build logic, command model, battle doctrine, representative classes, and visual cues.

When the user asks short follow-ups like "联邦的制度设计什么的" or "其他外星人呢？", treat them as requests to extend the same world-bible immediately rather than re-explaining prior context.

For this mode, do **not** over-force a single cosmic mystery. The narrative can be held together by institutional ascent, competing civilizations, colonial frontier pressure, and recurring political/military consequences.

For richer long-form projects, proactively produce additional world-bible docs under `world/` beyond the base three. Common high-value companions are:
- `人类谱系与起源设定-<title>.md` — human lineage, migration history, phenotypic branches, and political arguments over who counts as properly human.
- `外星文明设定-<title>.md` — 3-5 major alien civilizations with origin, body plan, senses, social structure, values, and human conflict points.
- `外星舰船设定-<title>.md` — alien ship design language, build logic, command model, battle doctrine, representative classes, and visual cues.

When the user asks short follow-ups like "联邦的制度设计什么的" or "其他外星人呢？", treat them as requests to extend the same world-bible immediately rather than re-explaining prior context.

### Space-opera opening rules (important)
For fleet-era / empire-frontier novels, do **not** default to a low-tech opening where the chapter immediately becomes ground monster fighting or hand-to-hand survival. First establish that the frontier is a **contact zone between civilizations**:
- border sectors can be war zones, ceasefire belts, trade corridors, or mixed-status buffer regions
- developed frontier worlds should usually have orbital defense belts, surveillance satellites, shield grids, garrison fleets, and warning infrastructure
- undeveloped worlds still need strategic framing: beacons, picket satellites, exclusion zones, scout posts, or contested jump approaches
- mention higher-order logistics early when relevant: wormholes / star gates / jump corridors / spatial transition windows / supply lanes
- make it clear that in a starship era, decisive conflict usually begins in **orbit, at gates, on supply routes, or around jump points**; ground-level danger is downstream from that larger military system

If the user objects that the opening feels "too low-tech" or "not like a starship era", revise by adding orbital viewpoint, defense architecture, fleet presence, and strategic border context before any local danger scene.

### Character-introduction rules for chapter drafts
When the user asks who the protagonist's friend is, or says the cast relationships feel unclear, do not answer with only role labels like "teammate" or "engineer". Make the relationship legible in the prose and notes:
- explicitly identify the **core friend** for the current arc (for example: brother-in-arms / can-trust-with-your-back)
- distinguish that person from other allies such as a **technical partner**, **senior/mentor**, or **future love interest**
- give a concrete "how they met" hook that can be dropped straight into the chapter: a repair incident, shared danger, training cohort, first technical collaboration, etc.
- for close friends, show the bond through fast recognition and private habits/signals, not by exposition alone
- for technical allies, prefer "first respected each other's brain" before deep emotional trust

A good first-chapter cast pattern is:
- one clearly established old friend with survival history
- one future important ally introduced later through competence and friction
- one senior/leader figure who provides local authority and edge-of-frontier experience

## Project Structure

```
~/novel/
├── world/
│   ├── world-building-template.md    ← 世界观构建模板
│   └── current-setting.md            ← 当前小说设定（核心）
├── pipeline/
│   ├── chapter-prompt.md             ← 硬科幻写作风格 prompt
│   └── generate_chapter.py           ← Python 章节生成器
├── outline/                          ← 小说完整大纲（JSON）
├── chapters/                         ← 生成的章节
└── reference/                        ← 参考资料
```

## Workflow

### 1. 建立世界观
先确定是 **concept-first** 还是 **civilization-first**。

`current-setting.md` 至少应包含：
- 一句话梗概
- 核心驱动力（科学概念 或 文明制度矛盾）
- 时代背景
- 主要势力
- 视角角色 / 主角晋升路线
- 叙事结构（时间/空间跨度）

如果是 civilization-first（帝国/联邦/多文明太空歌剧）额外补：
- 文明阵营与制度差异
- 关键世界类型（圣都、铸造世界、要塞世界、开拓世界等）
- 战舰与武器层级
- 能长期连载的职位成长链

参考 `world-building-template.md` 辅助构思。

### 2. 生成大纲
用 `current-setting.md` 调用脚本生成 30 章大纲：

```bash
cd ~/novel && python3 pipeline/generate_chapter.py outline world/current-setting.md
```

或用 OpenCode 生成大纲 JSON 保存到 `~/novel/outline/`。

大纲格式：每章 title + 200字 summary + science_concept + hook。

### 3. 逐章生成
```bash
python3 pipeline/generate_chapter.py "第1章：xxx" outline/小说名.json
```

或在 Hermes 中用 cron 定时生成。

### 4. 交付时的沟通格式（重要）
当用户要求“开始写提纲和正文”这类一次性产出多个写作交付物时，不要只笼统说“写完了”。要在回复里**明确拆开列出**：
- 提纲是否已写
- 第一章/正文是否已写
- 各自保存路径
- 如用户是极简沟通风格，优先直接给一句可执行式确认：`提纲已写，在 …；第一章已写，在 …`。

如果用户随后问“提纲写了吗”“第一章内容呢”“发过来”，这表示他要的不是摘要，而是**直接看到正文内容**。此时应直接粘贴对应全文或大段关键内容，不要只重复文件路径或继续概述。

## Hard Sci-Fi Writing Rules

### Core Principles
1. **思想驱动叙事** — 每章一个核心科学/哲学概念，情节为其服务
2. **冷峻克制** — 避免情感渲染，用事实和逻辑制造震撼
3. **尺度感** — 用时间跨度、空间距离、数量级对比制造宏大感
4. **反常识但自洽** — 设定违反直觉但内部逻辑严谨

### Chapter Structure
```
【引子】细节/数据片段暗示核心思想
【展开】剧情中自然呈现科学概念
【转折】新信息颠覆认知
【收束】留下悬念
```

### Style
- 语言简洁精确（类似科普文学化表达）
- 对话有信息密度
- 场景描写"科学家式的观察"——先现象后原理
- 紧张感来自：信息差、时间压力、认知颠覆
- **禁用词**：突然、震惊地、不可思议地、惊呆了、泪流满面
- **推荐用词**：意识到、推算出、观察到、坐标显示、误差范围内

## Platforms

- **番茄小说** — 免费阅读+广告分成，适合长篇连载日更
- **知乎盐选** — 适合短篇/中篇悬疑脑洞

## Pitfalls

- 用户可能在早期迅速推翻整套母设定（例如从《三体》式概念驱动切到帝国/联邦多文明太空歌剧）。发生这种 pivot 时，不要只局部修补；应重写 `world/current-setting.md`，并让 outline / 角色文档 / 制度文档全部切换到同一套设定。
- 对于 civilization-first 项目，仅有 `current-setting.md` 往往不够。最好同步产出至少 1-3 份 world-bible 文档，分别覆盖角色与成长线、制度与军政、星球与文明细节。
- DEEPSEEK_API_KEY 可能被安全机制屏蔽，无法直接在 Python 子进程中使用。临时解决：用 Hermes shell 传 `DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY"`。稳定方案：用 opencode run 代替直接 API 调用。
- 大纲用 JSON 格式输出，文件名用小说标题。
- 章节生成温度 0.8 左右，大纲规划温度 0.7。
- 番茄要求日更 1-2 章才能有流量推荐，考虑 cron 定时每天自动生成+你审核后发布。

## Linked Files

- `references/world-building-template.md` — 世界观构建框架
- `references/chapter-prompt.md` — 硬科幻写作风格 prompt
- `templates/current-setting.md` — 空的世界设定模板
- `scripts/generate_chapter.py` — 章节生成器脚本
