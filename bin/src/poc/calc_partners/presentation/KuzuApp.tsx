import React, { useEffect, useState } from 'react'
import { initializeDatabase, executeQueryWithConnection } from '../infrastructure/index.js'
import type { Database, Connection } from '../infrastructure/index.js'

/**
 * Presentation Layer Component
 * Uses infrastructure layer abstractions, not direct kuzu-wasm dependency
 */
export function KuzuApp(): JSX.Element {
  const [status, setStatus] = useState<string>('初期化中...')
  const [connection, setConnection] = useState<Connection | null>(null)

  useEffect(() => {
    const init = async (): Promise<void> => {
      try {
        console.log('[Kuzu] 初期化開始')
        
        // Use infrastructure layer abstraction
        const { db, conn } = await initializeDatabase()
        setConnection(conn)
        
        // Execute ping query
        const pingQuery = "RETURN 'pong' AS response, 1 AS status"
        console.log('[Kuzu] ping.cypherクエリ実行:', pingQuery)
        
        const resultJson = await executeQueryWithConnection(conn, pingQuery)
        console.log('[Kuzu] 結果JSON:', JSON.stringify(resultJson))
        
        setStatus(`ping確認OK: ${JSON.stringify(resultJson)}`)
        console.log('[Kuzu] 初期化完了')
        
        // Cleanup
        await conn.close()
        await db.close()
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error('[Kuzu] エラー:', error)
        setStatus(`エラー: ${errorMessage}`)
      }
    }

    init()
  }, [])

  return (
    <div>
      <h1>Kuzu WASM Test</h1>
      <p>ステータス: {status}</p>
    </div>
  )
}

export default KuzuApp