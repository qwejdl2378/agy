import random, os, hashlib, json
r = random.Random(3); here = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(here, 'seed', 'inbox')
files = {}
def put(name, data): files[name] = data
for i in range(40):
    y, m, d = r.choice([2024, 2025, 2026]), r.randint(1, 12), r.randint(1, 28)
    put(f'IMG_{y}{m:02d}{d:02d}_{r.randint(100000,235959)}.jpg', b'\xff\xd8\xff' + r.randbytes(r.randint(2000, 6000)))
for i in range(12):
    y, m, d = 2026, r.randint(1, 10), r.randint(1, 28)
    put(f'Screenshot {y}-{m:02d}-{d:02d} at {r.randint(9,22)}.{r.randint(10,59)}.{r.randint(10,59)}.png', b'\x89PNG' + r.randbytes(r.randint(1000, 3000)))
for n in ['发票-2026-10.pdf', 'contract_v2.pdf', 'resume.docx', '会议纪要.docx', 'budget.xlsx', 'notes.txt', 'setup.dmg', 'archive.zip', 'song.mp3', 'clip.mov', 'README', '.DS_Store']:
    put(n, r.randbytes(r.randint(500, 4000)))
names = list(files)
dupsrc = r.sample([n for n in names if n != '.DS_Store'], 9)
for i, n in enumerate(dupsrc):
    base, ext = os.path.splitext(n)
    alt = [f'{base} (1){ext}', f'{base} copy{ext}', f'download_{i}{ext}'][i % 3]
    put(alt, files[n])
put('IMG_20250101_000000 (2).jpg', files[dupsrc[0]])  # triple
for n, b in files.items(): open(os.path.join(D, n), 'wb').write(b)
json.dump({'n_files': len(files), 'dup_groups': len(dupsrc)}, open(os.path.join(here, 'truth.json'), 'w'))
print(len(files))
