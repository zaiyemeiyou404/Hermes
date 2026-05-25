User prefers repository-level skill updates when asked to save reusable methods, rather than local-only skills.
§
User has a self-hosted n8n instance at https://flow.zaiyemeiyou.com and wants Hermes involved in task triage before Codex execution.
§
User is using Windows on their local machine for Codex-related workflows.
§
OpenCode CLI is installed on the cloud Hermes host at /home/ubuntu/.hermes/node/bin/opencode (version 1.15.5). OpenCode detects DeepSeek auth via the DEEPSEEK_API_KEY environment variable.
§
For cloud coding-agent workflows, user prefers DeepSeek as the default model source and GPT/OpenAI only when necessary.
§
Claude Code CLI is installed on the cloud Hermes host and reports version 2.1.145.
§
写代码类的任务交给 OpenCode 执行，Hermes 不用亲自逐文件编辑。coding 分类的任务应该通过 OpenCode runner 来跑。
§
In the task-pulse project, task detail pages should expose any generated artifacts or accessible links as direct, jumpable actions rather than plain text.
§
Open Design (nexu-io/open-design) installed via Docker at /home/ubuntu/open-design, running on port 7456, accessible at https://design.zaiyemeiyou.com (Caddy reverse proxy). Uses BYOK mode with DeepSeek API (OpenAI protocol). CodeGraph also installed and initialized in task-pulse and agent repos.
§
CloakBrowser v0.3.30 replaced Camofox as browser backend. REST API at ~/.hermes/scripts/cloakbrowser-server.py:9377, Camofox-compatible. Stealth Chromium with 58 C++ patches (navigator.webdriver=false). WeChat mp.weixin.qq.com still shows "环境异常" — IP geolocation issue on Singapore VPS.
§
在 task-pulse 中：①所有操作必须创建对应任务记录，归入正确大任务组（如 task-pulse 相关归 "task-Pluse 完善"），组名准确；②大任务标题必须写清楚明白；③PPT/产出类任务应作为子任务挂在主任务分组下，不独立建组。
§
Session 2026-05-25: User wanted OpenCode work on https://github.com/zaiyemeiyou404/agent (improve repo, switch branch) but was deferred — needs follow-up.
§
GitHub PAT (fine-grained) for zaiyemeiyou404 saved in ~/.bashrc as GITHUB_TOKEN. Use Bearer auth for API calls. Repos: task-Pluse, Hermes (https://github.com/zaiyemeiyou404/Hermes)