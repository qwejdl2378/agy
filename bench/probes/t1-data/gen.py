# Generates seed/orders.csv and truth.json (deterministic).
import random, csv, json, datetime as dt, os
r = random.Random(42); here = os.path.dirname(os.path.abspath(__file__))
regions = ['华东', '华北', '华南', '西部']
variants = {'华东': ['华东', '华东区', ' 华东', '华东 '], '华北': ['华北', '华北区'], '华南': ['华南', '华南 '], '西部': ['西部', '西部区']}
custs = ['c%04d' % i for i in range(1, 900)] + ['test_%02d' % i for i in range(5)]
rows = []; oid = 100000
start = dt.date(2026, 6, 1)
for i in range(5200):
    oid += 1; d = start + dt.timedelta(days=r.randint(0, 152))
    c = r.choice(custs); reg = r.choices(regions, [4, 3, 2, 1])[0]
    amt = round(r.uniform(20, 3000) * (1.3 if reg == '华南' else 1), 2)
    st = 'paid'
    if r.random() < 0.06: st = 'refunded'; amt = -round(amt * r.choice([1, 0.5]), 2)
    rows.append(dict(order_id=str(oid), date=d, customer=c, region=reg, amount=amt, status=st))
truth_rows = [x for x in rows]
# dirty output
out = []
missing = set(r.sample(range(len(rows)), 7))
for i, x in enumerate(rows):
    d = x['date']; f = r.random()
    ds = d.isoformat() if f < 0.6 else (f'{d.year}/{d.month}/{d.day}' if f < 0.85 else f'{d.year}年{d.month}月{d.day}日')
    a = x['amount']; g = r.random()
    if i in missing: s = ''
    elif g < 0.7: s = f'{a:.2f}'
    elif g < 0.9: s = ('-' if a < 0 else '') + f'¥{abs(a):,.2f}'
    else: s = f'{a:,.2f}'
    out.append([x['order_id'], ds, x['customer'], r.choice(variants[x['region']]), s, x['status']])
dups = r.sample(range(len(out)), 60)
for j in dups: out.insert(r.randint(0, len(out)), list(out[j]))
with open(os.path.join(here, 'seed', 'orders.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['order_id', 'order_date', 'customer', 'region', 'amount', 'status']); w.writerows(out)
# truth
valid = [x for i, x in enumerate(rows) if i not in missing and not x['customer'].startswith('test_')]
q3 = [x for x in valid if dt.date(2026, 7, 1) <= x['date'] <= dt.date(2026, 9, 30)]
net = round(sum(x['amount'] for x in q3), 2)
byreg = {}
for x in q3: byreg[x['region']] = round(byreg.get(x['region'], 0) + x['amount'], 2)
top = max(byreg, key=byreg.get)
cnt = {}
for x in q3:
    if x['status'] == 'paid': cnt[x['customer']] = cnt.get(x['customer'], 0) + 1
buyers = len(cnt); rep = sum(1 for v in cnt.values() if v >= 2)
monthly = {}
for x in valid: k = x['date'].strftime('%Y-%m'); monthly[k] = round(monthly.get(k, 0) + x['amount'], 2)
json.dump(dict(q3_net=net, by_region=byreg, top_region=top, top_amount=byreg[top], buyers=buyers, repeat=rep,
               repeat_rate=round(rep / buyers * 100, 1), missing=len(missing), dups=60, monthly=monthly,
               test_rows=sum(1 for x in rows if x['customer'].startswith('test_'))), open(os.path.join(here, 'truth.json'), 'w'), ensure_ascii=False, indent=1)
