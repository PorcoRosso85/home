/**
 * Infrastructure Layer - 外部システムとの接続
 * Kuzu WASM関連の処理
 */

import initKuzu from '@kuzu/kuzu-wasm'

/**
 * Kuzu WASMの初期化と接続の確立
 * @returns {Promise<{db: object, conn: object, close: function}>}
 */
export const initializeKuzu = async () => {
  console.log('[Infrastructure] Kuzu初期化開始')
  
  const kuzu = await initKuzu()
  const db = await kuzu.Database()  // メモリDB（引数なし）
  const conn = await kuzu.Connection(db)
  
  console.log('[Infrastructure] Kuzu初期化完了')
  
  // クリーンアップ関数を含むオブジェクトを返す
  return {
    db,
    conn,
    close: async () => {
      await conn.close()
      await db.close()
    }
  }
}

/**
 * Cypherクエリの実行
 * @param {object} conn - Kuzu接続オブジェクト
 * @param {string} query - 実行するCypherクエリ
 * @returns {Promise<array>} クエリ結果の配列
 */
export const executeQuery = async (conn, query) => {
  console.log('[Infrastructure] クエリ実行:', query)
  
  const result = await conn.execute(query)
  const resultJson = JSON.parse(result.table.toString())
  
  await result.close()
  
  console.log('[Infrastructure] クエリ結果:', resultJson)
  return resultJson
}