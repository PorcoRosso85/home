/**
 * アプリケーションエラー型定義
 * ユースケースレベルのエラーを定義
 */

export type ApplicationError =
  | { code: "VALIDATION_FAILED"; message: string; details: any }
  | { code: "OPERATION_FAILED"; message: string; operation: string }
  | { code: "DUCKLAKE_NOT_AVAILABLE"; message: string }
  | { code: "CATALOG_CREATION_FAILED"; message: string; catalogName: string }
  | { code: "TEST_ENVIRONMENT_FAILED"; message: string; reason: string };

// エラーヘルプメッセージ
export function getApplicationErrorHelp(code: string): string {
  const errorHelp: Record<string, string> = {
    "VALIDATION_FAILED": "入力値の検証に失敗しました。パラメータを確認してください。",
    "OPERATION_FAILED": "操作の実行に失敗しました。ログを確認してください。",
    "DUCKLAKE_NOT_AVAILABLE": "DuckLake拡張が利用できません。INSTALL ducklake; LOAD ducklake; を実行してください。",
    "CATALOG_CREATION_FAILED": "カタログの作成に失敗しました。権限とパスを確認してください。",
    "TEST_ENVIRONMENT_FAILED": "テスト環境の構築に失敗しました。"
  };
  return errorHelp[code] || "不明なアプリケーションエラーが発生しました。";
}

// 実行例の提供
export function getApplicationCommandExamples(): string[] {
  return [
    "curl -X POST http://localhost:3000/query -H 'Content-Type: application/json' -d '{\"query\": \"SELECT version()\"}'",
    "curl -X POST http://localhost:3000/query -H 'Content-Type: application/json' -d '{\"query\": \"INSTALL ducklake; LOAD ducklake\"}'",
    "curl -X POST http://localhost:3000/query -H 'Content-Type: application/json' -d '{\"query\": \"ATTACH 'ducklake::memory:' AS lake\"}'",
  ];
}
