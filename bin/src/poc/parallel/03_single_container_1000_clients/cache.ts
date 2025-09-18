/**
 * 高速LRUキャッシュ - 03独立実装
 */

export class LRUCache<T> {
  private cache = new Map<string, { data: T; timestamp: number }>();
  private accessOrder: string[] = [];

  constructor(
    private maxSize: number,
    private ttl: number,
  ) {}

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;

    // TTLチェック
    if (Date.now() - entry.timestamp > this.ttl) {
      this.delete(key);
      return undefined;
    }

    // LRU更新
    this.updateAccessOrder(key);
    return entry.data;
  }

  set(key: string, data: T): void {
    if (this.cache.has(key)) {
      this.delete(key);
    }

    if (this.cache.size >= this.maxSize) {
      const lruKey = this.accessOrder[0];
      if (lruKey) {
        this.delete(lruKey);
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
    this.accessOrder.push(key);
  }

  delete(key: string): boolean {
    const result = this.cache.delete(key);
    this.accessOrder = this.accessOrder.filter(k => k !== key);
    return result;
  }

  get size(): number {
    return this.cache.size;
  }

  private updateAccessOrder(key: string): void {
    this.accessOrder = this.accessOrder.filter(k => k !== key);
    this.accessOrder.push(key);
  }
}