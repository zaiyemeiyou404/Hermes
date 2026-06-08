User prefers repository-level skill updates when asked to save reusable methods, rather than local-only skills.
§
OpenCode CLI is installed on the cloud Hermes host at /home/ubuntu/.hermes/node/bin/opencode (version 1.15.5). OpenCode detects DeepSeek auth via the DEEPSEEK_API_KEY environment variable.
§
For cloud coding-agent workflows, user prefers DeepSeek as the default model source and GPT/OpenAI only when necessary.
§
Claude Code CLI is installed on the cloud Hermes host.
§
写代码类的任务交给 OpenCode 执行，Hermes 不用亲自逐文件编辑。coding 分类的任务应该通过 OpenCode runner 来跑。但非 coding 任务（如创作、写小说、策划）直接用 Hermes 自己干，不用开 OpenCode。
§
In the task-pulse project, task detail pages should expose any generated artifacts or accessible links as direct, jumpable actions rather than plain text.
§
Open Design is deployed via Docker at /home/ubuntu/open-design on port 7456, proxied at https://design.zaiyemeiyou.com using DeepSeek BYOK; CodeGraph is initialized in task-pulse and agent repos.
§
每次创建/完成 task-pulse 任务后立即检查：①category 是否正确（PPT→"ppt"、代码→"coding"、聊天→"chat"、设计→"design"）；②groupId 是否与其他同组任务一致（关键：同组任务必须同 groupName+同 repoLink，缺 repoLink 会导致 groupId 不同而分家）；③repoLink 是否填写。不传 category 默认 fallback "coding" 是常见错误。
§
调试/排查类工作，即使未成功也要在 Task Pulse 中创建子任务追踪每轮尝试，不能只在对话里做。每一步调试方向（改方案、调参数、换协议）都应打一个 task，方便复盘。
§
Task Pulse 分组规则：group 由 metadata.groupName+repoLink 自动计算（inferGroupId），改分组应改 metadata.groupName+repoLink 而非直接改 groupId。mock-data.ts 也有硬编码 groupName 需同步。当前规范分组：Agent 仓库完善、Task Pulse 完善、CTF Writeup 分析、Hermes 配置与验证、西电工具书页面部署、日常聊天。
§
task-pulse 任务创建后必须检查分组归类：小任务归到对应分组（如"agent 仓库联调""task-Pluse 完善""Hermes 配置备份"），严禁留空或用"代码开发"等通用名。
§
PPT生成必须先走 ppt-dispatch 调度加载三选一流程（PPT Master / 杂志风网页 PPT / pptxgenjs），不得直接默认使用任何一个工具。用户说"做PPT"时不得跳过调度直接开干——这是被多次纠正仍未解决的高优先级规则。
§
5:00 AM cron "task-pulse 每日整理" 需改用 Hermes agent 模式（非 no_agent）分析任务内容，智能重命名分组名（大任务名称），不只是跑脚本做关键词匹配分类修正。
§
Cloudflare 橙色云（Proxied）+ Caddy: domain block 加 `tls internal`，Cloudflare SSL/TLS 设 "Full" 模式。Homer 用 docker cp 写 config.yml，改了要清浏览器缓存才能看到变化（有 service worker）。
§
For public Task Pulse, user wants a read-only dashboard for security: no Hermes/OpenCode web launchers and no webpage task creation; keep only task/status/log/artifact monitoring.