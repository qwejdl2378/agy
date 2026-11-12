# Seconds to wait before retrying after a quota error: until the earliest account renewal
# among exhausted accounts, else a short backoff.
import json, glob, os, datetime as dt
f = max(glob.glob(os.path.expanduser("~/.config/magpie/routing/*.jsonl")), key=os.path.getmtime)
order = json.loads(open(f).read().splitlines()[-1]).get("order", [])
now = dt.datetime.now(dt.timezone.utc)
free = [o for o in order if o.get("used", 0) < 98]
if free:
    print(300)
else:
    dues = [dt.datetime.fromisoformat(o["due"].replace("Z", "+00:00")) for o in order if o.get("due")]
    print(max(300, int((min(dues) - now).total_seconds()) + 120) if dues else 1800)
