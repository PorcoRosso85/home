/**
 * Domain Layer - ビジネスロジックと計算ロジック
 * 純粋関数のみ、外部依存なし
 */

/**
 * pingクエリの生成
 * @returns {string} Cypherクエリ文字列
 */
export const createPingQuery = () => {
  return "RETURN 'pong' AS response, 1 AS status"
}

/**
 * ping応答の検証
 * @param {object} result - クエリ実行結果
 * @returns {boolean} 正常な応答かどうか
 */
export const validatePingResponse = (result) => {
  if (!result || !Array.isArray(result)) return false
  if (result.length !== 1) return false
  
  const row = result[0]
  return row.response === 'pong' && row.status === 1
}

/**
 * 結果のフォーマット
 * @param {object} result - クエリ実行結果
 * @returns {string} 表示用文字列
 */
export const formatPingResult = (result) => {
  return JSON.stringify(result)
}