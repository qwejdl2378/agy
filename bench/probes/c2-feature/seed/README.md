# taskq

Zero-dependency in-process task queue for Node 24 (TypeScript runs natively via type stripping; no build step, no npm deps allowed).

## API (`src/queue.ts`)

```ts
export class TaskQueue {
  constructor(opts: {
    concurrency: number;                       // >= 1, else throw RangeError
    retries?: number;                          // extra attempts after the first failure, default 0
    retryDelayMs?: (attempt: number) => number;// attempt = 1 for the first retry; default () => 0
    timeoutMs?: number;                        // per attempt; default none
  });
  add<T>(fn: (signal: AbortSignal) => Promise<T>,
         opts?: { priority?: number; signal?: AbortSignal; id?: string }): Promise<T>;
  readonly size: number;     // tasks waiting (not started, including those waiting for a retry delay)
  readonly pending: number;  // tasks currently running an attempt
  onIdle(): Promise<void>;   // resolves when size === 0 && pending === 0 (immediately if already idle)
  pause(): void;             // stop starting new attempts; running ones continue
  resume(): void;
}
```

## Semantics
1. Higher `priority` starts first (default 0); equal priority is FIFO.
2. Never more than `concurrency` attempts run at once.
3. A rejected attempt is retried up to `retries` times, waiting `retryDelayMs(attempt)` before re-entering the queue with its original priority. The final rejection reason is the last error.
4. `timeoutMs`: if an attempt does not settle in time, its signal is aborted and the attempt fails with an `Error` whose `name` is `"TimeoutError"`. Timeouts count as failures and may be retried.
5. External `signal`: if already aborted when `add` is called, or aborted while the task is waiting, the task is removed and its promise rejects with an `Error` whose `name` is `"AbortError"` (fn is never called). If aborted while running, the attempt's signal is aborted, the promise rejects with `"AbortError"` and **no retry** happens.
6. `id` dedupe: adding a task whose `id` is waiting or running returns the same promise and does not enqueue anything. After it settles the id can be reused.
7. An error thrown synchronously by `fn` is treated like a rejection.
