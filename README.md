# Hermes Agent — Personal Backup

这是我的 Hermes Agent 完整配置备份（含记忆、技能、脚本、人设、外部工具参考）。

> ⚠️ 外部工具（PPT Master、Task Pulse、CloakBrowser 等）是独立项目，本仓库只保存安装说明和引用配置，不包含完整项目文件。

## 目录结构

```
Hermes/
├── README.md                   # 本文件
├── setup.sh                    # 一键迁移脚本
├── backup/
│   ├── memories/               # 记忆文件（你是谁，我是谁）
│   │   ├── MEMORY.md           # 环境/项目/工具笔记
│   │   └── USER.md             # 用户画像（偏好、沟通风格）
│   ├── scripts/                # 自定义脚本
│   │   └── cloakbrowser-server.py  # CloakBrowser 服务端
│   └── persona/
│       └── AGENTS.md           # Agent 人设/人格文件
├── config/
│   └── config.yaml.example     # 配置模板（敏感信息已脱敏）
└── references/
    ├── ppt-master.md           # PPT Master 技能说明
    └── external-tools.md       # 外部工具清单（CloakBrowser, OpenCode 等）
```

## 迁移步骤

### 1. 安装 Hermes Agent

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | sh
```

### 2. 复制配置

```bash
# 克隆本仓库
git clone https://github.com/zaiyemeiyou404/Hermes.git ~/Hermes

# 恢复记忆
cp ~/Hermes/backup/memories/* ~/.hermes/memories/

# 恢复人设
cp ~/Hermes/backup/persona/* ~/.hermes/hermes-agent/agent/persona/

# 恢复浏览器脚本
cp ~/Hermes/backup/scripts/* ~/.hermes/scripts/

# 配置 config.yaml
cp ~/Hermes/config/config.yaml.example ~/.hermes/config.yaml
# 然后编辑 ~/.hermes/config.yaml 填写你的 API Key
```

### 3. 设置环境变量

```bash
# 添加到 ~/.bashrc
export GITHUB_TOKEN="your_github_pat"
export DEEPSEEK_API_KEY="your_deepseek_key"
# ...
```

### 4. 安装 OpenCode CLI

```bash
npm install -g @opencode-ai/cli
```

### 5. 安装 CloakBrowser

```bash
pip install cloakbrowser
```

### 6. 重启 Hermes

```bash
hermes gateway restart
```

## 注意事项

- **不要提交敏感信息**：`.env`、`auth.json`、`config.yaml`（含真实 token）不在备份范围内
- 每次修改技能或记忆后，记得 `cd ~/Hermes && git commit -am "update" && git push`
- 在新机器上执行 `setup.sh` 一键迁移（见下）
