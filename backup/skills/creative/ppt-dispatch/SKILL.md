---
name: ppt-dispatch
description: >
  PPT 生成入口调度器。当用户要创建演示文稿（PPT/slides/deck/演示/课件/汇报/分享）时，
  先从三个备选方案中匹配合适的工具，展示给用户选择。
  PPT Master 必须作为选项之一出现。
---

# PPT 生成调度器

> ## 🚨 OVERRIDING RULE：THINK → LOAD → SHOW → WAIT
>
> **这条规则的优先级高于本 skill 中任何其他内容：**
>
> **用户提到任何与「PPT/演示/slides/课件/汇报」相关的字眼后，第一步就是加载此 skill，展示三个备选方案。禁止跳过 dispatch，禁止默认选一个方案直接开工，禁止看完仓库再回头补 dispatch。展示三选项并等待用户选择后，才执行对应方案。**
>
> 这条规则被同一个用户多次纠正（至少 3 次），每次违反都构成执行失败。用户的措辞越简洁（如「生成PPT」「做个PPT」「关于X做个演示」），你越容易跳过——这是经过多次验证的高危模式。
>
> **特别警示——仓库 + PPT 组合请求（Pitfall #6 的增强版）：**
> 当用户同时说「看一下这个仓库」+「做个关于它的PPT」，大脑会先沉浸读源码，然后顺手开干。**看完仓库内容后必须回到 dispatch 流程**。解决方案：
> 1. 读仓库前先对自己说一遍：「这里面有 PPT 需求」
> 2. 读完仓库后，强制思维清零：「现在要 dispatch，不是直接开工」
> 3. 加载本 skill，展示三选项
>
> **违反此规则的代价**：用户需要额外发消息纠正你（如「用PPTmaster」「你没有问我是否用PPTmaster」），浪费至少一次对话轮次。继续违反会使用户失去耐心。

## 触发条件

用户提到：生成PPT、做PPT、写PPT、制作演示文稿、slides、deck、演示、课件、汇报PPT、分享slides 等。

## 三个备选方案

| # | 方案 | 产出格式 | 适用场景 | 速度 |
|---|------|---------|---------|------|
| 1 | **PPT Master** | 原生可编辑 .pptx (DrawingML) | 正式汇报、客户交付、需要高质量排版 | 慢（多步管线，需用户确认） |
| 2 | **guizang-ppt-skill** | 网页版横向翻页 HTML | 快速分享、行业分享、杂志风/瑞士风 | 快 |
| 3 | **pptxgenjs (powerpoint skill)** | .pptx 文件 | 简单结构、快速导出 | 中 |

## 调度规则

### 必须遵守

- **PPT Master 始终作为选项 1 列出**，不得跳过。
- 用户说"随便"/"都行"/"1"/"2"/"3" 时直接执行对应方案。
- 用户说"快一点"或"随便来一个" → 推荐 guizang-ppt-skill。

### 推荐逻辑

根据场景给建议：

| 用户场景 | 推荐 |
|---------|------|
| 正式汇报、客户交付、学术、对外分享 | PPT Master |
| 快速预览、内部分享、个人使用 | guizang-ppt-skill |
| 简单结构、有现成模板 | pptxgenjs |
| 行业分享、杂志感、网站嵌入 | guizang-ppt-skill |

### 展示给用户的格式

```
用哪个方案？

1. PPT Master    → 原生可编辑 .pptx，高质量，适合正式场合
2. 杂志风网页 PPT → 横向翻页 HTML，秒出，适合快速分享
3. pptxgenjs     → 简单 .pptx，快速生成，适合简单结构

推荐：方案X（原因）
```

### 选中后

- **方案 1 (PPT Master)**：路径 `/home/ubuntu/ppt-master-run/ppt-master/skills/ppt-master/SKILL.md`，项目根目录 `/home/ubuntu/ppt-master-run/ppt-master/`。执行前先确认 venv 就绪：`ls .venv/bin/python3 && .venv/bin/pip install -r skills/ppt-master/requirements.txt`。严格按其管线执行（源材料 → 项目初始化 → 策划 8 确认 → 执行 SVG → 后处理 → 导出 PPTX）。SKILL.md 中 `${SKILL_DIR}` 指 `skills/ppt-master`。

  > **源材料是 GitHub 仓库时的处理**: 若用户让"做一个关于这个仓库的PPT"，源材料不是单个文件或URL。此时进入 Step 1 前，先在本地仓库目录执行 `ls` + `cat README.md` + 按需读取关键文件获取内容，然后写一份综合 Markdown（项目简介 + 文件结构 + 技术架构 + 部署方式），再用 `import-sources --move` 导入这个 .md 文件。不要尝试把整个仓库的文件逐页引入。
- **方案 2 (guizang-ppt-skill)**：加载 `guizang-ppt-skill` skill，按 7 问澄清后生成 HTML。
- **方案 3 (pptxgenjs)**：加载 `powerpoint` skill，用 pptxgenjs 生成。

## 用户直接指名时的处理

当用户直接说"用PPTmaster"、"用方案1"、"用pptmaster"、"用guizang" 等明确指向三个方案之一的短语时，**跳过 3 选项展示，直接执行对应方案**。但仍然在确认消息中简短列出另外两个方案作为备选。

```markdown
收到，用 PPT Master 管线做。
备选：guizang（网页 PPT 快出）/ pptxgenjs（简单 .pptx），如需切换随时说。
```

## 源材料为 GitHub 仓库时的完整步骤

当用户说"做一个关于这个仓库的PPT"且仓库代码已在本地（如 agent 仓库）：

1. 先读取仓库关键文件：README.md + 项目文件结构 + 关键源码
2. 写一份综合 Markdown（项目简介 + 文件结构 + 技术架构 + 部署方式）
3. **必须先过本调度器展示三选项**，不得越过 dispatch 直接开干
4. 用户选择方案后：
   - **PPT Master**：init → import-sources --move <markdown> → 单独复制 demo-images/screenshots 到 `images/` 目录 → analyze_images → 继续管线
   - **guizang**: 直接按模板生成 HTML
   - **pptxgenjs**: 直接在 repo 目录写 JS 脚本

## 🚨 反模式（强制执行）

> 以下是本 session 中真实发生的错误，已编码为规则，**任何一次违反都构成执行失败**。

1. **❌ 跳过调度器直接产 PPT** — 用户说"做 PPT"时，不得自己直接拿 pptxgenjs / guizang-ppt-skill / python-pptx 开干。必须经由本调度器展示三个选项，用户选择后再执行对应的 skill。
2. **❌ 跳过选择直接默认** — 不得默认使用任何一个方案。即使觉得"这个题目适合xxx"，也必须展示三个选项让用户选。
3. **❌ 造坑不填** — 先出选项让用户确认，再干活。不要先做了再问"你看行不行"。
4. **❌ 用户纠正后才加载调度器** — 用户说"用PPTmaster"意味着你之前的方案选错了。第一次请求时就该加载本 skill。事后补丁性质的 dispatch 仍然是违规。
5. **❌ 源材料已读完但跳过 dispatch** —"已经读了仓库了解了内容"不是跳过 dispatch 的理由。阅读源材料是 Step 1，dispatch 是选工具，两个步骤独立。
6. **❌ 仓库 + PPT 组合不清零** — 当用户同时说"看仓库"+"做个PPT"时，容易先沉浸读源码，然后顺手用 pptxgenjs 开干。**看完仓库内容后，必须回到 dispatch 流程展示三选项，不得跳过。**

### Venv 路径

PPT Master 的 venv 在项目根目录 (`/home/ubuntu/ppt-master-run/ppt-master/.venv`)，所有脚本通过 `.venv/bin/python3` 运行。

### tabler-filled 图标命名坑

tabler-filled 库部分常见图标名称与实际不一致（如 `server`/`robot` 不存在，需用 `cloud-computing`/`sparkles`）。参见 `references/tabler-filled-icons.md`。执行 SVG 生成前务必 `ls | grep` 确认图标名存在。

### PPT Master 图片路径坑

SVG 中 `<image href="images/xxx.png">` 的路径解析相对于 `svg_output/`，图片需复制到 `svg_output/images/` 才能通过质检和导出。参见 `references/ppt-master-image-path-pitfall.md`。

### PPT Master SVG XML 标签坑

PPT Master 使用严格 XML 解析器 (`xml.etree.ElementTree`)，SVG 中混入 `<span>`、`<b>` 等 HTML 标签或未正确闭合的 `<tspan>` 会导致 `mismatched tag` 错误，导出失败。

**安全写法**：代码块用独立 `<text>` 元素（每行一个），避免复杂嵌套的 `<tspan>` 颜色高亮语法。参见 `references/ppt-master-svg-xml-pitfalls.md`。
