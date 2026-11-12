---
name: compose-snapshot
description: Build Jetpack Compose screens into a throwaway host app, run them on a connected Android phone or tablet, and capture light, dark, landscape and large-font screenshots to check layout, spacing, large-screen adaptation and dark mode. Use after writing or changing any Compose UI when an adb device is connected. 中文触发词包括“Compose 截图”“真机预览”“安卓界面效果”“平板适配检查”“视觉自检”。
---

# Compose 真机截图自检

写完或修改 Compose 界面后，用本技能把代码装进临时宿主 App，在已连接的设备上截图，**亲自查看图片**，发现问题就改代码再截。

## 前提

- `adb devices` 里有在线设备。没有设备就跳过本技能，在总结的「验证」里写明「未在设备上验证」。
- 多台设备在线时，先问用户用哪台，再把序列号作为第 5 个参数传入，不要猜。
- 用户说「不要编译」时不使用本技能。

## 用法

```bash
~/.gemini/config/skills/compose-snapshot/scripts/snapshot.sh <源码目录> <根Composable名> <输出前缀> [模式=light,dark] [设备序列号]
# 手机/平板常规检查：
~/.gemini/config/skills/compose-snapshot/scripts/snapshot.sh . SettingsRoute /tmp/snap/settings light,dark
# 平板再加横屏和大字体：
~/.gemini/config/skills/compose-snapshot/scripts/snapshot.sh . SettingsRoute /tmp/snap/settings light,dark,landscape,font
```

- 模式：`light`、`dark`、`landscape`（横屏浅色）、`font`（1.3 倍字体浅色）。设备是平板（最短边 ≥ 600dp）时必须包含 `landscape`。
- 根 Composable 必须能**无参调用**，例如 `SettingsRoute()`（ViewModel 用 `viewModel()` 默认参数并内置示例数据）。需要特定状态（空列表、错误、长文本）时，在 `/tmp` 下新建临时目录，复制源码并加一个无参包装函数再截图；不要把包装函数留在用户代码里。
- 宿主已提供：Compose BOM、Material 3（含 adaptive、window-size-class、icons-extended）、activity-compose、lifecycle、navigation-compose、coroutines。**不支持** Hilt、Room、Coil 等其他库；用到它们的界面要写一个不依赖它们的无参预览入口来截图。
- 代码里的 `res/` 目录会一并打包，`stringResource` 需要的 `strings.xml` 必须存在。
- 输出每个模式一张 PNG 路径，最后一行 `OK`。`BUILD FAILED` 先修编译错误；`CRASHED` 会附带崩溃栈。
- 截图放在 `/tmp` 等工作区外的目录，不要提交进仓库。

## 设备安全（必须遵守）

- 脚本只安装/更新自己的测试包 `agy.snapshot.host`（截图后保留在设备上，后续以覆盖更新安装，避免部分机型反复弹安装确认），深色和横屏只作用于这个测试 App，不改设备设置，可以直接运行。不要卸载它。
- **只通过本脚本操作设备。** 截图期间禁止自己执行 `adb install`、`am start`、`input`（tap/swipe/text/keyevent）、`uiautomator`、`screencap`、`logcat -c`、往设备写文件等命令。
- 脚本输出 `INSTALL BLOCKED`（设备弹出安装确认，或系统拒绝来自电脑的安装）或「锁屏」时：**立即停止使用本技能**，在总结里写明「设备拦截了安装，未在设备上验证」，请用户在设备上处理。**绝不替用户点击任何系统弹窗**，不重试。
- 输出 `BUSY` 说明设备正被其他截图任务占用，可稍后重试一次，仍失败就跳过。

## 迭代上限（重要）

- **最多 3 轮**「截图 → 看图 → 修改」。第 3 轮后仍有问题就停下，在总结里列出。
- 只修你自己代码造成的问题，不要研究或修改截图工具本身。

## 看图检查清单

1. **大屏适配**：平板横屏下单列内容不能拉满整屏宽——设置/表单类内容限制最大宽度并居中，列表-详情类改成双栏。
2. **截断与溢出**：文字截断、按钮挤压、内容被状态栏/导航栏遮挡（edge-to-edge 的 insets）。
3. **对齐与间距**：同类元素左边缘对齐、间距一致、触控区域足够大。
4. **层级**：标题、主要内容、主要操作一眼可辨；没有多余装饰色块、阴影。
5. **深色模式**：颜色全部来自 `MaterialTheme.colorScheme`，没有刺眼的白块或看不清的文字。
6. **大字体**：1.3 倍字体下没有重叠、截断成不可读。
7. **文案**：没有技术术语，语言一致。

## 已知局限

- 宿主会用设备的动态取色包裹根 Composable；代码自带主题时以代码为准。
- 截图包含系统状态栏和导航条，它们的样式不代表你的代码问题。
