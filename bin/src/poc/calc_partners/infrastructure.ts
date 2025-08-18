/**
 * Infrastructure Layer - 外部システムとの接続
 * Kuzu WASM関連の処理
 */

import initKuzu from '@kuzu/kuzu-wasm'
import type { KuzuDatabase, KuzuConnection, KuzuModule } from '@kuzu/kuzu-wasm'
import { log } from './log.js'

/**
 * Kuzu接続情報を格納するインターフェース
 */
export interface KuzuConnectionInfo {
  db: KuzuDatabase
  conn: KuzuConnection
  close: () => Promise<void>
}

/**
 * Kuzu WASMの初期化と接続の確立
 * @returns {Promise<KuzuConnectionInfo>}
 */
export const initializeKuzu = async (): Promise<KuzuConnectionInfo> => {
  log('INFO', {
    uri: '/infrastructure/kuzu',
    message: 'Kuzu初期化開始'
  })
  
  const kuzu: KuzuModule = await initKuzu()
  const db = await kuzu.Database()  // メモリDB（引数なし）
  const conn = await kuzu.Connection(db)
  
  log('INFO', {
    uri: '/infrastructure/kuzu',
    message: 'Kuzu初期化完了'
  })
  
  // クリーンアップ関数を含むオブジェクトを返す
  return {
    db,
    conn,
    close: async (): Promise<void> => {
      await conn.close()
      await db.close()
    }
  }
}

/**
 * Cypherクエリの実行
 * @param {KuzuConnection} conn - Kuzu接続オブジェクト
 * @param {string} query - 実行するCypherクエリ
 * @returns {Promise<any[]>} クエリ結果の配列
 */
export const executeQuery = async (conn: KuzuConnection, query: string): Promise<any[]> => {
  log('INFO', {
    uri: '/infrastructure/kuzu',
    message: 'Executing query',
    query: query.substring(0, 100) // 最初の100文字のみログ
  })
  
  const result = await conn.execute(query)
  const resultJson = JSON.parse(result.table.toString()) as any[]
  
  await result.close()
  
  log('INFO', {
    uri: '/infrastructure/kuzu',
    message: 'Query executed successfully',
    resultCount: resultJson.length
  })
  
  return resultJson
}