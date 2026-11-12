type Opts = { concurrency: number; retries?: number; retryDelayMs?: (a: number) => number; timeoutMs?: number };
type Item = { fn: (s: AbortSignal) => Promise<any>; priority: number; seq: number; signal?: AbortSignal; id?: string;
  attempt: number; resolve: (v: any) => void; reject: (e: any) => void; onAbort?: () => void; ctrl?: AbortController; running: boolean; timer?: any };
const err = (name: string, msg: string) => Object.assign(new Error(msg), { name });
export class TaskQueue {
  #o: Required<Omit<Opts, 'timeoutMs'>> & { timeoutMs?: number };
  #q: Item[] = []; #delayed = 0; #running = 0; #seq = 0; #paused = false; #ids = new Map<string, Promise<any>>(); #idle: (() => void)[] = [];
  constructor(o: Opts) {
    if (!(o.concurrency >= 1)) throw new RangeError('concurrency');
    this.#o = { retries: 0, retryDelayMs: () => 0, ...o };
  }
  get size() { return this.#q.length + this.#delayed; }
  get pending() { return this.#running; }
  add<T>(fn: (s: AbortSignal) => Promise<T>, opts: { priority?: number; signal?: AbortSignal; id?: string } = {}): Promise<T> {
    if (opts.id !== undefined && this.#ids.has(opts.id)) return this.#ids.get(opts.id)!;
    let it!: Item;
    const p = new Promise<T>((resolve, reject) => { it = { fn, priority: opts.priority ?? 0, seq: this.#seq++, signal: opts.signal, id: opts.id, attempt: 0, resolve, reject, running: false }; });
    if (opts.signal?.aborted) { it.reject(err('AbortError', 'aborted')); return p; }
    if (opts.id !== undefined) { this.#ids.set(opts.id, p); p.then(() => this.#ids.delete(opts.id!), () => this.#ids.delete(opts.id!)); }
    if (opts.signal) { it.onAbort = () => this.#abort(it); opts.signal.addEventListener('abort', it.onAbort, { once: true }); }
    this.#enqueue(it); return p;
  }
  #enqueue(it: Item) { this.#q.push(it); this.#q.sort((a, b) => b.priority - a.priority || a.seq - b.seq); this.#pump(); }
  #abort(it: Item) {
    const i = this.#q.indexOf(it);
    if (i >= 0) this.#q.splice(i, 1);
    if (it.running) it.ctrl!.abort(err('AbortError', 'aborted'));
    if (it.timer) { clearTimeout(it.timer); it.timer = undefined; this.#delayed--; }
    this.#finish(it, false, err('AbortError', 'aborted'));
  }
  #done = new WeakSet<Item>();
  #finish(it: Item, ok: boolean, v: any) {
    if (this.#done.has(it)) return; this.#done.add(it);
    if (it.onAbort) it.signal!.removeEventListener('abort', it.onAbort);
    ok ? it.resolve(v) : it.reject(v); this.#checkIdle();
  }
  #checkIdle() { queueMicrotask(() => { if (this.size === 0 && this.#running === 0) { const w = this.#idle; this.#idle = []; w.forEach(f => f()); } }); }
  #pump() {
    while (!this.#paused && this.#running < this.#o.concurrency && this.#q.length) this.#start(this.#q.shift()!);
  }
  #start(it: Item) {
    this.#running++; it.running = true; it.attempt++;
    const ctrl = new AbortController(); it.ctrl = ctrl;
    let to: any;
    const attempt = new Promise((res, rej) => {
      if (this.#o.timeoutMs !== undefined) to = setTimeout(() => { const e = err('TimeoutError', 'timeout'); ctrl.abort(e); rej(e); }, this.#o.timeoutMs);
      try { Promise.resolve(it.fn(ctrl.signal)).then(res, rej); } catch (e) { rej(e); }
    });
    attempt.then(v => ({ ok: true, v }), e => ({ ok: false, v: e })).then((r: any) => {
      clearTimeout(to); this.#running--; it.running = false;
      if (this.#done.has(it)) { this.#pump(); this.#checkIdle(); return; }
      if (r.ok) this.#finish(it, true, r.v);
      else if (it.attempt <= this.#o.retries) {
        this.#delayed++;
        it.timer = setTimeout(() => { it.timer = undefined; this.#delayed--; this.#enqueue(it); }, this.#o.retryDelayMs(it.attempt));
      } else this.#finish(it, false, r.v);
      this.#pump();
    });
  }
  onIdle() { if (this.size === 0 && this.#running === 0) return Promise.resolve(); return new Promise<void>(r => this.#idle.push(r)); }
  pause() { this.#paused = true; }
  resume() { this.#paused = false; this.#pump(); }
}
