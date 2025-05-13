import { DuckDBInstance } from "npm:@duckdb/node-api";
import { LogRow } from "../domain/entities.ts";
import { SqlRepository, Result, SqlError } from "../domain/repository.ts";
import { DB_PATH, VALIDATION_RULES } from "./variables.ts";

// SQLクエリのバリデーション
const validateQuery = (sql: string): Result<void> => {
  // クエリの長さをチェック
  if (sql.length > VALIDATION_RULES.MAX_QUERY_LENGTH) {
    return {
      ok: false,
      error: {
        code: "QUERY_TOO_LONG",
        message: `クエリが長すぎます (${sql.length} > ${VALIDATION_RULES.MAX_QUERY_LENGTH})`,
      }
    };
  }
  
  // ブラックリストに含まれるステートメントをチェック
  const upperSql = sql.toUpperCase();
  for (const blacklisted of VALIDATION_RULES.BLACKLISTED_STATEMENTS) {
    if (upperSql.includes(blacklisted)) {
      return {
        ok: false,
        error: {
          code: "FORBIDDEN_STATEMENT",
          message: `禁止されたステートメントが含まれています: ${blacklisted}`,
        }
      };
    }
  }
  
  return { ok: true, value: undefined };
};

// DuckDBリポジトリの実装
export const createSqlRepository = (): SqlRepository => {
  return {
    async execute(sql: string, params: unknown[] = []): Promise<Result<LogRow[]>> {
      // SQLクエリをバリデーション
      const validationResult = validateQuery(sql);
      if (!validationResult.ok) {
        return validationResult;
      }
      
      try {
        // インスタンスとコネクションの作成
        const instance = await DuckDBInstance.create(DB_PATH);
        const connection = await instance.connect();
        
        try {
          // SQLクエリを実行
          let reader;
          if (params.length > 0) {
            // パラメータ付きクエリの場合はプリペアドステートメントを使用
            const prepared = await connection.prepare(sql);
            
            // パラメータをバインド
            for (let i = 0; i < params.length; i++) {
              const param = params[i];
              const index = i + 1; // パラメータインデックスは1から始まる
              
              if (typeof param === 'string') {
                prepared.bindVarchar(index, param);
              } else if (typeof param === 'number') {
                if (Number.isInteger(param)) {
                  prepared.bindInteger(index, param);
                } else {
                  prepared.bindDouble(index, param);
                }
              } else if (param === null || param === undefined) {
                prepared.bindNull(index);
              } else if (param instanceof Date) {
                prepared.bindTimestamp(index, param);
              } else {
                // オブジェクトなどはJSON文字列に変換
                prepared.bindVarchar(index, JSON.stringify(param));
              }
            }
            
            reader = await prepared.runAndReadAll();
          } else {
            // 単純なクエリの場合
            reader = await connection.runAndReadAll(sql);
          }
          
          // 結果をそのまま返す（最小限のフォーマット）
          const rows = reader.getRows();
          const columns = reader.getColumns();
          
          // デバッグ情報
          console.log("DuckDB カラム情報:", columns.map(c => `${c.name}:${c.typeId}`));
          
          return { ok: true, value: rows };
        } finally {
          // リソースの解放
          connection.closeSync();
          instance.closeSync();
        }
      } catch (err) {
        return {
          ok: false,
          error: {
            code: "SQL_ERROR",
            message: err instanceof Error ? err.message : String(err),
            cause: err
          }
        };
      }
    }
  };
};