# PPT Master — 暗色科技风 PPT 生成

## 来源
GitHub: https://github.com/hugohe3/ppt-master.git

## 安装
```bash
git clone https://github.com/hugohe3/ppt-master.git ~/ppt-master-run/ppt-master
cd ~/ppt-master-run/ppt-master
pip install -r requirements.txt
```

## 本地位置
`/home/ubuntu/ppt-master-run/ppt-master/` — 独立的 git 仓库（~1.6G，含所有模板和示例）

## 使用方式
通过 Hermes 的 `ppt-master` skill 调用。工作流：

1. **strategist** → 8 个确认点（主题、受众、页数、风格等）
2. **image_generator** → AI 生成配图
3. **executor** → SVG 幻灯片 → PPTX 导出

## 核心命令
```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

## 已有项目产出
| 项目 | 位置 |
|------|------|
| task-pulse 介绍 PPT | `projects/task-pulse-intro_ppt169_20260525/exports/` |
| Hermes 架构图 PPT | `projects/hermes-architecture_ppt169_20260520/exports/` |
| 烟雾弹演示 | `projects/smoke_demo_ppt169_20260519/exports/` |

## 风格偏好
- 暗色科技风（Dark Tech）
- 画布格式：ppt169 (16:9)
- 输出：原生 .pptx（文字可编辑，非图片式）
