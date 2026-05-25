# PPT Master — 暗色科技风 PPT 生成

## 位置
`/home/ubuntu/ppt-master-run/ppt-master/` — 独立项目，非 Hermes 内置。

## 使用方式
通过 Hermes 的 `ppt-master` skill 调用，工作流：

1. **策略师 (Strategist)**：分析源文档，确定 8 个确认点（主题、受众、页数、风格等）
2. **图片生成 (Image Generator)**：AI 生成配图
3. **执行器 (Executor)**：生成 SVG 幻灯片 → 合成 PPTX

## 核心命令
```bash
# 初始化项目
cd ~/ppt-master-run/ppt-master
python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169

# 生成 PPT
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

## 风格
- 暗色科技风（Dark Tech）
- 偏好的 canvas 格式：ppt169 (16:9)
- 输出格式：原生 .pptx（非图片式，文字可编辑）

## 迁移说明
在目标机器上需要：
```bash
git clone <ppt-master-repo> ~/ppt-master-run/ppt-master
cd ~/ppt-master-run/ppt-master
pip install -r requirements.txt
```
