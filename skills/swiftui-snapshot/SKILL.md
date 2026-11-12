---
name: swiftui-snapshot
description: Render a SwiftUI view to light and dark PNG screenshots without an Xcode project, then look at them to check layout, spacing, truncation, empty values and dark mode. Use after writing or changing any macOS SwiftUI UI. 中文触发词包括“SwiftUI 截图”“渲染预览”“看看界面效果”“视觉自检”。
---

# SwiftUI 截图自检

写完或修改 macOS SwiftUI 界面后，用本技能渲染浅色/深色两张截图，**亲自查看图片**，发现问题就改代码再渲染。

## 用法

```bash
~/.gemini/config/skills/swiftui-snapshot/scripts/snapshot.sh <源码目录> <根视图类型名> <宽> <高> <输出前缀> [最低macOS版本=14.0] [window|panel]
# 普通窗口（含标题栏、工具栏）：
~/.gemini/config/skills/swiftui-snapshot/scripts/snapshot.sh . DiskAnalyzerView 1000 640 /tmp/snap/main 14.0
# 菜单栏面板 / 弹出框（无边框）：
~/.gemini/config/skills/swiftui-snapshot/scripts/snapshot.sh . ClipboardPanelView 360 520 /tmp/snap/panel 14.0 panel
```

- 根视图必须能用 `RootView()` 无参初始化。
- 要检查其他状态（空列表、长文本、错误态），在 `/tmp` 下新建临时目录，复制源码并加一个包装视图，如 `struct SnapEmpty: View { var body: some View { ClipboardPanelView(items: []) } }`，再渲染 `SnapEmpty`。不要把包装视图留在用户代码里。
- 输出 `OK` 和两个 PNG 路径后，读取这两张图查看。输出 `BUILD FAILED` 时先修编译错误（脚本按最低系统版本 + Swift 6 编译）。
- 截图放在 `/tmp` 等工作区外的目录，不要提交进仓库。

## 迭代上限（重要）

- **最多 3 轮**「渲染 → 看图 → 修改」。第 3 轮后仍有问题就停下，在总结里列出剩余问题，不要无限打磨。
- 只修**你自己代码**造成的问题。不要为了研究截图工具本身的行为去写实验视图、测试工程或调试脚本。

## 看图检查清单

1. **截断与溢出**：文字意外截断、表格列被挤出视图、内容超出窗口。
2. **空值与占位**：空白徽标、显示成空胶囊的 `0`/空字符串、缺失图标。
3. **对齐与间距**：同类元素左边缘对齐、间距一致、数字列右对齐。
4. **层级**：标题、主要内容、主要操作一眼可辨；没有多余装饰色块、渐变、阴影。
5. **深色模式**：没有刺眼的白块、看不清的文字、硬编码颜色。
6. **文案**：界面上没有 API 名或技术术语，语言一致。
7. **字号**：文字用系统文本样式；`grep -rn 'system(size:' --include=*.swift .` 命中的文字（非装饰图标）都要改掉。

## 已知局限（不是你的代码问题，不要为此改代码或做实验）

- 窗口不是焦点窗口：`.borderedProminent` 主按钮、列表选中色可能显示为灰色。
- 显示器休眠时脚本会输出 `NOTE: 显示器休眠…`，此时毛玻璃显示为纯色、侧边栏/检查器的系统文字可能偏暗、**侧边栏选中行显示为一整块黑色**、主按钮发灰，这些都不用修。但侧边栏、检查器、工具栏的**布局**仍然可信：缺失的元素、错位、溢出、未选中行里看不见的文字是真实问题，要修。
- 截图尺寸应不小于视图声明的最小尺寸（`.frame(minWidth:minHeight:)`），否则内容会被裁切。
- 相对时间、日期格式按本机语言区域显示，可能与界面文案语言不同。
