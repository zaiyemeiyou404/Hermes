# PPT Master 图片路径陷阱

## 问题

PPT Master 的 `svg_quality_checker.py` 和 `svg_to_pptx.py` 在解析 `<image href="images/xxx.png">` 时，默认相对于 `svg_output/` 目录查找图片。如果图片只放在项目根目录的 `images/` 下而不复制到 `svg_output/images/`，质检会报 "Image file not found" 错误且导出 PPTX 时图片缺失。

## 根因

SVG 文件中的 `<image href="images/...">` 路径是**相对路径**。当 `finalize_svg.py` 和 `svg_to_pptx.py` 处理 SVG 时，它们的工作目录解析在 `svg_output/` 下，所以 `images/` 需要存在于 `svg_output/images/`。

## 修复方法

```bash
cd <project_path>
mkdir -p svg_output/images
cp images/*.png svg_output/images/
cp images/*.jpg svg_output/images/
```

在 `finalize_svg.py` 之后、`svg_to_pptx.py` 之前执行即可。

## spec_lock.md 通用颜色遗漏

`spec_lock_reference.md` 模板只包含业务色。以下**显示用颜色**容易遗漏导致质检告警，建议创建时就加入：

```yaml
## colors
- white: #FFFFFF      # 白色文本
- black: #000000      # 视频播放器等深色区域
- purple: #8B5CF6     # 模块划分辅助色（可选）
- video_bg: #0A0A14   # 视频播放器深色背景（可选）
```

## 流程检查清单

PPT Master 全流程中易漏步骤：

- [ ] `import-sources --move` 导入源材料后，**单独复制 demo-images/screenshots** 到 `images/`
- [ ] SVG 中使用 `<image href="images/xxx.png">` 后，把图片也复制到 `svg_output/images/`
- [ ] `spec_lock.md` 中把所有 SVG 中实际使用的颜色都声明，包括 white/black
- [ ] `finalize_svg.py` → `svg_to_pptx.py` 连续执行，中间不中断
- [ ] 导出后在 `exports/` 下确认 `xxx.pptx` 文件存在且大小合理
