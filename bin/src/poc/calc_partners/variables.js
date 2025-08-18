/**
 * Variables - 環境変数と設定値
 * 
 * 環境変数の一元管理
 * デフォルト値は禁止、必須変数は明示的にエラー
 */

/**
 * 環境変数の取得
 * @returns {object} 環境変数オブジェクト
 */
export const getVariables = () => {
  return {
    // 現時点では環境変数なし
    // 将来的にはここに追加
    // NODE_ENV: process.env.NODE_ENV || throw new Error('NODE_ENV is required'),
  }
}