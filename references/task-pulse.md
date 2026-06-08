# Task Pulse — 任务管理面板

## 位置
`/home/ubuntu/task-pulse/` — 独立 Next.js 项目

## GitHub
[https://github.com/zaiyemeiyou404/task-Pluse](https://github.com/zaiyemeiyou404/task-Pluse)

## 功能
- 可视化任务 dashboard，按大任务分组展示
- 任务详情页：实时 SSE 流更新、事件日志、执行日志
- 任务启动器：支持 Hermes/OpenCode runner
- 分类标签：📊生成PPT、💻写代码、💬聊天、📄论文
- 审核流程：阻塞等待、命令同意、停止/重试

## 启动方式
```bash
cd ~/task-pulse
npx next build          # 编译
npx next start -p 3000  # 启动（生产模式）
```

或从 GitHub 克隆：
```bash
git clone https://github.com/zaiyemeiyou404/task-Pluse.git ~/task-pulse
cd ~/task-pulse && npx next build && npx next start -p 3000
```

## 数据目录
`.task-pulse-data/` — 每个任务一个 JSON 文件，文件即数据库。

## 备份与恢复
运行时数据快照已纳入 Hermes 备份仓库 `~/Hermes/backup/task-pulse-data/`。

- **备份**: 运行 `cp -r ~/task-pulse/.task-pulse-data ~/Hermes/backup/task-pulse-data`
- **恢复**: `setup.sh` 自动将快照恢复到 `~/task-pulse/.task-pulse-data`

## 部署域名
https://pulse.zaiyemeiyou.com (Caddy 反向代理 → localhost:3000)

## 环境变量
```bash
export GITHUB_TOKEN="your_token"  # 用于推送分支
```

## 使用约定
- 所有操作先在 task-pulse 创建任务记录
- 任务必须归入正确的大任务分组
- Big/main tasks 标题写清楚明白
