# Screenshot a local HTML file in phone/desktop, light/dark; report console errors and horizontal overflow.
# usage: uv run --with playwright python webshot.py <html> <out_prefix>
import sys, json
from playwright.sync_api import sync_playwright
html, out = sys.argv[1], sys.argv[2]
res = {"errors": [], "overflow": {}}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    for name, vp in [("phone", (390, 844)), ("desktop", (1280, 800))]:
        for scheme in ("light", "dark"):
            pg = b.new_page(viewport={"width": vp[0], "height": vp[1]}, color_scheme=scheme, device_scale_factor=2 if name == "phone" else 1)
            pg.on("console", lambda m: m.type == "error" and res["errors"].append(m.text))
            pg.on("pageerror", lambda e: res["errors"].append(str(e)))
            pg.goto("file://" + html); pg.wait_for_timeout(600)
            res["overflow"][f"{name}-{scheme}"] = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            pg.screenshot(path=f"{out}-{name}-{scheme}.png", full_page=False)
            pg.close()
    b.close()
res["errors"] = sorted(set(res["errors"]))[:10]
print(json.dumps(res, ensure_ascii=False))
