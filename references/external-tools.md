# 外部工具清单

这些工具需要在目标机器上额外安装，不属于 Hermes Agent 核心。

## CloakBrowser (浏览器后端)
- **用途**: 替代 Camofox，提供更底层（C++ 级别）的反检测浏览器
- **安装**: `pip install cloakbrowser`
- **启动**: `python3 ~/.hermes/scripts/cloakbrowser-server.py`
- **端口**: 9377 (Camofox 兼容 API)
- **健康检查**: `curl http://localhost:9377/health`

## OpenCode CLI (代码执行器)
- **用途**: 执行 coding 类任务的 AI 编程助手
- **安装**: 
  ```bash
  npm install -g @opencode-ai/cli
  ```
- **版本**: 1.15.5
- **配置**: 需要 DEEPSEEK_API_KEY 环境变量
- **调用**: `opencode --acp --stdio`

## Claude Code CLI (备用代码执行器)
- **用途**: Anthropic 的代码执行器，作为 OpenCode 的备选
- **版本**: 2.1.145
- **安装**: `npm install -g @anthropic-ai/claude-code`

## Task Pulse (任务管理面板)
- **用途**: 可视化任务管理，dashboard + 实时详情
- **位置**: `/home/ubuntu/task-pulse/`
- **启动**: 
  ```bash
  cd ~/task-pulse
  npx next build
  npx next start -p 3000
  ```
- **域名**: https://pulse.zaiyemeiyou.com (Caddy 反向代理)

## n8n (工作流引擎)
- **用途**: 自动化工作流，Hermes 通过 webhook 与 n8n 联动
- **地址**: https://flow.zaiyemeiyou.com
- **集成**: Hermes → n8n webhook → 任务执行 → 回调更新

## PPT Master
- 详见 `references/ppt-master.md`

## Open Design
- **用途**: UI 设计生成工具
- **安装**: Docker
- **地址**: https://design.zaiyemeiyou.com
