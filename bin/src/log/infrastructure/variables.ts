// ログシステムの最小構成設定

// データベースのパス（カレントディレクトリを使用）
export const DB_PATH = "./logs.db";

// バリデーションルール
export const VALIDATION_RULES = {
  // 将来的なバリデーションルールを追加するための枠組み
  MAX_QUERY_LENGTH: 10000,
  BLACKLISTED_STATEMENTS: [
    "DROP TABLE",
    "DROP DATABASE",
    "DELETE FROM",
    "TRUNCATE TABLE"
  ]
};
