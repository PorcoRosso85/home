/**
 * KuzuDBのデータベース接続テスト - DDL/DML/DQLのみの最小構成
 */

import { createDatabase, closeConnection } from "../services/databaseService.ts";
import { dirname, join } from "https://deno.land/std@0.177.0/path/mod.ts";

// 現在のファイルのディレクトリパスを取得
const getCurrentDirectory = () => {
  const fileUrl = import.meta.url;
  const filePath = new URL(fileUrl).pathname;
  return dirname(filePath);
};

// ファイルコンテンツを読み込む関数
const readFileContent = async (filePath: string): Promise<string> => {
  try {
    const content = await Deno.readTextFile(filePath);
    return content;
  } catch (error) {
    console.error(`ファイル読み込みエラー (${filePath}): ${error.message}`);
    throw error;
  }
};

async function main() {
  console.log("KuzuDBテスト開始");
  
  let connection = null;
  
  try {
    // データベース接続を設定
    connection = await createDatabase("test_connection");
    const { db, conn } = connection;
    
    // 各クエリファイルのパスを取得
    const currentDir = getCurrentDirectory();
    const schemaFile = join(currentDir, "ddl", "schema.cypher");
    const dmlFiles = [];
    const dqlFiles = [];
    
    try {
      // DMLディレクトリ内のファイルを検索
      for (const entry of Deno.readDirSync(join(currentDir, "dml"))) {
        if (entry.isFile && entry.name.endsWith(".cypher")) {
          dmlFiles.push(join(currentDir, "dml", entry.name));
        }
      }
      
      // DQLディレクトリ内のファイルを検索
      for (const entry of Deno.readDirSync(join(currentDir, "dql"))) {
        if (entry.isFile && entry.name.endsWith(".cypher")) {
          dqlFiles.push(join(currentDir, "dql", entry.name));
        }
      }
    } catch (e) {
      console.log(`ディレクトリ検索中のエラー (無視): ${e.message}`);
    }
    
    console.log(`見つかったファイル: DDL=${schemaFile.split('/').pop() || 'なし'}, DML=${dmlFiles.length}個, DQL=${dqlFiles.length}個`);
    
    // スキーマ(DDL)を適用
    console.log("スキーマ定義を実行");
    try {
      const schemaContent = await readFileContent(schemaFile);
      
      // セミコロンで分割し、空でないクエリを実行
      const queries = schemaContent
        .split(";")
        .map(q => q.trim())
        .filter(q => q !== "");
      
      for (const query of queries) {
        if (query) {
          console.log(`スキーマクエリを実行: ${query.substring(0, 50)}${query.length > 50 ? '...' : ''}`);
          await conn.query(query);
        }
      }
      console.log("スキーマ定義の適用が完了しました");
    } catch (schemaError) {
      console.error("スキーマ定義の適用に失敗しました:", schemaError);
    }
    
    // DMLファイルを実行
    if (dmlFiles.length > 0) {
      console.log("DMLファイルを実行");
      for (const dmlFile of dmlFiles) {
        try {
          console.log(`DMLファイルを実行: ${dmlFile.split('/').pop()}`);
          const dmlContent = await readFileContent(dmlFile);
          
          // セミコロンで分割し、空でないクエリを実行
          const queries = dmlContent
            .split(";")
            .map(q => q.trim())
            .filter(q => q !== "");
          
          for (const query of queries) {
            if (query) {
              console.log(`DMLクエリを実行: ${query.substring(0, 50)}${query.length > 50 ? '...' : ''}`);
              await conn.query(query);
            }
          }
        } catch (dmlError) {
          console.error(`DMLファイル実行エラー (${dmlFile.split('/').pop()}):`, dmlError);
        }
      }
    }
    
    // DQLファイルを実行
    if (dqlFiles.length > 0) {
      console.log("DQLファイルを実行");
      for (const dqlFile of dqlFiles) {
        try {
          console.log(`DQLファイルを実行: ${dqlFile.split('/').pop()}`);
          const dqlContent = await readFileContent(dqlFile);
          
          // セミコロンで分割し、空でないクエリを実行
          const queries = dqlContent
            .split(";")
            .map(q => q.trim())
            .filter(q => q !== "");
          
          for (const query of queries) {
            if (query) {
              console.log(`DQLクエリを実行: ${query.substring(0, 50)}${query.length > 50 ? '...' : ''}`);
              const result = await conn.query(query);
              
              // 結果を表示
              console.log(`クエリ結果:`, await result.getAllObjects());
            }
          }
        } catch (dqlError) {
          console.error(`DQLファイル実行エラー (${dqlFile.split('/').pop()}):`, dqlError);
        }
      }
    }
    
    // データベース接続をクローズ
    await closeConnection(connection);
    console.log("テスト完了");
  } catch (error) {
    console.error("エラー:", error);
    
    // エラー発生時も接続をクローズ
    if (connection) {
      try {
        await closeConnection(connection);
      } catch (closeError) {
        console.error("クローズ中にエラー:", closeError);
      }
    }
    
    Deno.exit(1);
  }
}

// メイン関数を実行
if (import.meta.main) {
  await main();
}

export { main };
