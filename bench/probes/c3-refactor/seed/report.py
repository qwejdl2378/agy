import sys, re, json
from collections import defaultdict
# quick script written in a hurry, do not judge
def main():
    f = sys.argv[1]
    data = open(f).read().split('\n')
    tot = 0; errs = 0; st = defaultdict(int); paths = defaultdict(list); ips = defaultdict(int); bad = 0; bytes_ = 0; hours = defaultdict(int); slow = []
    for l in data:
        if l.strip() == '': continue
        m = re.match(r'(\S+) \S+ \S+ \[(\d+)/(\w+)/(\d+):(\d+):(\d+):(\d+) [^\]]+\] "(\S+) (\S+) [^"]*" (\d+) (\S+) (\d+\.\d+)', l)
        if not m:
            bad += 1; continue
        tot += 1
        ip = m.group(1); h = int(m.group(5)); meth = m.group(8); p = m.group(9); s = int(m.group(10)); b = m.group(11); t = float(m.group(12))
        if '?' in p: p = p[:p.index('?')]
        if p != '/' and p.endswith('/'): p = p[:-1]
        st[s // 100] += 1
        if s >= 500: errs += 1
        if b != '-': bytes_ += int(b)
        ips[ip] += 1
        hours[h] += 1
        paths[meth + ' ' + p].append(t)
        if t > 1.0: slow.append((t, meth + ' ' + p, ip))
    print('== Access report ==')
    print('requests: %d  (unparsed lines: %d)' % (tot, bad))
    if tot == 0:
        print('no data'); return
    print('5xx rate: %.2f%%' % (errs * 100.0 / tot))
    print('traffic: %.1f MB' % (bytes_ / 1024.0 / 1024.0))
    print('-- status classes --')
    for k in sorted(st.keys()):
        print('  %dxx %6d' % (k, st[k]))
    print('-- top endpoints by p95 latency (min 3 hits) --')
    rows = []
    for k in paths:
        v = sorted(paths[k])
        if len(v) < 3: continue
        i = int(round(0.95 * (len(v) - 1)))
        rows.append((v[i], k, len(v), sum(v) / len(v)))
    rows.sort(key=lambda r: (-r[0], r[1]))
    for r in rows[:5]:
        print('  %-30s p95=%.3fs avg=%.3fs n=%d' % (r[1], r[0], r[3], r[2]))
    print('-- top clients --')
    cl = sorted(ips.items(), key=lambda x: (-x[1], x[0]))[:3]
    for ip, n in cl:
        print('  %-15s %d' % (ip, n))
    print('-- busiest hour --')
    bh = sorted(hours.items(), key=lambda x: (-x[1], x[0]))[0]
    print('  %02d:00 %d requests' % (bh[0], bh[1]))
    print('-- slow requests (>1s): %d --' % len(slow))
    slow.sort(key=lambda x: -x[0])
    for s in slow[:3]:
        print('  %.3fs %s from %s' % s)
main()
