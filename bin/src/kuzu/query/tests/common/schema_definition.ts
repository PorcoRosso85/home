/**
 * 階層型トレーサビリティモデル - スキーマ定義
 * 
 * このファイルは階層型トレーサビリティモデルのグラフデータベーススキーマを定義します。
 * - スキーマファイルの読み込み
 * - スキーマ定義実行
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

/**
 * スキーマ定義ファイルに基づくデータベーススキーマを作成する関数
 * @param conn データベース接続オブジェクト
 */
export async function createSchema(conn: any): Promise<void> {
  console.log("スキーマ定義ファイルを読み込み中...");
  
  // スキーマ定義ファイルのパス
  const schemaFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/ddl/schema.cypher");
  
  try {
    // ファイルを読み込む
    const schemaContent = await Deno.readTextFile(schemaFilePath);
    
    // 各クエリを実行
    const queries = schemaContent.split(";").filter(q => q.trim() !== "");
    
    console.log(`スキーマ定義クエリを実行中... (${queries.length}個のクエリ)`);
    
    for (const query of queries) {
      try {
        await conn.query(query);
      } catch (error) {
        console.error(`クエリ実行エラー: ${query.trim()}`);
        console.error(`エラー詳細: ${error.message}`);
        throw error;
      }
    }
    
    console.log("スキーマ定義を完了しました");
  } catch (error) {
    console.error(`スキーマ定義ファイルの読み込みまたは実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

