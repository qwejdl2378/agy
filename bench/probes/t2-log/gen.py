import random, os, datetime as dt
r = random.Random(5); here = os.path.dirname(os.path.abspath(__file__))
t0 = dt.datetime(2026, 11, 12, 12, 0, 0); lines = []
svcs = ['api-gw', 'order-svc', 'payment-svc', 'search-svc', 'notify-svc']
def L(t, svc, lvl, msg): lines.append((t, f"{t.isoformat(timespec='milliseconds')} {lvl:<5} [{svc}] {msg}"))
pool = 50; cur = t0; reqid = 0
while cur < t0 + dt.timedelta(hours=4):
    cur += dt.timedelta(milliseconds=r.randint(40, 260)); reqid += 1
    svc = r.choice(svcs); after = cur >= dt.datetime(2026, 11, 12, 14, 2, 41)
    if svc == 'order-svc':
        busy = r.randint(5, 30) if not after else 5
        wait = r.randint(1, 8) if not after else r.randint(200, 3000)
        if after and r.random() < 0.35:
            L(cur, svc, 'ERROR', f'req={reqid:x} db acquire timeout after 3000ms (pool active={busy}/{pool} waiting={r.randint(20,180)})')
            L(cur + dt.timedelta(milliseconds=3), 'api-gw', 'ERROR', f'req={reqid:x} upstream order-svc returned 503 in 3012ms')
        else:
            L(cur, svc, 'INFO', f'req={reqid:x} POST /orders 201 {wait + r.randint(10,40)}ms pool active={busy}/{pool}')
    elif svc == 'payment-svc':
        L(cur, svc, 'INFO', f'req={reqid:x} charge ok provider=stripe {r.randint(80,400)}ms')
        if r.random() < 0.004: L(cur, svc, 'WARN', f'req={reqid:x} provider latency high {r.randint(1500,2500)}ms')
    elif svc == 'search-svc':
        L(cur, svc, 'INFO', f'req={reqid:x} GET /search 200 {r.randint(20,90)}ms')
        if r.random() < 0.01: L(cur, svc, 'WARN', 'GC pause 412ms (G1 Young)')
    elif svc == 'notify-svc':
        L(cur, svc, 'INFO', f'req={reqid:x} email queued')
        if r.random() < 0.003: L(cur, svc, 'ERROR', f'req={reqid:x} SMTP 421 try again later')
    else:
        L(cur, svc, 'INFO', f'req={reqid:x} {r.choice(["GET","POST"])} {r.choice(["/orders","/search","/pay","/me"])} 200')
    if cur.minute == 55 and cur.hour == 13 and not any('rollout' in x[1] for x in lines[-2000:]):
        L(cur, 'search-svc', 'INFO', 'rollout v2.14.0 started (image search-svc:2.14.0) replicas 0/6')
        L(cur + dt.timedelta(seconds=40), 'search-svc', 'INFO', 'rollout v2.14.0 complete replicas 6/6')
        L(cur + dt.timedelta(seconds=41), 'search-svc', 'WARN', 'deprecated config key search.legacy_ranker ignored')
    if after and pool == 50:
        L(dt.datetime(2026, 11, 12, 14, 2, 40, 100000), 'order-svc', 'INFO', 'config watcher: /etc/order/app.yaml changed (sha 9c1e..→4ab2..), hot reloading')
        L(dt.datetime(2026, 11, 12, 14, 2, 40, 300000), 'order-svc', 'INFO', 'db.pool resized max_connections 50 -> 5 (from db.max_pool_size)')
        L(dt.datetime(2026, 11, 12, 14, 2, 40, 310000), 'order-svc', 'INFO', 'feature flag checkout_v3 unchanged')
        pool = 5
    if cur.hour == 14 and cur.minute == 10 and r.random() < 0.01:
        L(cur, 'api-gw', 'WARN', 'disk usage /var/log 81%')
    if after and r.random() < 0.002:
        L(cur, 'order-svc', 'WARN', 'HikariPool-1 - Thread starvation or clock leap detected')
lines.sort(key=lambda x: x[0])
open(os.path.join(here, 'seed', 'app.log'), 'w').write('\n'.join(x[1] for x in lines) + '\n')
print(len(lines))
