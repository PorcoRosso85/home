/**
 * LocationURIデータのキャッシュ管理関数群
 * 
 * TODO: クラスではなく関数として実装
 */

import { LocationURI } from '../../domain/types';

// キャッシュエントリの型定義
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

// キャッシュの保持期間（5分 = 300000ミリ秒）
const DEFAULT_CACHE_TTL = 300000;

// キャッシュストレージ
const cacheStorage = new Map<string, CacheEntry<any>>();

/**
 * キャッシュにデータを保存する
 */
export function setCache<T>(
  key: string, 
  data: T, 
  ttl: number = DEFAULT_CACHE_TTL
): void {
  const now = Date.now();
  cacheStorage.set(key, {
    data,
    timestamp: now,
    expiresAt: now + ttl
  });
}

/**
 * キャッシュからデータを取得する
 * 期限切れの場合はundefinedを返す
 */
export function getCache<T>(key: string): T | undefined {
  const entry = cacheStorage.get(key) as CacheEntry<T> | undefined;
  
  if (!entry) {
    return undefined;
  }
  
  // 期限切れかどうかチェック
  const now = Date.now();
  if (now > entry.expiresAt) {
    // 期限切れの場合は削除して未定義を返す
    cacheStorage.delete(key);
    return undefined;
  }
  
  return entry.data;
}

/**
 * キャッシュからデータを削除する
 */
export function deleteCache(key: string): void {
  cacheStorage.delete(key);
}

/**
 * すべてのキャッシュをクリアする
 */
export function clearAllCache(): void {
  cacheStorage.clear();
}

/**
 * 期限切れのキャッシュをすべて削除する
 */
export function cleanExpiredCache(): void {
  const now = Date.now();
  
  cacheStorage.forEach((entry, key) => {
    if (now > entry.expiresAt) {
      cacheStorage.delete(key);
    }
  });
}

/**
 * バージョンIDに基づくLocationURIキャッシュのキーを生成する
 */
export function createVersionUriCacheKey(versionId: string): string {
  return `version_uris_${versionId}`;
}

/**
 * バージョンのLocationURIデータをキャッシュから取得する
 */
export function getCachedLocationUris(versionId: string): LocationURI[] | undefined {
  const key = createVersionUriCacheKey(versionId);
  return getCache<LocationURI[]>(key);
}

/**
 * バージョンのLocationURIデータをキャッシュに保存する
 */
export function cacheLocationUris(
  versionId: string, 
  uris: LocationURI[], 
  ttl: number = DEFAULT_CACHE_TTL
): void {
  const key = createVersionUriCacheKey(versionId);
  setCache<LocationURI[]>(key, uris, ttl);
}

/**
 * 特定のバージョンのキャッシュを無効化する
 */
export function invalidateVersionCache(versionId: string): void {
  const key = createVersionUriCacheKey(versionId);
  deleteCache(key);
}
