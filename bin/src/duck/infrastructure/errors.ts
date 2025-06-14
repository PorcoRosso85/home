/**
 * インフラストラクチャエラー型定義
 * 技術的な問題に関連するエラーを定義
 */

export type InfrastructureError =
  | { code: "DB_CONNECTION_ERROR"; message: string }
  | { code: "FILE_SYSTEM_ERROR"; message: string; path: string }
  | { code: "NETWORK_ERROR"; message: string }
  | { code: "DUCKDB_EXECUTION_ERROR"; message: string; originalError: string }
  | { code: "FILE_NOT_FOUND"; message: string; filePath: string }
  | { code: "PERMISSION_ERROR"; message: string; operation: string };

// エラーヘルプメッセージ
export function getInfrastructureErrorHelp(code: string): string {
  const errorHelp: Record<string, string> = {
    "DB_CONNECTION_ERROR": "データベース接続エラーです。DuckDBインスタンスの状態を確認してください。",
    "FILE_SYSTEM_ERROR": "ファイルシステムエラーです。ディスク容量と権限を確認してください。",
    "NETWORK_ERROR": "ネットワークエラーです。接続状態を確認してください。",
    "DUCKDB_EXECUTION_ERROR": "DuckDBの実行エラーです。クエリログを確認してください。",
    "FILE_NOT_FOUND": "指定されたファイルが見つかりません。パスを確認してください。",
    "PERMISSION_ERROR": "権限エラーです。ファイルやディレクトリのアクセス権限を確認してください。"
  };
  return errorHelp[code] || "不明なインフラストラクチャエラーが発生しました。";
}
