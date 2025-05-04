/**
 * 階層型トレーサビリティモデル - テストデータ生成
 * 
 * このファイルはテスト用のサンプルデータ生成を提供します。
 * - 基本サンプルデータファイルの読み込み
 * - 拡張サンプルデータファイルの読み込み
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

/**
 * Cypherファイルからクエリを実行する共通関数
 * @param conn データベース接続オブジェクト
 * @param filePath Cypherファイルのパス
 */
async function executeCypherFile(conn: any, filePath: string): Promise<void> {
  try {
    console.log(`Cypherファイルを読み込み中: ${filePath}`);
    
    // ファイルを読み込む
    const content = await Deno.readTextFile(filePath);
    
    // 各クエリを実行
    // コメントを除去し、セミコロンで分割して、空のクエリを除去
    const queries = content
      .split("\n")
      .filter(line => !line.trim().startsWith("//")) // コメント行を除去
      .join("\n")
      .split(";")
      .map(q => q.trim())
      .filter(q => q !== "");
    
    console.log(`クエリを実行中... (${queries.length}個のクエリ)`);
    
    for (const query of queries) {
      try {
        await conn.query(query);
      } catch (error) {
        console.error(`クエリ実行エラー: ${query}`);
        console.error(`エラー詳細: ${error.message}`);
        throw error;
      }
    }
    
    console.log(`Cypherファイルの実行が完了しました: ${filePath}`);
  } catch (error) {
    console.error(`Cypherファイルの読み込みまたは実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

/**
 * 基本サンプルデータを挿入する関数
 * @param conn データベース接続オブジェクト 
 */
export async function insertSampleData(conn: any): Promise<void> {
  console.log("基本サンプルデータを挿入中...");
  
  // Cypherクエリファイルのパス
  const dataFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/dml/sample_data.cypher");
  const relationshipsFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/dml/sample_relationships.cypher");
  
  // データノードの作成
  await executeCypherFile(conn, dataFilePath);
  
  // 関係の作成
  await executeCypherFile(conn, relationshipsFilePath);
  
  console.log("基本サンプルデータの挿入が完了しました");
}

/**
 * 拡張サンプルデータを挿入する関数
 * @param conn データベース接続オブジェクト
 */
export async function insertExtendedSampleData(conn: any): Promise<void> {
  // まず基本データを挿入
  await insertSampleData(conn);
  
  console.log("拡張サンプルデータを挿入中...");
  
  // 拡張データのCypherファイルパス
  const extendedDataFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/dml/extended_sample_data.cypher");
  
  // 拡張データを実行
  await executeCypherFile(conn, extendedDataFilePath);
  
  console.log("拡張サンプルデータの挿入が完了しました");
}

/**
 * レガシーデータを挿入する関数
 * 旧スキーマとの互換性のために使用
 * @param conn データベース接続オブジェクト
 */
export async function insertLegacySampleData(conn: any): Promise<void> {
  console.log("レガシーサンプルデータを挿入中...");
  
  // レガシーデータのCypherファイルパス
  const legacyDataFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/dml/legacy/legacy_data.cypher");
  const legacyRelationshipsFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/dml/legacy/legacy_relationships.cypher");
  
  // データノードの作成
  await executeCypherFile(conn, legacyDataFilePath);
  
  // 関係の作成
  await executeCypherFile(conn, legacyRelationshipsFilePath);
  
  console.log("レガシーサンプルデータの挿入が完了しました");
}
