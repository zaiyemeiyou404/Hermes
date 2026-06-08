# Hermes Agent — Full Recovery Backup

除密钥/令牌外，本仓库可完整恢复 Hermes 记忆、skills、persona、scripts、Task Pulse 运行时数据，并可自动拉取 Task Pulse 项目代码到 `~/task-pulse`。

## 目录结构

```
Hermes/
├── README.md                   # 本文件
├── setup.sh                    # 一键恢复脚本
├── backup/
│   ├── memories/               # 记忆文件（你是谁，我是谁）
│   │   ├── MEMORY.md           # 环境/项目/工具笔记
│   │   └── USER.md             # 用户画像（偏好、沟通风格）
│   ├── skills/                 # 当前活跃 skills 全量备份（已排除缓存/归档）
│   ├── scripts/                # 自定义脚本
│   │   ├── cloakbrowser-server.py   # CloakBrowser 服务端
│   │   └── task-pulse-cleanup.py    # Task Pulse 每日清理
│   ├── persona/
│   │   └── AGENTS.md           # Agent 人设/开发指南
│   └── task-pulse-data/        # Task Pulse 运行时数据快照
├── config/
│   └── config.yaml.example     # 配置模板（敏感信息已脱敏）
└── references/
    ├── ppt-master.md           # PPT Master 技能说明
    ├── task-pulse.md           # Task Pulse 项目配置
    └── external-tools.md       # 外部工具清单
```

## 一键恢复（推荐）

```bash
# 1. 安装 Hermes Agent（如未安装）
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | sh

# 2. 克隆本仓库（可克隆到任意路径）
git clone https://github.com/zaiyemeiyou404/Hermes.git

# 3. 执行一键恢复脚本
cd Hermes && bash setup.sh

# 4. 配置 API 密钥（复制模板后编辑）
cp config/config.yaml.example ~/.hermes/config.yaml
# 编辑 ~/.hermes/config.yaml 填入真实密钥

# 5. 重启 Hermes
hermes gateway restart
```

`setup.sh` 会自动完成：
- 恢复记忆、skills、persona、自定义脚本
- 克隆/更新 Task Pulse 项目代码到 `~/task-pulse`
- 恢复 Task Pulse 运行时数据快照
- 如有 npm，自动执行 `npm install`

## 分步手动恢复（可选）

```bash
git clone https://github.com/zaiyemeiyou404/Hermes.git
cd Hermes
cp backup/memories/* ~/.hermes/memories/
cp -r backup/skills/* ~/.hermes/skills/
cp backup/persona/AGENTS.md ~/.hermes/hermes-agent/AGENTS.md
cp backup/scripts/* ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.py
cp config/config.yaml.example ~/.hermes/config.yaml
# 编辑 ~/.hermes/config.yaml 填入密钥
git clone https://github.com/zaiyemeiyou404/task-Pluse.git ~/task-pulse
cp -r backup/task-pulse-data ~/task-pulse/.task-pulse-data
hermes gateway restart
```

## Task Pulse 启动

```bash
cd ~/task-pulse
npx next build
npx next start -p 3000
```

## 环境变量

```bash
# 添加到 ~/.bashrc
export GITHUB_TOKEN="your_github_pat"
export DEEPSEEK_API_KEY="your_deepseek_key"
```

## 注意事项

- **不要提交敏感信息**：`.env`、`auth.json`、`config.yaml`（含真实 token）不在备份范围内
- `backup/skills/` 是当前服务器 **活跃 skills 集合** 的镜像备份；缓存、归档、hub 索引等已排除
- `config/config.yaml.example` 由当前服务器 `~/.hermes/config.yaml` 脱敏导出，保留行为配置但不保留密钥
- 每次修改技能或记忆后，记得进入仓库目录执行 `git commit -am "update" && git push`
- 本仓库不包含 secrets —— 需手动填入 API Key（见 config.yaml.example 模板）
