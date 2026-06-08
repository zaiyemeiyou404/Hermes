# PPT Master SVG XML 标签陷阱

## 问题

在 SVG 中使用复杂嵌套的 `<tspan>` 高亮配色语法时，PPT Master 的 XML 解析器 (`xml.etree.ElementTree`) 会因标签不匹配而报错：

```
xml.etree.ElementTree.ParseError: mismatched tag: line N, column M
```

## 根因

SVG 代码块中的 `<tspan>` 嵌套颜色标记虽然浏览器能渲染，但 PPT Master 的 `drawingml_converter.py` 使用严格 XML 解析器。以下两种情况最容易出错：

### 1. 非 SVG 标签混入

```svg
<!-- ❌ 错误：<span> 不是 SVG 标签 -->
<text>
  <tspan>for i in </tspan><span>range</span><tspan>(n):</tspan>
</text>

<!-- ✅ 正确：合并为纯文本 -->  
<text>
  <tspan>for i in range(n):</tspan>
</text>
```

`<span>`、`<b>`、`<i>`、`<br>` 等 HTML 标签在 SVG 中无效，必须用 `<tspan>`。

### 2. 嵌套 `<tspan>` 边界错误

多颜色高亮的嵌套 `<tspan>` 容易出错。PPT Master 的 flatten 阶段会把 `dy` 属性的 `<tspan>` 展开为独立 `<text>`，但如果有未闭合的标签或错配的标签，XML 解析直接失败。

## 最佳实践

### 代码块推荐写法：独立 `<text>` 元素

```svg
<!-- 代码块背景 -->
<rect x="55" y="200" width="600" height="300" rx="8" fill="#0A0A14" stroke="#2A3A5E"/>

<!-- 每行代码用独立 <text> -->
<text x="75" y="230" font-family="Consolas, Courier New, monospace" font-size="13" fill="#00D4AA">  class HiddenInputParser(HTMLParser):</text>
<text x="75" y="255" font-family="Consolas, Courier New, monospace" font-size="13" fill="#D0D8F0">      def __init__(self):</text>
<text x="75" y="280" font-family="Consolas, Courier New, monospace" font-size="13" fill="#D0D8F0">          super().__init__()</text>
```

每行独立 `<text>` 的间距通过 `y` 值等差递增（如 230 → 255 → 280，间隔 25px），避免 `<tspan dy>` 的复杂依赖。

### 高亮时的安全做法：纯色代码块

代码用单色，靠背景色块区分不同区域，比逐词高亮更可靠：

```
# 代码区域用 #0A0A14 深色背景 
# 注释区域用提示卡片分开（不同背景色 + 侧边 accent bar）
# 公式用独立卡片 + 浅色背景
```

### 如果需要高亮

用 `<text>` 分段 + 错开 `x` 坐标实现（但排列脆弱，不推荐用于长段代码）。

### 验证清单

生成 SVG 后先检查：

- [ ] 无 `<span>`、`<b>`、`<i>` 等 HTML 标签
- [ ] 所有 `<tspan>` 正确开闭
- [ ] `&lt;` 代替 `<`，`&gt;` 代替 `>`，`&amp;` 代替 `&`
- [ ] 没有 `</sp` 之类的截断标签

### 快速验证 XML 合法性

在 `svg_to_pptx.py` 前运行：

```bash
python3 -c "
import xml.etree.ElementTree as ET, glob
for f in sorted(glob.glob('svg_output/*.svg')):
    try:
        ET.parse(f)
        print(f'OK: {f.split(\"/\")[-1]}')
    except Exception as e:
        print(f'FAIL: {f.split(\"/\")[-1]} - {e}')
"
```
