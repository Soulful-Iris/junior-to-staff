/** Bounded workers: preserve input order; drain started work and report errors per item. */
export async function mapLimit<T, R>(items: readonly T[], limit: number, fn: (item: T, index: number) => Promise<R>): Promise<PromiseSettledResult<R>[]> {
  if (!Number.isInteger(limit) || limit < 1) throw new RangeError('positive integer limit required');
  const out: PromiseSettledResult<R>[] = new Array(items.length);
  let next = 0;
  async function worker() {
    while (next < items.length) {
      const index = next++; // No await between reading and claiming the index.
      try { out[index] = { status: 'fulfilled', value: await fn(items[index], index) }; }
      catch (reason) { out[index] = { status: 'rejected', reason }; }
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return out;
}

/** Aborting old work saves resources where supported. The generation guard protects correctness. */
export function latestOnly<T>(load: (query: string, signal: AbortSignal) => Promise<T>, render: (value: T) => void) {
  let generation = 0;
  let active: AbortController | undefined;
  return async (query: string): Promise<boolean> => {
    const own = ++generation;
    active?.abort();
    const controller = new AbortController();
    active = controller;
    try {
      const value = await load(query, controller.signal);
      if (own !== generation) return false;
      render(value);
      return true;
    } catch (error) {
      if (own !== generation) return false;
      throw error; // Current request failure must be visible to the caller/UI.
    }
  };
}

export class LRU<K, V> {
  private readonly values = new Map<K, V>();
  private readonly capacity: number;
  constructor(capacity: number) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('nonnegative integer capacity required');
    this.capacity = capacity;
  }
  get(key: K): V | undefined {
    if (!this.values.has(key)) return undefined;
    const value = this.values.get(key) as V;
    this.values.delete(key);
    this.values.set(key, value);
    return value;
  }
  put(key: K, value: V) {
    if (this.capacity === 0) return;
    this.values.delete(key);
    this.values.set(key, value);
    if (this.values.size > this.capacity) this.values.delete(this.values.keys().next().value as K);
  }
}

export type Bookmark = { id: string; title: string; version: number };
/** Apply a server response only if no newer local/server version is known. */
export function reconcile(current: Bookmark, incoming: Bookmark): Bookmark {
  if (current.id !== incoming.id) throw new Error('different entity');
  return incoming.version >= current.version ? incoming : current;
}
