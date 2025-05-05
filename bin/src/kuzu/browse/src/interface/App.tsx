import React, { useState, useEffect } from 'react';
import { databaseService } from '../application/databaseService';

// 最小構成のKuzu-Wasmアプリケーション
const App = () => {
  // ステート
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  // シンプルなクエリ（スキーマ非依存）
  const [query, setQuery] = useState<string>('');
  
  // BigInt値を文字列に変換するヘルパー関数
  const jsonStringifyReplacer = (key, value) => {
    // BigInt型の値を文字列に変換
    if (typeof value === 'bigint') {
      return value.toString();
    }
    return value;
  };
  
  // クエリを実行する関数
  const executeQuery = async (queryString) => {
    try {
      setLoading(true);
      setError(null);
      
      // データベース接続がない場合は接続
      if (!window.conn) {
        const connectResult = await databaseService.connect();
        if (!connectResult.success) {
          setError(connectResult.error);
          return;
        }
      }
      
      // クエリを実行
      const queryResult = await window.conn.query(queryString);
      
      // 結果の変換
      let resultJson;
      if (queryResult.table) {
        const resultTable = queryResult.table.toString();
        resultJson = JSON.parse(resultTable);
      } else if (queryResult.getAllObjects) {
        resultJson = await queryResult.getAllObjects();
      } else {
        resultJson = queryResult;
      }
      
      setQuery(queryString);
      setResult(resultJson);
      
    } catch (err) {
      console.error('クエリ実行エラー:', err);
      setError(`クエリの実行に失敗しました: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 接続テスト - バージョン情報取得
  const checkConnection = async () => {
    const versionQuery = `RETURN 'Connection Test' as result`;
    await executeQuery(versionQuery);
  };
  
  // 全ノードIDを取得
  const fetchAllNodeIds = async () => {
    const nodeIdQuery = `
      MATCH (n)
      RETURN n
      LIMIT 1000
    `;
    await executeQuery(nodeIdQuery);
  };
  
  // テーブル一覧を取得
  const listTables = async () => {
    try {
      // 最も基本的なクエリを試す
      const tablesQuery = `MATCH (n) RETURN n LIMIT 5`;
      await executeQuery(tablesQuery);
    } catch (error) {
      console.error("基本クエリ実行エラー:", error);
      setError(`基本クエリの実行に失敗しました: ${error.message}`);
    }
  };
  
  // エッジ一覧を取得
  const listRelationships = async () => {
    try {
      // 最も基本的な関係クエリ
      const edgesQuery = `MATCH (a)-[r]->(b) RETURN r LIMIT 5`;
      await executeQuery(edgesQuery);
    } catch (error) {
      console.error("関係クエリ実行エラー:", error);
      setError(`関係クエリの実行に失敗しました: ${error.message}`);
    }
  };
  
  // Kuzuの初期化
  useEffect(() => {
    const initKuzu = async () => {
      try {
        setLoading(true);
        console.log('Kuzu初期化開始...');
        
        // アプリケーション層のデータベースサービスを使用して接続
        const connectResult = await databaseService.connect();
        
        if (!connectResult.success) {
          setError(connectResult.error);
          return;
        }
        
        console.log(connectResult.data.message);
        setResult({ 
          message: 'test_dbディレクトリのデータベースに接続しました', 
          connection: 'OK',
          dbPath: window.db_path
        });
        console.log('Kuzu初期化完了');
      } catch (error) {
        console.error('Kuzu初期化エラー:', error);
        console.log('エラータイプ:', typeof error);
        console.log('エラーメッセージ:', error.message);
        console.log('エラースタック:', error.stack);
        setError(`Kuzuの初期化中にエラーが発生しました: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    initKuzu();
    
    // クリーンアップ関数
    return () => {
      // コンポーネントのアンマウント時にリソースをクリーンアップ
      databaseService.disconnect()
        .catch(err => console.error('クリーンアップエラー:', err));
    };
  }, []);

  return (
    <div>
      <h1>Kuzu-Wasm データベースブラウザ</h1>
      
      <div>
        <h2>ステータス</h2>
        {loading && <p>処理中...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>
      
      <div>
        <h2>データベース操作</h2>
        
        {/* クエリ操作ボタン */}
        <div style={{ marginBottom: '15px' }}>
          <button 
            onClick={checkConnection}
            style={{ 
              padding: '8px 12px', 
              backgroundColor: '#673ab7', 
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
            disabled={loading}
          >
            接続テスト
          </button>
          
          <button 
            onClick={fetchAllNodeIds}
            style={{ 
              padding: '8px 12px', 
              backgroundColor: '#4caf50', 
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
            disabled={loading}
          >
            全ノードIDを取得
          </button>
          
          <button 
            onClick={listTables}
            style={{ 
              padding: '8px 12px', 
              backgroundColor: '#2196f3', 
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
            disabled={loading}
          >
            ノードテーブル一覧
          </button>
          
          <button 
            onClick={listRelationships}
            style={{ 
              padding: '8px 12px', 
              backgroundColor: '#ff9800', 
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
            disabled={loading}
          >
            リレーションシップ一覧
          </button>
        </div>
        
        {/* カスタムクエリ入力 */}
        <div style={{ marginTop: '20px', marginBottom: '15px' }}>
          <h3>カスタムクエリ</h3>
          <textarea
            style={{
              width: '100%',
              minHeight: '100px',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ccc',
              fontFamily: 'monospace'
            }}
            placeholder="Cypherクエリを入力してください..."
            onChange={(e) => setQuery(e.target.value)}
            value={query}
          />
          <button
            onClick={() => executeQuery(query)}
            style={{
              marginTop: '10px',
              padding: '8px 12px',
              backgroundColor: '#673ab7',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
            disabled={loading || !query.trim()}
          >
            クエリを実行
          </button>
        </div>
        
        {result && (
          <div>
            {query && <p><strong>実行クエリ:</strong> <code>{query}</code></p>}
            <h3>実行結果</h3>
            <pre style={{ maxHeight: '400px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '15px', borderRadius: '4px' }}>
              {JSON.stringify(result, jsonStringifyReplacer, 2)}
            </pre>
            
            {/* DB接続情報の追加表示 */}
            <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#e8f5e9', borderRadius: '4px' }}>
              <h3>データベース接続情報</h3>
              <div>
                <p><strong>接続状態:</strong> {window.conn ? '✅ 接続済み' : '❌ 未接続'}</p>
                <p><strong>データベースパス:</strong> {window.db_path || '不明'}</p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div style={{ marginTop: '30px' }}>
        <h3>環境情報</h3>
        <ul>
          <li>WebAssembly: {typeof WebAssembly !== 'undefined' ? '✅ サポート' : '❌ 未サポート'}</li>
          <li>SharedArrayBuffer: {typeof SharedArrayBuffer !== 'undefined' ? '✅ サポート' : '❌ 未サポート'}</li>
          <li>Cross-Origin-Isolation: {window.crossOriginIsolated ? '✅ 有効' : '❌ 無効'}</li>
        </ul>
      </div>
    </div>
  );
};

export default App;