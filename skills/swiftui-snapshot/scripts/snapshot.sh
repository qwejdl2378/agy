#!/bin/zsh
# Render a SwiftUI view to light/dark PNGs without an Xcode project.
# usage: snapshot.sh <src_dir> <RootView> <width> <height> <out_prefix> [min_macos=14.0] [window|panel]
#   window (default): real titled window incl. toolbar, sidebar and inspector
#   panel: borderless, for menu bar extras / popovers
# Output: <out_prefix>-light.png, <out_prefix>-dark.png
set -u
SRC=${1:?src_dir}; ROOT=${2:?RootView}; W=${3:?width}; H=${4:?height}; OUT=${5:?out_prefix}
MIN=${6:-14.0}; KIND=${7:-window}
OUT=${OUT:A}; mkdir -p "${OUT:h}"
B=$(mktemp -d)
trap 'rm -rf $B' EXIT
find "$SRC" -name '*.swift' -not -path '*/.build/*' -not -path '*/DerivedData/*' -exec cp {} $B/ \;
# Drop @main so the harness can provide the entry point.
for f in $B/*.swift; do sed -i '' -E 's/^[[:space:]]*@main[[:space:]]*$//; s/^@main //' "$f"; done
if [[ $KIND == panel ]]; then MASK='[.borderless]'; else MASK='[.titled, .closable, .miniaturizable, .resizable]'; fi
cat > $B/main.swift <<X
import SwiftUI
import AppKit
// Report key/main so controls draw in their active appearance without activating the app.
final class SnapshotWindow: NSWindow {
    override var isKeyWindow: Bool { true }
    override var isMainWindow: Bool { true }
    override var canBecomeKey: Bool { true }
}
let a = CommandLine.arguments
let app = NSApplication.shared
app.setActivationPolicy(.accessory)
MainActor.assumeIsolated {
    for dark in [false, true] {
        let w = CGFloat(Double(a[2])!), h = CGFloat(Double(a[3])!)
        let host = NSHostingView(rootView: $ROOT().frame(width: w, height: h))
        let win = SnapshotWindow(contentRect: NSRect(x: -4000, y: -4000, width: w, height: h),
                           styleMask: $MASK, backing: .buffered, defer: false)
        win.appearance = NSAppearance(named: dark ? .darkAqua : .aqua)
        win.contentView = host
        win.orderFrontRegardless()
        RunLoop.main.run(until: Date().addingTimeInterval(1.5))
        // Force a full draw pass so the window server has composited content before capture.
        let warm = host.bitmapImageRepForCachingDisplay(in: host.bounds)!
        host.cacheDisplay(in: host.bounds, to: warm)
        if let frameView = win.contentView?.superview {
            let warmFrame = frameView.bitmapImageRepForCachingDisplay(in: frameView.bounds)!
            frameView.cacheDisplay(in: frameView.bounds, to: warmFrame)
        }
        win.displayIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))
        let url = URL(fileURLWithPath: a[1] + (dark ? "-dark.png" : "-light.png"))
        // Composited window capture includes materials, sidebar and toolbar, but comes back blank
        // while the display is asleep; then fall back to caching the window's frame view.
        var rep: NSBitmapImageRep? = nil
        if let img = CGWindowListCreateImage(.null, .optionIncludingWindow, CGWindowID(win.windowNumber), [.boundsIgnoreFraming]) {
            let r = NSBitmapImageRep(cgImage: img)
            var colors = Set<String>()
            for i in 1...12 { for j in 1...12 {
                if let c = r.colorAt(x: r.pixelsWide * i / 13, y: r.pixelsHigh * j / 13) { colors.insert(c.description) }
            } }
            if colors.count > 2 { rep = r }
        }
        if rep == nil {
            let v: NSView = win.contentView?.superview ?? host
            let r = v.bitmapImageRepForCachingDisplay(in: v.bounds)!
            v.cacheDisplay(in: v.bounds, to: r)
            rep = r
            try? "fallback".write(toFile: a[1] + ".fallback", atomically: true, encoding: .utf8)
        }
        try! rep!.representation(using: .png, properties: [:])!.write(to: url)
        win.close()
    }
}
X
if ! swiftc -swift-version 6 -target arm64-apple-macos$MIN -o $B/app $B/*.swift > $B/build.log 2>&1; then
  echo "BUILD FAILED (macOS $MIN, Swift 6)"; grep 'error:' $B/build.log | grep -v '^ ' | head -20; exit 1
fi
$B/app "$OUT" "$W" "$H" > $B/run.log 2>&1 &
pid=$!
for i in {1..40}; do [[ -f "$OUT-dark.png" ]] && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null
if [[ -f "$OUT-light.png" && -f "$OUT-dark.png" ]]; then
  echo "OK"; echo "$OUT-light.png"; echo "$OUT-dark.png"
  if [[ -f "$OUT.fallback" ]]; then
    rm -f "$OUT.fallback"
    echo "NOTE: 显示器休眠，已降级为视图缓存截图：毛玻璃材质显示为纯色、侧边栏/检查器中的系统文字可能偏暗、侧边栏选中行可能是一整块黑色、.borderedProminent 主按钮可能发灰。这些是截图工具无法还原系统活力效果所致，不是代码问题，不要为此修改代码或编写实验。"
  fi
else
  echo "RENDER FAILED"; tail -20 $B/run.log; exit 1
fi
