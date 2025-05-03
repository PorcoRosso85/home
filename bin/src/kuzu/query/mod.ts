#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル 基本モジュール
 */

// 型定義
export interface LocationURI {
  uri_id: string;
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
}

export interface CodeEntity {
  persistent_id: string;
  name: string;
  type: string;
  signature: string;
  complexity: number;
  start_position: number;
  end_position: number;
}

export interface RequirementEntity {
  id: string;
  title: string;
  description: string;
  priority: string;
  requirement_type: string;
}

// KuzuDBモジュールをロード
export async function loadKuzuModule() {
  try {
    console.log("KuzuDBモジュールをロード試行中...");
    const module = await import("kuzu");
    return module;
  } catch (error) {
    console.error("KuzuDBモジュールのロード失敗:", error);
    return null;
  }
}

// ディレクトリ存在確認・作成
export async function ensureDir(dir: string): Promise<void> {
  try {
    const stat = await Deno.stat(dir);
    if (!stat.isDirectory) {
      throw new Error(`${dir}はディレクトリではありません`);
    }
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      console.log(`${dir}ディレクトリを作成します`);
      await Deno.mkdir(dir, { recursive: true });
    } else {
      throw error;
    }
  }
}
