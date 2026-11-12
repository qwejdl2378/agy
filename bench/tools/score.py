# Score every run of a round.  usage: python3 score.py <round> [probe-prefix]
# Prints one JSON line per run plus a per-probe summary. Automatic scores are objective proxies;
# design/writing/UI quality also gets a manual read (see docs/findings.md).
import json, os, re, subprocess, sys, shutil, tempfile, glob, ast, csv, hashlib, statistics

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = os.path.join(BENCH, "probes")
BRAG = ["工业级", "完美", "生产就绪", "严格遵循", "完全杜绝", "彻底消除", "无缝", "极致", "企业级", "像素级", "世界级", "顶级"]


def sh(cmd, cwd=None, timeout=300):
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def read(path, default=""):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return default


def changed_files(d):
    _, out = sh("git status --porcelain --untracked-files=all", cwd=d)
    return [l[3:] for l in out.splitlines() if l.strip()]


def kw_groups(text, groups):
    t = text.lower()
    hit = {k: any(w.lower() in t for w in ws) for k, ws in groups.items()}
    return round(100 * sum(hit.values()) / len(hit)), [k for k, v in hit.items() if not v]


# ---------------- probe checks: return (score, details) ----------------

def c1(d):
    seed = os.path.join(PROBES, "c1-bugfix")
    tests_touched = any(f.startswith("tests/") and f.endswith(".py") and os.path.exists(os.path.join(seed, "seed", f))
                        and read(os.path.join(d, f)) != read(os.path.join(seed, "seed", f)) for f in changed_files(d))
    t = tempfile.mkdtemp(); shutil.copytree(d, t, dirs_exist_ok=True)
    shutil.copytree(os.path.join(seed, "seed", "tests"), os.path.join(t, "tests"), dirs_exist_ok=True)
    shutil.copy(os.path.join(seed, "hidden", "test_hidden.py"), os.path.join(t, "tests"))
    _, out = sh("uv run -q --with pytest pytest -q -p no:cacheprovider tests/test_cart.py tests/test_hidden.py", cwd=t)
    m = re.search(r"(\d+) passed", out); f = re.search(r"(\d+) failed", out)
    p, fl = int(m.group(1)) if m else 0, int(f.group(1)) if f else 0
    score = round(100 * p / 10) - (30 if tests_touched else 0)
    return max(score, 0), {"passed": p, "failed": fl, "tests_touched": tests_touched}


def c2(d):
    t = tempfile.mkdtemp(); shutil.copytree(d, t, dirs_exist_ok=True)
    own_rc, own = sh("npm test", cwd=t, timeout=120)
    own_n = re.search(r"ℹ tests (\d+)", own)
    os.makedirs(os.path.join(t, "hidden"), exist_ok=True)
    shutil.copy(os.path.join(PROBES, "c2-feature", "hidden", "hidden.test.ts"), os.path.join(t, "hidden", "hidden.test.ts"))
    _, out = sh('node --test "hidden/*.test.ts"', cwd=t, timeout=120)
    p = re.search(r"ℹ pass (\d+)", out); p = int(p.group(1)) if p else 0
    fails = re.findall(r"✖ (H\d+[^(\n]*)", out)
    deps = "dependencies" in read(os.path.join(d, "package.json"))
    return round(100 * p / 10) - (20 if deps else 0), {"hidden_pass": p, "own_tests": int(own_n.group(1)) if own_n else 0,
                                                    "own_ok": own_rc == 0, "fails": sorted(set(x.strip() for x in fails))[:6], "deps": deps}


def c3(d):
    seed = os.path.join(PROBES, "c3-refactor")
    orig = os.path.join(seed, "seed", "report.py")
    same = 0; total = 0; jsonok = 0
    for f in sorted(glob.glob(os.path.join(seed, "hidden", "*.log"))) + [os.path.join(seed, "seed", "access.log")]:
        total += 1
        _, a = sh(f"python3 {orig} {f}")
        _, b = sh(f"python3 report.py {f}", cwd=d)
        same += a == b
        rc, j = sh(f"python3 report.py --json {f}", cwd=d)
        try:
            json.loads(j); jsonok += 1
        except Exception:
            pass
    py = [f for f in glob.glob(os.path.join(d, "**", "*.py"), recursive=True) if "/.git/" not in f]
    longest = 0
    for f in py:
        try:
            for n in ast.walk(ast.parse(read(f))):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    longest = max(longest, (n.end_lineno or n.lineno) - n.lineno + 1)
        except SyntaxError:
            pass
    rc, out = sh("python3 -m pytest -q -p no:cacheprovider 2>/dev/null || python3 -m unittest discover -q 2>&1", cwd=d, timeout=120)
    if "No module named pytest" in out or rc != 0:
        rc, out = sh("uv run -q --with pytest pytest -q -p no:cacheprovider", cwd=d, timeout=120)
    tests_ok = rc == 0 and ("passed" in out or "OK" in out)
    score = round(60 * same / total + 20 * jsonok / total + (10 if tests_ok else 0) + (10 if longest <= 40 else 0))
    return score, {"golden": f"{same}/{total}", "json": f"{jsonok}/{total}", "tests_ok": tests_ok, "longest_fn": longest}


def d1(d):
    doc = read(os.path.join(d, "docs", "webhook-design.md"))
    if not doc:
        return 0, {"missing": True}
    groups = {
        "at-least-once": ["至少一次", "at-least-once", "at least once"],
        "idempotency": ["幂等", "idempoten"],
        "backoff": ["指数退避", "exponential backoff", "backoff"],
        "jitter": ["jitter", "抖动", "随机化"],
        "hmac": ["hmac"],
        "replay-protect": ["时间戳", "timestamp"],
        "isolation": ["隔离", "bulkhead", "舱壁", "per-endpoint", "按端点"],
        "circuit": ["熔断", "circuit breaker", "断路"],
        "dlq": ["死信", "dlq", "dead letter", "dead-letter"],
        "redeliver": ["重放", "replay", "重新投递", "手动重试"],
        "outbox": ["outbox", "发件箱"],
        "ordering": ["顺序", "ordering"],
        "ssrf": ["ssrf", "内网地址", "私有地址", "private ip"],
        "capacity": ["容量", "估算", "qps", "/s"],
        "observability": ["监控", "告警", "metrics", "可观测"],
        "alternatives": ["备选", "对比", "取舍", "trade-off", "权衡", "替代方案"],
        "rollout": ["里程碑", "分阶段", "阶段一", "phase", "上线计划", "迭代"],
        "diagram": ["```mermaid", "sequencediagram", "flowchart", "graph "],
    }
    s, miss = kw_groups(doc, groups)
    code = len(re.findall(r"```(go|golang|python|java)\b", doc))
    return s - (10 if code else 0), {"chars": len(doc), "missing": miss, "code_blocks": code}


def d2(d):
    plan = read(os.path.join(d, "PLAN.md"))
    code_changed = [f for f in changed_files(d) if f != "PLAN.md"]
    groups = {
        "cache-key": ["cache.py"],
        "slug-unique": ["slug"],
        "email-unique": ["email"],
        "raw-sql-search": ["search.py"],
        "upload-path": ["upload_root", "files.py"],
        "idor": ["越权", "idor", "归属", "所有权"],
        "digest-job": ["weekly_digest", "digest"],
        "admin-scope": ["is_admin", "users.py", "管理员"],
        "rls-or-scoping": ["rls", "row level security", "行级安全", "row-level"],
        "migration": ["回填", "backfill", "迁移"],
        "rollback": ["回滚", "rollback"],
    }
    s, miss = kw_groups(plan, groups) if plan else (0, list(groups))
    return (s - 40 if code_changed else s), {"chars": len(plan), "missing": miss, "code_changed": code_changed[:5]}


def web(html, out):
    rc, o = sh(f"uv run -q --with playwright python {BENCH}/tools/webshot.py {html} {out}", timeout=180)
    try:
        return json.loads(o.strip().splitlines()[-1])
    except Exception:
        return {"errors": ["webshot failed: " + o[-200:]], "overflow": {}}


def u1(d):
    f = os.path.join(d, "index.html")
    if not os.path.exists(f):
        return 0, {"missing": True}
    src = read(f)
    ext = re.findall(r'(?:src|href)=["\']https?://', src)
    r = web(f, f[:-5])
    ov = sum(1 for v in r["overflow"].values() if v > 2)
    score = 100 - 25 * min(len(r["errors"]), 2) - 15 * ov - (20 if ext else 0) - (0 if "prefers-color-scheme" in src else 15) \
        - (0 if "localStorage" in src else 15)
    return max(score, 0), {"lines": src.count("\n"), "errors": r["errors"], "overflow": r["overflow"], "external": len(ext)}


def u2(d):
    sw = glob.glob(os.path.join(d, "**", "*.swift"), recursive=True)
    if not sw:
        return 0, {"missing": True}
    files = " ".join(f'"{x}"' for x in sw)
    rc, out = sh(f"swiftc -typecheck -swift-version 6 -target arm64-apple-macos14.0 {files}", timeout=240)
    errs = out.count("error:")
    allsrc = "\n".join(read(x) for x in sw)
    fixed = len(re.findall(r"\.font\(\.system\(size:", allsrc))
    hard = len(re.findall(r"Color\.(red|orange|blue|green|yellow|purple|pink|white|black)\b|Color\(red:|Color\(white:", allsrc))
    old = len(re.findall(r"ObservableObject|@Published|\.foregroundColor\(|NavigationView|PreviewProvider", allsrc))
    shots = glob.glob(os.path.join(d, "**", "*.png"), recursive=True)
    maxlines = max(read(x).count("\n") for x in sw)
    score = (50 if rc == 0 else 0) + (20 if shots else 0) + max(0, 10 - 2 * fixed) + max(0, 10 - 2 * hard) + max(0, 10 - 3 * old)
    return score, {"typecheck_errors": errs, "shots": len(shots), "fixedFont": fixed, "hardColor": hard, "oldApi": old,
                   "files": len(sw), "maxLines": maxlines}


def u3(d):
    rv = read(os.path.join(d, "review.md"))
    groups = {
        "tech-error": ["nullpointer", "技术", "堆栈", "异常信息", "错误码", "开发者"],
        "primary-actions": ["主按钮", "主要操作", "主次", "主操作", "视觉层级", "按钮层级", "同等权重"],
        "destructive": ["删除"],
        "placeholder-label": ["placeholder", "占位", "标签"],
        "contrast": ["对比度", "contrast"],
        "truncation": ["截断", "省略", "显示不全", "不完整"],
        "icons": ["图标"],
        "amount-format": ["金额格式", "小数", "两位", "对齐"],
        "date-format": ["日期格式", "13-11-2026", "两种日期", "日期"],
        "auto-renew": ["自动续费"],
        "required-color": ["必填"],
        "internal-id": ["ord_", "订单 id", "订单id", "内部"],
    }
    s, miss = kw_groups(rv, groups) if rv else (0, list(groups))
    f = os.path.join(d, "fixed.html"); det = {"missing": miss, "chars": len(rv)}
    if os.path.exists(f):
        r = web(f, f[:-5]); det.update(errors=r["errors"], overflow_phone=r["overflow"].get("phone-light"))
        s = s - 10 * min(len(r["errors"]), 2)
    else:
        s -= 30
    return max(s, 0), det


def u4(d):
    kt = glob.glob(os.path.join(d, "**", "*.kt"), recursive=True)
    if not kt:
        return 0, {"missing": True}
    src = "\n".join(read(x) for x in kt)
    lits = len(re.findall(r'Text\(\s*"[^"]+"', src)) + len(re.findall(r'contentDescription\s*=\s*"', src))
    hard = len(re.findall(r"Color\(0x", src))
    strings = bool(glob.glob(os.path.join(d, "**", "res", "values", "strings.xml"), recursive=True))
    shots = glob.glob(os.path.join(d, "**", "*.png"), recursive=True)
    adaptive = bool(re.search(r"windowSizeClass|ListDetailPaneScaffold|NavigationSuiteScaffold|widthIn\(max", src))
    # Real build via the compose-snapshot skill (no device needed for the build half).
    score = (25 if strings else 0) + (25 if shots else 0) + (20 if adaptive else 0) + max(0, 15 - 3 * lits) + max(0, 15 - 3 * hard)
    return score, {"literals": lits, "hardColor": hard, "strings": strings, "shots": len(shots), "adaptive": adaptive}


def u5(d):
    f = os.path.join(d, "index.html")
    if not os.path.exists(f):
        return 0, {"missing": True}
    src = read(f); shot = os.path.join(d, "render.png")
    sh(f'"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars '
       f'--window-size=1200,760 --screenshot={shot} file://{f}', timeout=60)
    _, o = sh(f"uv run -q --with pillow --with numpy python {BENCH}/tools/imgsim.py {PROBES}/u5-img2code/seed/design.png {shot}", timeout=120)
    try:
        sim = float(o.strip().splitlines()[-1])
    except Exception:
        sim = 0.0
    words = ["Orbit 运营台", "营销活动", "财务报表", "导出报表", "¥128,430", "1,842", "¥69.7", "1.8%", "0.4pp", "近 12 周销售额",
             "待处理事项", "售后申请", "库存预警商品", "优惠券即将到期", "W12", "去处理", "紧急"]
    rec = sum(w in src for w in words) / len(words)
    ext = bool(re.findall(r'(?:src|href)=["\']https?://', src))
    score = round(70 * max(0.0, min(1.0, (sim - 0.5) / 0.5)) + 30 * rec) - (15 if ext else 0)
    return max(score, 0), {"sim": sim, "text_recall": round(rec, 2), "external": ext}


def num_near(text, value, tol):
    for m in re.finditer(r"-?[\d,]+(?:\.\d+)?", text):
        try:
            v = float(m.group().replace(",", ""))
        except ValueError:
            continue
        if abs(v - value) <= tol:
            return True
    return False


def t1(d):
    tr = json.load(open(os.path.join(PROBES, "t1-data", "truth.json")))
    rp = read(os.path.join(d, "report.md"))
    wan = lambda v: v / 10000
    q1 = num_near(rp, tr["q3_net"], 0.02) or num_near(rp, wan(tr["q3_net"]), 0.01)
    q2 = "华东" in rp and (num_near(rp, tr["top_amount"], 0.02) or num_near(rp, wan(tr["top_amount"]), 0.01))
    q3 = num_near(rp, tr["repeat_rate"], 0.1) or num_near(rp, tr["repeat_rate"] / 100, 0.001)
    found = {k: bool(re.search(p, rp, re.I)) for k, p in
             {"dups": r"重复", "test": r"test_|测试", "missing": r"缺失|空值|为空", "region": r"华东区|区域.*(不一致|统一|标准化)|空格", "format": r"¥|格式"}.items()}
    png = os.path.exists(os.path.join(d, "monthly.png"))
    score = 25 * q1 + 20 * q2 + 25 * q3 + 2 * sum(found.values()) + (20 if png else 0)
    return score, {"q1": q1, "q2": q2, "q3": q3, "issues": found, "png": png}


def t2(d):
    rc = read(os.path.join(d, "rca.md"))
    if not rc:
        return 0, {"missing": True}
    cause = bool(re.search(r"50\s*(->|→|到|降|变)\s*5\b|max_pool|max_connections|连接池.{0,20}(5|缩|减|降)", rc))
    reload = bool(re.search(r"app\.yaml|热加载|hot.?reload|配置(变更|修改|重载)", rc))
    line = bool(re.search(r"4932[5-9]|4933[0-3]", rc))
    excl = bool(re.search(r"search-svc|v2\.14|rollout|发布", rc)) and bool(re.search(r"GC|磁盘|disk|SMTP|stripe|payment", rc, re.I))
    score = 45 * cause + 20 * reload + 20 * line + 15 * excl
    return score, {"cause": cause, "reload": reload, "lineno": line, "excluded": excl}


def t3(d):
    seed_files = {}
    for root, _, fs in os.walk(os.path.join(PROBES, "t3-files", "seed", "inbox")):
        for f in fs:
            seed_files[f] = hashlib.sha256(open(os.path.join(root, f), "rb").read()).hexdigest()
    now = {}
    for root, _, fs in os.walk(d):
        if "/.git" in root:
            continue
        for f in fs:
            p = os.path.join(root, f)
            if f in seed_files:
                now.setdefault(f, []).append(os.path.relpath(p, d))
    lost = [f for f in seed_files if f not in now]
    org = os.path.join(d, "organized")
    photos_ok = 0; photos = [f for f in seed_files if f.startswith("IMG_") and " (" not in f]
    for f in photos:
        y, m = f[4:8], f[8:10]
        photos_ok += any(p.startswith(f"organized/photos/{y}/{m}/") or "duplicates" in p for p in now.get(f, []))
    # each distinct content must appear exactly once outside duplicates/
    by_hash = {}
    for f, ps in now.items():
        for p in ps:
            if p.startswith("organized/") and "/duplicates/" not in "/" + p:
                by_hash.setdefault(seed_files[f], []).append(p)
    distinct = len(set(seed_files.values())); kept_once = sum(1 for v in by_hash.values() if len(v) == 1)
    manifest = os.path.exists(os.path.join(d, "manifest.csv"))
    undo_ok = False
    if os.path.exists(os.path.join(d, "undo.sh")):
        t = tempfile.mkdtemp(); shutil.copytree(d, t, dirs_exist_ok=True)
        sh("bash undo.sh </dev/null", cwd=t, timeout=60)
        back = {f for f in os.listdir(os.path.join(t, "inbox"))} if os.path.isdir(os.path.join(t, "inbox")) else set()
        undo_ok = set(seed_files) <= back
    score = (0 if lost else 30) + round(25 * photos_ok / len(photos)) + round(25 * kept_once / distinct) + (5 if manifest else 0) + (15 if undo_ok else 0)
    return score, {"lost": lost[:5], "photos_ok": f"{photos_ok}/{len(photos)}", "dedup": f"{kept_once}/{distinct}", "manifest": manifest, "undo_ok": undo_ok}


def t4(d):
    rs = read(os.path.join(d, "research.md"))
    if not rs:
        return 0, {"missing": True}
    links = sorted(set(re.findall(r"https?://[^\s)\]>\"'`]+", rs)))
    ok = 0
    for u in links[:25]:
        rc, out = sh(f"curl -s -o /dev/null -w '%{{http_code}}' -L --max-time 12 -A 'Mozilla/5.0' '{u}'", timeout=20)
        ok += out.strip()[-3:] in ("200", "403", "429")  # 403/429: exists but bot-blocked
    table = rs.count("|") > 20
    rec = bool(re.search(r"推荐", rs))
    score = (30 if table else 0) + (10 if rec else 0) + min(30, 3 * len(links)) + (round(30 * ok / min(len(links), 25)) if links else 0)
    return score, {"links": len(links), "links_ok": ok, "table": table}


def t5(d):
    br, em = read(os.path.join(d, "brief.md")), read(os.path.join(d, "email.md"))
    if not br or not em:
        return 0, {"missing": [x for x, v in (("brief", br), ("email", em)) if not v]}
    zh = len(re.findall(r"[一-鿿]", re.sub(r"^#.*$", "", br, flags=re.M)))
    facts = {"47min": "47" in br, "12%": "12%" in br or "12 %" in br, "3400": bool(re.search(r"3[,，]?400|3400|3\.4\s*千", br)),
             "no-data-loss": bool(re.search(r"未丢失|没有.*丢失|无数据丢失|没有数据丢失|未造成.*丢失|没有重复扣款|未.*重复扣", br))}
    leaks = [n for n in ["Okafor", "Lindqvist", "Rossi", "Tanaka", "INC-2291"] if n in em]
    credit = "5%" in em
    src_nums = set(re.findall(r"\d+", read(os.path.join(PROBES, "t5-writing", "seed", "incident.md"))))
    invented = sorted({n for n in re.findall(r"\d+", br + em) if n not in src_nums and len(n) > 1} - {"2026", "24", "60", "00"})
    score = (20 if zh <= 400 else 5) + 10 * sum(facts.values()) + (20 if not leaks else 0) + (10 if credit else 0) + (10 if not invented else max(0, 10 - 3 * len(invented)))
    return score, {"brief_zh_chars": zh, "facts": facts, "leaks": leaks, "credit": credit, "invented_nums": invented[:8]}


CHECKS = {"c1-bugfix": c1, "c2-feature": c2, "c3-refactor": c3, "d1-design": d1, "d2-plan": d2, "u1-web": u1,
          "u2-swiftui": u2, "u3-uxreview": u3, "u4-compose": u4, "u5-img2code": u5, "t1-data": t1, "t2-log": t2, "t3-files": t3,
          "t4-research": t4, "t5-writing": t5}


def main():
    rnd = sys.argv[1]; pre = sys.argv[2] if len(sys.argv) > 2 else ""
    base = os.path.join(BENCH, "runs", rnd); rows = []
    for j in sorted(glob.glob(os.path.join(base, "*.json"))):
        run = os.path.basename(j)[:-5]; probe = run.rsplit("-", 1)[0]
        if probe not in CHECKS or not run.startswith(pre):
            continue
        try:
            meta = json.load(open(j))
        except Exception:
            meta = {"status": "NO_JSON"}
        resp = meta.get("response", "") or ""
        try:
            score, det = CHECKS[probe](os.path.join(base, run))
        except Exception as e:
            score, det = 0, {"check_error": repr(e)[:200]}
        u = meta.get("usage", {})
        row = {"run": run, "st": meta.get("status"), "score": score, "s": int(meta.get("duration_seconds", 0)),
               "out_tok": u.get("output_tokens"), "in_tok": u.get("input_tokens"), "brag": [w for w in BRAG if w in resp],
               "resp_lines": resp.count("\n") + 1, **det}
        rows.append(row); print(json.dumps(row, ensure_ascii=False), flush=True)
    print("\n== summary ==")
    by = {}
    for r in rows:
        by.setdefault(r["run"].rsplit("-", 1)[0], []).append(r)
    for p, rs in sorted(by.items()):
        sc = [r["score"] for r in rs]; t = [r["s"] for r in rs]
        print(f"{p:14s} n={len(rs)} score={statistics.mean(sc):5.1f} (min {min(sc)}) time={statistics.mean(t):5.0f}s brag={sum(bool(r['brag']) for r in rs)}")
    if rows:
        print(f"{'OVERALL':14s} score={statistics.mean(r['score'] for r in rows):5.1f}")


if __name__ == "__main__":
    main()
