用户是西电 XDSEC CTF 选手，沟通极度简洁（单字短语"改""1"白屏"不行"），意思是不用问直接干。一个词反馈表示"这条路不通，换全新的策略"，不要建议重试或解释原因。技术追问深至代码级+数学直觉+类比，要求展示证据链（JS源码、Network、反编译）。学习方式：必须看到完整链路（F12 → 找JS → 抠后16字节 → Python实现），抽象描述不够。CTF 工作流偏好：批量 writeup 归入现有技能，不建逐题技能。动手实操型——说"打开Sources"会截图确认位置，需要引导到具体文件/行。
§
User prefers configuration/help responses to include complete directly copyable commands, not abstract editing instructions.
§
用户计划在番茄小说写长篇科幻，当前明确方向为多文明太空歌剧《帝国边疆》：不要黑暗森林，强调帝国/联邦/外星文明等不同制度文化、人类与外星谱系起源、殖民开拓、外交交流、等级森严的人类帝国、主角长期晋升路线，以及战舰/武器/星球体系细节。项目仍在 ~/novel/。
§
任务规则：分大小。秒级小改动直接改不建 task；新功能/多文件改动/重构必须先建 task。关键节点必须有 task。我主动决定分组归类（小任务归已有大任务，新功能开新大任务），不询问用户。测试任务用完即删。
§
User wants task-execution workflows to expose a server-hosted real-time status view and proactive delivery to their computer/WeChat, not just chat summaries.
§
GitHub workflow: 所有改动只推送到 feature 分支，永不直接推 main。由用户自己合并到 main。
§
User is affiliated with Xidian University (西安电子科技大学) — agent repo has Xidian IDS+Ehall course schedule scraper.
§
Task Pulse 偏好：做了啥事就要建对应任务记录，不同工作流不能混淆；同类任务必须并到同一个 groupId。文件处理：用户给的链接/URL 参数不能删减，只能增加。代码偏好：简洁直接，能写 main 就不包装函数，边界情况可少处理。服务器管理：统一 Cloudflare Proxied + Caddy `tls internal` + SSL/TLS Full。用户说“给 Hermes 备份”时，指备份到云端 Hermes 主机本地，而不是推 GitHub。
§
Core rule: 大任务不能拆成更多大任务，只修小任务分类不拆分组。cron 任务整理只能修正 category（ppt/coding/chat）和 groupId 一致性，不能拆分或重命名大任务分组。