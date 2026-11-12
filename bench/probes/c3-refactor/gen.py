import random, sys
def gen(seed, n):
    r = random.Random(seed); out = []
    eps = [('GET','/'),('GET','/api/items'),('GET','/api/items/'),('POST','/api/items'),('GET','/api/search?q=x'),('GET','/static/app.js'),('DELETE','/api/items/7'),('GET','/health')]
    for i in range(n):
        if r.random() < 0.02: out.append('garbage line ' + str(i)); continue
        ip = '10.0.%d.%d' % (r.randint(0,3), r.randint(1,20)); m,p = r.choice(eps)
        s = r.choice([200]*12+[201,204,301,304,400,404,500,502,503])
        b = '-' if r.random()<0.1 else str(r.randint(100, 900000))
        t = round(r.expovariate(3) + (1.5 if p.startswith('/api/search') and r.random()<0.3 else 0), 3)
        out.append('%s - - [%02d/Nov/2026:%02d:%02d:%02d +0900] "%s %s HTTP/1.1" %d %s %.3f' % (ip, 12, r.randint(0,23), r.randint(0,59), r.randint(0,59), m, p, s, b, t))
    if r.random() < 2: out.append('')
    return '\n'.join(out)
open(sys.argv[1],'w').write(gen(int(sys.argv[2]), int(sys.argv[3])))
