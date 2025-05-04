/**
 * 階層型トレーサビリティモデル - スキーマ定義
 * 
 * このファイルは階層型トレーサビリティモデルのグラフデータベーススキーマを定義します。
 * - スキーマファイルの読み込み
 * - スキーマ定義実行
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

/**
 * 新しいスキーマ定義に基づくデータベーススキーマを作成する関数
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

/**
 * 旧スキーマとの互換性のためのレガシースキーマを作成する関数
 * 注: 過渡期にのみ使用。将来的には削除予定
 * @param conn データベース接続オブジェクト
 */
export async function createLegacySchema(conn: any): Promise<void> {
  // ノードテーブル
  await conn.query(`
    CREATE NODE TABLE LocationURI (
      uri_id STRING PRIMARY KEY,
      scheme STRING,
      authority STRING,
      path STRING,
      fragment STRING,
      query STRING
    )
  `);
  
  await conn.query(`
    CREATE NODE TABLE CodeEntity (
      persistent_id STRING PRIMARY KEY,
      name STRING,
      type STRING,
      signature STRING,
      complexity INT64,
      start_position INT64,
      end_position INT64
    )
  `);
  
  await conn.query(`
    CREATE NODE TABLE RequirementEntity (
      id STRING PRIMARY KEY,
      title STRING,
      description STRING,
      priority STRING,
      requirement_type STRING
    )
  `);
  
  // 旧エッジテーブル
  await conn.query(`
    CREATE REL TABLE HAS_LOCATION_URI (
      FROM CodeEntity TO LocationURI
    )
  `);
  
  await conn.query(`
    CREATE REL TABLE REQUIREMENT_HAS_LOCATION_URI (
      FROM RequirementEntity TO LocationURI
    )
  `);
  
  await conn.query(`
    CREATE REL TABLE IMPLEMENTS (
      FROM CodeEntity TO RequirementEntity,
      implementation_type STRING
    )
  `);
  
  await conn.query(`
    CREATE REL TABLE CONTAINS (
      FROM CodeEntity TO CodeEntity
    )
  `);
}

