/**
 * Infrastructure Layer - 外部システムとの接続
 * Kuzu WASM関連の処理
 */

import kuzuWasm from 'kuzu-wasm'
import type { KuzuDatabase, KuzuConnection } from 'kuzu-wasm'
// Simple console logging
const log = console.log.bind(console)

// 環境判定
const isNode = typeof window === 'undefined'
const isBrowser = typeof window !== 'undefined'

log('INFO', {
  uri: '/infrastructure/kuzu',
  message: `環境判定: ${isNode ? 'Node.js' : 'Browser'}`,
  environment: {
    isNode,
    isBrowser,
    hasProcess: typeof process !== 'undefined',
    hasWindow: typeof window !== 'undefined'
  }
})

/**
 * Kuzu接続情報を格納する型定義
 */
export type KuzuConnectionInfo = {
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
  
  // kuzu-wasm 0.11.1では、init()を最初に呼び出す必要がある
  // ブラウザ環境ではWorkerが自動的に設定される
  await kuzuWasm.init()
  
  // その後Database/Connectionを作成（newキーワードが必要）
  const db = await new kuzuWasm.Database()  // メモリDB（引数なし）
  const conn = await new kuzuWasm.Connection(db)
  
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
 * @returns {Promise<Record<string, unknown>[]>} クエリ結果の配列
 */
export const executeQuery = async (conn: KuzuConnection, query: string): Promise<Record<string, unknown>[]> => {
  log('INFO', {
    uri: '/infrastructure/kuzu',
    message: 'Executing query',
    query: query.substring(0, 100) // 最初の100文字のみログ
  })
  
  // 公式exampleに従い、conn.query()を使用
  // Note: KuzuConnection型定義にquery()メソッドが不足しているため、型アサーションを使用
  const result = await (conn as unknown as { query: (q: string) => Promise<{ getAllObjects: () => Promise<Record<string, unknown>[]>, close?: () => Promise<void>, toString?: () => Promise<string> }> }).query(query)
  
  // getAllObjects()メソッドで結果を取得
  let resultJson: Record<string, unknown>[]
  if (result && typeof result.getAllObjects === 'function') {
    resultJson = await result.getAllObjects()
  } else if (result && typeof result.toString === 'function') {
    // フォールバック：toString()を使用
    const jsonString = await result.toString()
    try {
      resultJson = JSON.parse(jsonString)
    } catch {
      resultJson = []
    }
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

/**
 * Initialize database for presentation layer
 * Wraps initializeKuzu for backward compatibility
 */
export const initializeDatabase = async (): Promise<{ db: KuzuDatabase, conn: KuzuConnection }> => {
  const { db, conn } = await initializeKuzu()
  return { db, conn }
}

/**
 * Execute query with connection for presentation layer
 * Wraps executeQuery for backward compatibility
 */
export const executeQueryWithConnection = async (conn: KuzuConnection, query: string): Promise<Record<string, unknown>[]> => {
  return executeQuery(conn, query)
}