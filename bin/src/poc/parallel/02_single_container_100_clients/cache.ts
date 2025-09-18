/**
 * LRUキャッシュ実装
 */

import type { CacheEntry } from "./types.ts";

export class LRUCache<T> {
  private cache = new Map<string, CacheEntry<T>>();
  private accessOrder: string[] = [];

  constructor(
    private maxSize: number,
    private ttl: number, // milliseconds
  ) {}

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;

    // TTLチェック
    if (Date.now() - entry.timestamp > this.ttl) {
      this.delete(key);
      return undefined;
    }

    // LRU: アクセス順を更新
    this.updateAccessOrder(key);
    return entry.data;
  }

  set(key: string, data: T): void {
    // 既存のキーの場合は削除
    if (this.cache.has(key)) {
      this.delete(key);
    }

    // サイズ制限チェック
    if (this.cache.size >= this.maxSize) {
      const lruKey = this.accessOrder[0];
      if (lruKey) {
        this.delete(lruKey);
      }
    }

    // 新規追加
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

  clear(): void {
    this.cache.clear();
    this.accessOrder = [];
  }

  get size(): number {
    return this.cache.size;
  }

  // キャッシュ統計
  getStats(): {
    size: number;
    maxSize: number;
    utilization: number;
    oldestEntry: number | null;
  } {
    let oldestTimestamp: number | null = null;

    for (const entry of this.cache.values()) {
      if (oldestTimestamp === null || entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
      }
    }

    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      utilization: this.cache.size / this.maxSize,
      oldestEntry: oldestTimestamp ? Date.now() - oldestTimestamp : null,
    };
  }

  private updateAccessOrder(key: string): void {
    this.accessOrder = this.accessOrder.filter(k => k !== key);
    this.accessOrder.push(key);
  }
}