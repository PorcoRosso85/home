/**
 * KuzuDB Deno Query Repository (最小構成)
 * 
 * Deno環境でKuzuDBクエリファイル読み込みのための最小限関数群
 */

import { existsSync } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { join, dirname } from "https://deno.land/std@0.224.0/path/mod.ts";

// 型定義
export type QueryResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
  available_queries?: string[];
};

// 定数
const QUERY_DIR = dirname(new URL(import.meta.url).pathname);
const DQL_DIR = join(QUERY_DIR, "../../dql");
const CYPHER_EXTENSION = ".cypher";

/**
 * クエリファイルを検索する
 */
export async function findQueryFile(queryName: string): Promise<[boolean, string]> {
  const searchPaths = [
    join(DQL_DIR, `${queryName}${CYPHER_EXTENSION}`),
    join(DQL_DIR, "validation", `${queryName}${CYPHER_EXTENSION}`)
  ];
  
  for (const path of searchPaths) {
    if (await existsSync(path)) {
      return [true, path];
    }
  }
  
  return [false, `クエリファイル '${queryName}' が見つかりませんでした`];
}
/**
 * クエリファイルの内容を読み込む
 */
export async function readQueryFile(filePath: string): Promise<QueryResult<string>> {
  if (!await existsSync(filePath)) {
    return { success: false, error: `ファイルが存在しません: ${filePath}` };
  }
  
  const content = await Deno.readTextFile(filePath).catch(() => null);
  
  if (content === null) {
    return { 
      success: false, 
      error: `クエリファイルの読み込みに失敗しました: ${filePath}` 
    };
  }
  
  return { success: true, data: content };
}