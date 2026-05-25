# 外部工具清单

这些工具需要在目标机器上额外安装，不属于 Hermes Agent 核心。

## CloakBrowser (浏览器后端)
- **用途**: 替代 Camofox，提供更底层（C++ 级别）的反检测浏览器
- **安装**: 
  ```bash
  pip install cloakbrowser
  # 首次运行会自动下载 Chromium 引擎（~680MB 缓存）
  ```
- **启动**: `python3 ~/.hermes/scripts/cloakbrowser-server.py`
- **端口**: 9377 (Camofox 兼容 REST API)
- **健康检查**: `curl http://localhost:9377/health`
- **代理**: 通过 `CAMOFOX_URL` 环境变量路由（向后兼容）
- **已备份**: `backup/scripts/cloakbrowser-server.py`

## OpenCode CLI (代码执行器)
- **用途**: 执行 coding 类任务的 AI 编程助手
- **安装**: 
  ```bash
  npm install -g @opencode-ai/cli
  ```
- **版本**: 1.15.5
- **配置**: 需要 `DEEPSEEK_API_KEY` 环境变量
- **二进制**: `/home/ubuntu/.hermes/node/bin/opencode`
- **调用**: `opencode --acp --stdio`

## Claude Code CLI (备用代码执行器)
- **用途**: Anthropic 的代码执行器，作为 OpenCode 的备选
- **版本**: 2.1.145
- **安装**: `npm install -g @anthropic-ai/claude-code`

## Task Pulse (任务管理面板)
- **用途**: 可视化任务管理，dashboard + 实时详情
- **GitHub**: https://github.com/zaiyemeiyou404/task-Pluse
- **部署**: https://pulse.zaiyemeiyou.com
- **启动**: 
  ```bash
  git clone https://github.com/zaiyemeiyou404/task-Pluse.git ~/task-pulse
  cd ~/task-pulse
  npx next build && npx next start -p 3000
  ```
- **环境变量**: `GITHUB_TOKEN` (用于推送分支)
- **数据**: `.task-pulse-data/` — 每个任务一个 JSON 文件
- **配置**: 详见 `references/task-pulse.md`

## n8n (工作流引擎)
- **用途**: 自动化工作流，Hermes 通过 webhook 与 n8n 联动
- **地址**: https://flow.zaiyemeiyou.com
- **自建**: 用户自托管
- **集成**: Hermes → n8n webhook → 任务执行 → 回调更新 task-pulse

## PPT Master (幻灯片生成)
- **来源**: https://github.com/hugohe3/ppt-master
- **本地**: `~/ppt-master-run/ppt-master/` (独立 git repo, ~1.6G)
- **安装**: 
  ```bash
  git clone https://github.com/hugohe3/ppt-master.git ~/ppt-master-run/ppt-master
  cd ~/ppt-master-run/ppt-master && pip install -r requirements.txt
  ```
- **风格**: 暗色科技风, 16:9, 原生 .pptx 输出
- **配置**: 详见 `references/ppt-master.md`

## Open Design (UI 设计生成)
- **用途**: UI 设计生成工具
- **安装**: Docker
- **地址**: https://design.zaiyemeiyou.com
- **配置**: BYOK 模式 (DeepSeek API)
