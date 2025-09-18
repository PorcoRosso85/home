/**
 * 設定管理のテスト
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.218.0/assert/mod.ts";
import {
  DEFAULT_DB_MAX_SIZE,
  DEFAULT_CACHE_TTL,
  VALID_QUERY_TYPES,
  QUERY_FILE_EXTENSION,
  DEFAULT_QUERY_DIR,
  getKuzuPath,
  getCacheEnabled,
  getMaxCacheSize,
  getDebugMode,
  getDefaultConfig,
  mergeConfig,
} from "../shared/config.ts";

Deno.test("グローバル定数の確認", () => {
  // kuzu_pyと同じ値であることを確認
  assertEquals(DEFAULT_DB_MAX_SIZE, 1 << 30); // 1GB
  assertEquals(DEFAULT_DB_MAX_SIZE, 1073741824); // 1GB in bytes
  
  assertEquals(DEFAULT_CACHE_TTL, 3600);
  assertEquals(QUERY_FILE_EXTENSION, ".cypher");
  assertEquals(DEFAULT_QUERY_DIR, "./queries");
  
  // クエリタイプの確認
  assertEquals(VALID_QUERY_TYPES, ["dml", "dql", "auto"]);
});

Deno.test("環境変数の取得（デフォルト値）", () => {
  // 環境変数が設定されていない場合のデフォルト値を確認
  const origEnv = { ...Deno.env.toObject() };
  
  // 環境変数をクリア
  delete Deno.env.toObject()["KUZU_DB_PATH"];
  delete Deno.env.toObject()["KUZU_TS_CACHE_ENABLED"];
  delete Deno.env.toObject()["KUZU_TS_MAX_CACHE_SIZE"];
  delete Deno.env.toObject()["KUZU_TS_DEBUG"];
  
  // デフォルト値の確認
  const dbPath = getKuzuPath();
  assertExists(dbPath);
  assertEquals(dbPath.endsWith(".kuzu/default.db"), true);
  
  assertEquals(getCacheEnabled(), true);
  assertEquals(getMaxCacheSize(), 100);
  assertEquals(getDebugMode(), false);
  
  // 環境変数を復元
  Object.entries(origEnv).forEach(([key, value]) => {
    Deno.env.set(key, value);
  });
});

Deno.test("環境変数の取得（カスタム値）", () => {
  const origEnv = { ...Deno.env.toObject() };
  
  // カスタム値を設定
  Deno.env.set("KUZU_DB_PATH", "/custom/path/to/db");
  Deno.env.set("KUZU_TS_CACHE_ENABLED", "false");
  Deno.env.set("KUZU_TS_MAX_CACHE_SIZE", "200");
  Deno.env.set("KUZU_TS_DEBUG", "true");
  
  // カスタム値の確認
  assertEquals(getKuzuPath(), "/custom/path/to/db");
  assertEquals(getCacheEnabled(), false);
  assertEquals(getMaxCacheSize(), 200);
  assertEquals(getDebugMode(), true);
  
  // 環境変数を復元
  Object.entries(origEnv).forEach(([key, value]) => {
    Deno.env.set(key, value);
  });
});

Deno.test("デフォルト設定の取得", () => {
  const config = getDefaultConfig();
  
  assertExists(config.dbPath);
  assertEquals(config.maxDbSize, DEFAULT_DB_MAX_SIZE);
  assertEquals(config.cacheEnabled, getCacheEnabled());
  assertEquals(config.maxCacheSize, getMaxCacheSize());
  assertEquals(config.debugMode, getDebugMode());
  assertEquals(config.cacheTTL, DEFAULT_CACHE_TTL);
});

Deno.test("設定のマージ", () => {
  // 部分的な設定でマージ
  const customConfig = {
    maxDbSize: 2 << 30, // 2GB
    debugMode: true,
  };
  
  const merged = mergeConfig(customConfig);
  
  // カスタム値が適用されていることを確認
  assertEquals(merged.maxDbSize, 2 << 30);
  assertEquals(merged.debugMode, true);
  
  // その他の値はデフォルトのまま
  assertExists(merged.dbPath);
  assertEquals(merged.cacheEnabled, getCacheEnabled());
  assertEquals(merged.maxCacheSize, getMaxCacheSize());
  assertEquals(merged.cacheTTL, DEFAULT_CACHE_TTL);
});

Deno.test("設定のマージ（空の設定）", () => {
  // 空の設定でマージ
  const merged = mergeConfig();
  const defaultConfig = getDefaultConfig();
  
  // すべてデフォルト値になることを確認
  assertEquals(merged.dbPath, defaultConfig.dbPath);
  assertEquals(merged.maxDbSize, defaultConfig.maxDbSize);
  assertEquals(merged.cacheEnabled, defaultConfig.cacheEnabled);
  assertEquals(merged.maxCacheSize, defaultConfig.maxCacheSize);
  assertEquals(merged.debugMode, defaultConfig.debugMode);
  assertEquals(merged.cacheTTL, defaultConfig.cacheTTL);
});