import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import initKuzu, { KuzuModule, KuzuDatabase, KuzuConnection, KuzuQueryResult } from '@kuzu/kuzu-wasm'

function App(): JSX.Element {
  const [status, setStatus] = useState<string>('初期化中...')
  const [kuzu, setKuzu] = useState<KuzuModule | null>(null)

  useEffect(() => {
    const init = async (): Promise<void> => {
      try {
        console.log('[Kuzu] 初期化開始')
        const kuzu: KuzuModule = await initKuzu()
        setKuzu(kuzu)
        
        // 公式READMEの例に従う（awaitを使用）
        const db: KuzuDatabase = await kuzu.Database()  // メモリDB（引数なし）
        const conn: KuzuConnection = await kuzu.Connection(db)
        
        // ping.cypherの内容を実行
        // queries/dql/ping.cypher: RETURN 'pong' AS response, 1 AS status
        const pingQuery: string = "RETURN 'pong' AS response, 1 AS status"
        
        console.log('[Kuzu] ping.cypherクエリ実行:', pingQuery)
        
        // 公式READMEではexecuteメソッドを使用
        const result: KuzuQueryResult = await conn.execute(pingQuery)
        console.log('[Kuzu] クエリ結果:', result)
        
        // 結果をJSONに変換（公式READMEの方法）
        const resultJson: unknown = JSON.parse(result.table.toString())
        console.log('[Kuzu] 結果JSON:', JSON.stringify(resultJson))
        
        console.log('[Kuzu] ping応答:', resultJson)
        setStatus(`ping確認OK: ${JSON.stringify(resultJson)}`)
        
        await result.close()
        await conn.close()
        await db.close()
        
        console.log('[Kuzu] 初期化完了')
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        const errorStack = error instanceof Error ? error.stack : undefined
        
        console.error('[Kuzu] エラー:', error)
        console.error('[Kuzu] スタック:', errorStack)
        setStatus(`エラー: ${errorMessage}`)
      }
    }
    
    init()
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Kuzu WASM ping確認</h1>
      <p>ステータス: {status}</p>
      <p>実行クエリ: queries/dql/ping.cypher</p>
      <p>コンソールログも確認してください (F12)</p>
    </div>
  )
}

const rootElement = document.getElementById('root')
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(<App />)
}