/**
 * クエリ実行結果の型定義
 * CONVENTION.yaml準拠: パターンマッチ優先のTagged Union
 */

// クエリ実行結果の詳細型（パターンマッチ対応）
export type QueryExecutionResult = 
  | { status: "success"; data: any }
  | { status: "validation_error"; field: string; message: string }
  | { status: "execution_error"; code: string; message: string }
  | { status: "connection_error"; message: string }
  | { status: "not_found"; resource: string };

// データベース接続結果
export type DatabaseConnectionResult =
  | { status: "connected"; connection: any }
  | { status: "connection_failed"; code: string; message: string }
  | { status: "invalid_config"; field: string; message: string };

// データ変換結果
export type DataTransformResult =
  | { status: "transformed"; data: any }
  | { status: "transform_error"; operation: string; message: string }
  | { status: "validation_failed"; field: string; message: string };
