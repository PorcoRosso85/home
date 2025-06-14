/**
 * ドメインエラー型定義
 * ビジネスロジックに関連するエラーを定義
 */

export type DomainError = 
  | { code: "INVALID_QUERY"; message: string }
  | { code: "TABLE_NOT_FOUND"; message: string; table: string }
  | { code: "PERMISSION_DENIED"; message: string; resource: string }
  | { code: "INVALID_SYNTAX"; message: string; query: string }
  | { code: "CONSTRAINT_VIOLATION"; message: string; constraint: string };

// エラーヘルプメッセージ
export function getDomainErrorHelp(code: string): string {
  const errorHelp: Record<string, string> = {
    "INVALID_QUERY": "クエリが無効です。SQL構文を確認してください。",
    "TABLE_NOT_FOUND": "指定されたテーブルが見つかりません。カタログ名とテーブル名を確認してください。",
    "PERMISSION_DENIED": "リソースへのアクセス権限がありません。",
    "INVALID_SYNTAX": "SQL構文エラーです。DuckDBのドキュメントを参照してください。",
    "CONSTRAINT_VIOLATION": "制約違反が発生しました。データの整合性を確認してください。"
  };
  return errorHelp[code] || "不明なドメインエラーが発生しました。";
}
