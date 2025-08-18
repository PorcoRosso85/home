import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import initKuzu from '@kuzu/kuzu-wasm'

function App() {
  const [status, setStatus] = useState('初期化中...')
  const [kuzu, setKuzu] = useState(null)

  useEffect(() => {
    const init = async () => {
      try {
        console.log('[Kuzu] 初期化開始')
        const kuzu = await initKuzu()
        setKuzu(kuzu)
        
        // 公式READMEの例に従う（awaitを使用）
        const db = await kuzu.Database()  // メモリDB（引数なし）
        const conn = await kuzu.Connection(db)
        
        // ping.cypherの内容を実行
        // queries/dql/ping.cypher: RETURN 'pong' AS response, 1 AS status
        const pingQuery = "RETURN 'pong' AS response, 1 AS status"
        
        console.log('[Kuzu] ping.cypherクエリ実行:', pingQuery)
        
        // 公式READMEではexecuteメソッドを使用
        const result = await conn.execute(pingQuery)
        console.log('[Kuzu] クエリ結果:', result)
        
        // 結果をJSONに変換（公式READMEの方法）
        const resultJson = JSON.parse(result.table.toString())
        console.log('[Kuzu] 結果JSON:', JSON.stringify(resultJson))
        
        console.log('[Kuzu] ping応答:', resultJson)
        setStatus(`ping確認OK: ${JSON.stringify(resultJson)}`)
        
        await result.close()
        await conn.close()
        await db.close()
        
        console.log('[Kuzu] 初期化完了')
      } catch (error) {
        console.error('[Kuzu] エラー:', error)
        console.error('[Kuzu] スタック:', error.stack)
        setStatus(`エラー: ${error.message}`)
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

ReactDOM.createRoot(document.getElementById('root')).render(<App />)