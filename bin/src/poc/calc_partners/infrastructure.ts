/**
 * Infrastructure Layer - 外部システムとの接続
 * Kuzu WASM関連の処理
 */

import initKuzu from 'kuzu-wasm'
import type { KuzuDatabase, KuzuConnection, KuzuModule } from 'kuzu-wasm'
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
  
  // Kuzu WASM 0.7.0の公式API: result.table.toString()
  // 注意: APIドキュメントのgetAllRows/getAllObjectsは実際には存在しない
  // NPM READMEのサンプルコードが正しい
  // DDL文（CREATE/DROP等）はtableを返さない場合がある
  let resultJson: any[]
  if (result && result.table) {
    resultJson = JSON.parse(result.table.toString()) as any[]
  } else {
    // DDL文など結果セットがない場合は空配列を返す
    resultJson = []
  }
  
  // closeメソッドが存在する場合のみ実行
  if (result && typeof result.close === 'function') {
    await result.close()
  }
  
  log('INFO', {
    uri: '/infrastructure/kuzu',
    message: 'Query executed successfully',
    resultCount: resultJson.length
  })
  
  return resultJson
}