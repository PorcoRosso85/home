/**
 * Domain Layer - ビジネスロジックと計算ロジック
 * 純粋関数のみ、外部依存なし
 */

/**
 * Ping応答の行データ型
 */
interface PingResponseRow {
  response: string;
  status: number;
}

/**
 * クエリ結果の型定義
 */
type QueryResultData = PingResponseRow[];

/**
 * ping応答の検証
 * @param result - クエリ実行結果
 * @returns 正常な応答かどうか
 */
export const validatePingResponse = (result: QueryResultData | null | undefined): result is QueryResultData => {
  if (!result || !Array.isArray(result)) return false;
  if (result.length !== 1) return false;
  
  const row = result[0];
  return row !== undefined && row.response === 'pong' && row.status === 1;
};

/**
 * 結果のフォーマット
 * @param result - クエリ実行結果
 * @returns 表示用文字列
 */
export const formatPingResult = (result: QueryResultData | null | undefined): string => {
  return JSON.stringify(result);
};