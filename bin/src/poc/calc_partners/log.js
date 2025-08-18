/**
 * 構造化ログ出力（規約準拠）
 * logging.md準拠の簡易実装
 */

/**
 * 構造化ログ出力
 * @param {string} level - ログレベル (INFO, ERROR, WARN, DEBUG, METRIC)
 * @param {object} data - ログデータ（uri, message必須）
 */
export const log = (level, data) => {
  // 必須フィールドチェック
  if (!data.uri || !data.message) {
    console.error('Log error: uri and message are required')
    return
  }
  
  // JSONL形式で標準出力
  const logEntry = {
    level,
    timestamp: new Date().toISOString(),
    ...data
  }
  
  // 本番環境では構造化ログ、開発環境では読みやすい形式
  if (process.env.NODE_ENV === 'production') {
    console.log(JSON.stringify(logEntry))
  } else {
    // 開発環境用の読みやすい出力
    const prefix = {
      ERROR: '❌',
      WARN: '⚠️',
      INFO: '📝',
      DEBUG: '🔍',
      METRIC: '📊'
    }[level] || '📝'
    
    console.log(`${prefix} [${level}] ${data.message}`)
    if (level === 'ERROR' && data.error) {
      console.error('  Details:', data.error)
    }
  }
}