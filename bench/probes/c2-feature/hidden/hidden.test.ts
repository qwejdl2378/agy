import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TaskQueue } from '../src/queue.ts';
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
const d = <T,>(v: T, ms: number) => () => sleep(ms).then(() => v);

test('H1 concurrency bound and RangeError', async () => {
  assert.throws(() => new TaskQueue({ concurrency: 0 }), RangeError);
  const q = new TaskQueue({ concurrency: 2 }); let cur = 0, max = 0;
  const job = async () => { cur++; max = Math.max(max, cur); await sleep(15); cur--; };
  await Promise.all(Array.from({ length: 6 }, () => q.add(job)));
  assert.equal(max, 2);
});
test('H2 priority then FIFO', async () => {
  const q = new TaskQueue({ concurrency: 1 }); const order: string[] = [];
  q.pause();
  const mk = (n: string) => async () => { order.push(n); };
  const ps = [q.add(mk('a')), q.add(mk('b'), { priority: 5 }), q.add(mk('c')), q.add(mk('d'), { priority: 5 })];
  assert.equal(q.size, 4); q.resume(); await Promise.all(ps);
  assert.deepEqual(order, ['b', 'd', 'a', 'c']);
});
test('H3 retries with delay attempt numbering, final error', async () => {
  const seen: number[] = []; let n = 0;
  const q = new TaskQueue({ concurrency: 1, retries: 2, retryDelayMs: a => { seen.push(a); return 5; } });
  await assert.rejects(q.add(async () => { n++; throw new Error('e' + n); }), /e3/);
  assert.equal(n, 3); assert.deepEqual(seen, [1, 2]);
});
test('H4 retry eventually succeeds', async () => {
  let n = 0; const q = new TaskQueue({ concurrency: 1, retries: 3 });
  assert.equal(await q.add(async () => { if (++n < 3) throw new Error('x'); return 'ok'; }), 'ok');
});
test('H5 timeout aborts signal and is retried', async () => {
  const q = new TaskQueue({ concurrency: 1, timeoutMs: 20, retries: 1 }); let aborted = 0, n = 0;
  await assert.rejects(q.add(s => new Promise(() => { n++; s.addEventListener('abort', () => aborted++); })), (e: any) => e.name === 'TimeoutError');
  assert.equal(n, 2); assert.equal(aborted, 2);
});
test('H6 pre-aborted and waiting abort never call fn', async () => {
  const q = new TaskQueue({ concurrency: 1 }); let called = 0;
  await assert.rejects(q.add(async () => { called++; }, { signal: AbortSignal.abort() }), (e: any) => e.name === 'AbortError');
  const blocker = q.add(d(1, 30)); const ac = new AbortController();
  const p = q.add(async () => { called++; }, { signal: ac.signal });
  assert.equal(q.size, 1); ac.abort();
  await assert.rejects(p, (e: any) => e.name === 'AbortError');
  assert.equal(q.size, 0); await blocker; assert.equal(called, 0);
});
test('H7 abort while running: no retry, signal forwarded', async () => {
  const q = new TaskQueue({ concurrency: 1, retries: 3 }); const ac = new AbortController(); let n = 0, inner = false;
  const p = q.add(s => new Promise((_, rej) => { n++; s.addEventListener('abort', () => { inner = true; rej(new Error('inner')); }); }), { signal: ac.signal });
  await sleep(5); ac.abort();
  await assert.rejects(p, (e: any) => e.name === 'AbortError');
  await sleep(20); assert.equal(n, 1); assert.ok(inner);
});
test('H8 id dedupe and reuse after settle', async () => {
  const q = new TaskQueue({ concurrency: 1 }); let n = 0;
  const f = async () => { n++; await sleep(5); return n; };
  const a = q.add(f, { id: 'k' }), b = q.add(f, { id: 'k' });
  assert.equal(a, b); assert.equal(await a, 1);
  assert.equal(await q.add(f, { id: 'k' }), 2);
});
test('H9 sync throw is rejection; onIdle', async () => {
  const q = new TaskQueue({ concurrency: 2 });
  await q.onIdle();
  await assert.rejects(q.add((() => { throw new Error('sync'); }) as any), /sync/);
  let done = 0; q.add(async () => { await sleep(10); done++; }); q.add(async () => { await sleep(20); done++; });
  await q.onIdle(); assert.equal(done, 2); assert.equal(q.pending, 0);
});
test('H10 size counts retry-delayed tasks; pause keeps running ones', async () => {
  const q = new TaskQueue({ concurrency: 1, retries: 1, retryDelayMs: () => 30 });
  const p = q.add(async () => { throw new Error('x'); }).catch(() => {});
  await sleep(10); assert.equal(q.size, 1); assert.equal(q.pending, 0);
  await p;
  const r = q.add(d('r', 20)); await sleep(2); q.pause(); const w = q.add(d('w', 1));
  assert.equal(await r, 'r'); await sleep(10); assert.equal(q.size, 1); q.resume(); assert.equal(await w, 'w');
});
