#!/bin/zsh
# Build Compose sources into a host app, run it on a connected Android device, and screenshot it.
# usage: snapshot.sh <src_dir> <RootComposable> <out_prefix> [modes=light,dark] [serial]
#   modes: comma list of light | dark | landscape | font (font = light with 1.3x font scale)
# Output: <out_prefix>-<mode>.png per mode.
# Only installs/updates its own package (agy.snapshot.host); never changes device settings.
set -u
SRC=${1:?src_dir}; ROOT=${2:?RootComposable}; OUT=${3:?out_prefix}
MODES=${4:-light,dark}; SERIAL=${5:-}
SKILL=${0:A:h:h}; PKG=agy.snapshot.host
SDK=${ANDROID_HOME:-$HOME/Library/Android/sdk}
ADB=$SDK/platform-tools/adb
OUT=${OUT:A}; mkdir -p "${OUT:h}"
# Audit trail of device runs.
echo "$(date '+%F %T') ${SRC:A} $ROOT $MODES ${SERIAL:-auto}" >> /tmp/compose-snapshot.log
GRADLE=( $HOME/.gradle/wrapper/dists/gradle-8.13-bin/*/gradle-8.13/bin/gradle(N) )
[[ -x $ADB ]] || { echo "FAILED: 找不到 adb（$ADB）"; exit 1; }
(( ${#GRADLE} )) || GRADLE=( $(command -v gradle) )
[[ -n ${GRADLE[1]:-} ]] || { echo "FAILED: 找不到 Gradle 8.13"; exit 1; }

# Device selection: explicit serial, else exactly one attached device.
if [[ -z $SERIAL ]]; then
  devs=( ${(f)"$($ADB devices | awk 'NR>1 && $2=="device" {print $1}')"} )
  if (( ${#devs} != 1 )); then
    echo "FAILED: 需要指定设备序列号（当前在线设备 ${#devs} 台：${devs[*]:-无}）"; exit 1
  fi
  SERIAL=${devs[1]}
fi
A=( $ADB -s $SERIAL )

# Locate the root composable and use its package as the namespace so `R` resolves.
ROOTFILE=$(grep -rlE "fun[[:space:]]+${ROOT}[[:space:]]*\(" "$SRC" --include='*.kt' 2>/dev/null | grep -v '/build/' | head -1)
[[ -n $ROOTFILE ]] || { echo "FAILED: 在 $SRC 中找不到 fun $ROOT("; exit 1; }
NS=$(sed -nE 's/^package[[:space:]]+([A-Za-z0-9_.]+).*/\1/p' "$ROOTFILE" | head -1)
[[ -n $NS ]] || NS=snapshot.root

W=$(mktemp -d)/host
trap 'rm -rf ${W:h}' EXIT
cp -R $SKILL/template $W
echo "sdk.dir=$SDK" > $W/local.properties
sed -i '' "s/__NAMESPACE__/$NS/" $W/app/build.gradle.kts
CALL=$ROOT'()'; [[ $NS != snapshot.root ]] && CALL="$NS.$ROOT()"
sed -i '' "s/__ROOT_CALL__/$CALL/" $W/app/src/main/java/agy/snapshot/host/SnapshotActivity.kt
J=$W/app/src/main/java/src; mkdir -p $J
find "$SRC" -name '*.kt' -not -path '*/build/*' -not -path '*/.git/*' -not -path '*/test/*' -not -path '*/androidTest/*' -exec cp {} $J/ \;
# Resources: merge every res/ directory found (values, drawable, ...).
find "$SRC" -type d -name res -not -path '*/build/*' -not -path '*/.git/*' | while read r; do
  for sub in $r/*(N/); do mkdir -p $W/app/src/main/res/${sub:t}; cp -R $sub/. $W/app/src/main/res/${sub:t}/; done
done

cd $W
if ! ${GRADLE[1]} -q --console=plain assembleDebug > $W/build.log 2>&1; then
  echo "BUILD FAILED"; grep -E '^e: |error:|What went wrong' -A2 $W/build.log | head -30; exit 1
fi
APK=$W/app/build/outputs/apk/debug/app-debug.apk

# One device, one screen: serialize concurrent runs. Never proceed without the lock.
LOCK=/tmp/compose-snapshot.lock.d
got=0
for i in {1..900}; do
  if mkdir $LOCK 2>/dev/null; then echo $$ > $LOCK/pid; got=1; break; fi
  owner=$(cat $LOCK/pid 2>/dev/null)
  [[ -n $owner ]] && ! kill -0 $owner 2>/dev/null && rm -rf $LOCK
  sleep 1
done
(( got )) || { echo "BUSY: 设备被其他截图任务占用超过 15 分钟，请稍后再试"; exit 1; }
trap '${A[@]} shell am force-stop $PKG >/dev/null 2>&1; rm -rf $LOCK; rm -rf ${W:h}' EXIT INT TERM
if [[ $(${A[@]} shell dumpsys window 2>/dev/null | grep -c 'isKeyguardShowing=true') -gt 0 ]]; then
  echo "FAILED: 设备处于锁屏状态，请用户先解锁。不要尝试用 adb 解锁。"; exit 1
fi
${A[@]} shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
# Some vendor ROMs (e.g. OPlus) show an install confirmation for adb installs. Wait a bounded
# time, then stop and tell the user instead of letting anyone tap through a security prompt.
${A[@]} install -r -t $APK > $W/install.log 2>&1 &
ipid=$!
for i in {1..${COMPOSE_SNAPSHOT_INSTALL_WAIT:-60}}; do kill -0 $ipid 2>/dev/null || break; sleep 1; done
if kill -0 $ipid 2>/dev/null; then
  kill $ipid 2>/dev/null
  echo "INSTALL BLOCKED: 设备上弹出了安装确认（系统安全弹窗）。请停止并请用户在设备上处理，或让用户关闭该机型的 USB 安装确认后再试。禁止用 input tap、uiautomator 等方式代替用户点击。"
  exit 2
fi
if ! wait $ipid; then
  if grep -q 'Failure \[-99\]' $W/install.log; then
    echo "INSTALL BLOCKED: 设备系统拒绝了来自电脑的安装（Failure [-99]，常见于 OPlus 的安装防护）。请停止并请用户在设备上允许 USB 安装后再试，不要绕过。"; exit 2
  fi
  echo "INSTALL FAILED"; tail -3 $W/install.log; exit 1
fi
SINCE=$(${A[@]} shell date '+%m-%d\ %H:%M:%S.000' | tr -d '\r')
for m in ${(s:,:)MODES}; do
  extras=()
  case $m in
    dark) extras=(--ez dark true) ;;
    landscape) extras=(--ez landscape true) ;;
    font) extras=(--ef fontScale 1.3) ;;
  esac
  ${A[@]} shell am start -W -S -n $PKG/.SnapshotActivity ${extras[@]} >/dev/null 2>&1
  sleep 4
  if ! ${A[@]} shell pidof $PKG >/dev/null 2>&1; then
    echo "CRASHED ($m)"; ${A[@]} logcat -d -b crash -T "$SINCE" | grep -E 'Exception|Error|at ' | head -15
    exit 1
  fi
  ${A[@]} exec-out screencap -p > "$OUT-$m.png"
  # Full-resolution tablet captures are large; downscale for faster review.
  sips -Z 1400 "$OUT-$m.png" >/dev/null 2>&1
  echo "$OUT-$m.png"
done
${A[@]} shell am force-stop $PKG >/dev/null 2>&1
# The host stays installed by default (COMPOSE_SNAPSHOT_KEEP=0 removes it) so later runs are updates, which some ROMs
# do not re-confirm.
[[ ${COMPOSE_SNAPSHOT_KEEP:-1} == 1 ]] || ${A[@]} uninstall $PKG >/dev/null 2>&1
echo OK
