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
        const kuzuModule = await initKuzu()
        setKuzu(kuzuModule)
        
        // メモリ内DBで動作確認
        const db = new kuzuModule.Database()
        const conn = new kuzuModule.Connection(db)
        
        // テスト用のテーブル作成とクエリ
        await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))")
        await conn.query("CREATE (p:Person {name: 'Alice', age: 30})")
        
        const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age")
        const rows = await result.getAllObjects()
        
        console.log('[Kuzu] クエリ結果:', rows)
        setStatus(`動作確認OK: ${JSON.stringify(rows)}`)
        
        await result.close()
        await conn.close()
        await db.close()
        
        console.log('[Kuzu] 初期化完了')
      } catch (error) {
        console.error('[Kuzu] エラー:', error)
        setStatus(`エラー: ${error.message}`)
      }
    }
    
    init()
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Kuzu WASM 最小動作確認</h1>
      <p>ステータス: {status}</p>
      <p>コンソールログも確認してください (F12)</p>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)