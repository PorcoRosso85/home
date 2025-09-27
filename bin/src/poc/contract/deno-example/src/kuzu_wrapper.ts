import { createDatabase, createConnection } from "../../../persistence/kuzu_ts/core/database.ts";
import { log } from "../../../log/mod.ts";
import { applyDdl } from "./kuzu_integration.ts";

export interface Database {
  query(cypher: string, params?: any): Promise<any[]>;
  execute(cypher: string): Promise<void>;
}

class KuzuDatabase implements Database {
  private conn: any;

  constructor(connection: any) {
    this.conn = connection;
  }

  async query(cypher: string, params?: any): Promise<any[]> {
    try {
      log("DEBUG", {
        uri: "contract.kuzu_wrapper.query",
        message: "Executing query",
        query: cypher,
        params: params
      });

      // conn.queryを使用（usage_example_test.tsの通り）
      const result = await this.conn.query(cypher, params);
      
      // 結果取得
      if (result && typeof result.getAll === 'function') {
        return await result.getAll();
      }
      
      // DDL文など結果がない場合は空配列を返す
      return [];
    } catch (error) {
      log("ERROR", {
        uri: "contract.kuzu_wrapper.query",
        message: "Query execution failed",
        error: error instanceof Error ? error.message : String(error),
        query: cypher
      });
      throw error;
    }
  }

  async execute(cypher: string): Promise<void> {
    try {
      // DDL実行もconn.queryを使用
      await this.conn.query(cypher);
    } catch (error) {
      log("ERROR", {
        uri: "contract.kuzu_wrapper.execute",
        message: "Statement execution failed",
        error: error instanceof Error ? error.message : String(error),
        statement: cypher.substring(0, 100)
      });
      throw error;
    }
  }
}

export async function initDatabase(): Promise<Database> {
  try {
    // In-memoryデータベースを作成（テスト用に一意のインスタンス）
    const db = await createDatabase(":memory:", { testUnique: true });
    const conn = await createConnection(db);
    
    // スキーマを適用
    const kuzuDb = new KuzuDatabase(conn);
    await applyDdl(kuzuDb, "ddl/contract_schema.cypher");
    
    log("INFO", {
      uri: "contract.kuzu_wrapper.initDatabase",
      message: "KuzuDB initialized successfully"
    });
    
    return kuzuDb;
  } catch (error) {
    log("ERROR", {
      uri: "contract.kuzu_wrapper.initDatabase",
      message: "Failed to initialize KuzuDB",
      error: error instanceof Error ? error.message : String(error)
    });
    throw error;
  }
}