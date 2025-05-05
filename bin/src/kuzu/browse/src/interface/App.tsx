import React, { useState, useEffect } from 'react';
import { databaseService } from '../application/databaseService';

// 最小構成のKuzu-Wasmアプリケーション
const App = () => {
  // ステート
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<{connected: boolean, dbPath: string}>({
    connected: false,
    dbPath: ''
  });
  const [query, setQuery] = useState<string>('');
  const [dbStats, setDbStats] = useState<{nodeCount: number | null, edgeCount: number | null}>({
    nodeCount: null,
    edgeCount: null
  });
  
  // BigInt値を文字列に変換するヘルパー関数
  const jsonStringifyReplacer = (key, value) => {
    // BigInt型の値を文字列に変換
    if (typeof value === 'bigint') {
      return value.toString();
    }
    return value;
  };
  
  // データベースに接続する関数
  const connectToDatabase = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // すでに接続済みの場合は処理をスキップ
      if (connectionStatus.connected && window.conn) {
        setLoading(false);
        return true;
      }
      
      // アプリケーション層のデータベースサービスを使用して接続
      const connectResult = await databaseService.connect();
      
      if (!connectResult.success) {
        setError(connectResult.error || 'データベース接続に失敗しました');
        setConnectionStatus({ connected: false, dbPath: '' });
        setLoading(false);
        return false;
      }
      
      // 接続情報を更新
      const dbPath = window.db_path || 'unknown';
      setConnectionStatus({ 
        connected: true, 
        dbPath: dbPath
      });
      
      console.log('データベースに接続しました: ' + dbPath);
      
      // 接続成功を返す
      setLoading(false);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '不明なエラー';
      console.error('データベース接続エラー:', error);
      setError(`データベースへの接続に失敗しました: ${errorMsg}`);
      setConnectionStatus({ connected: false, dbPath: '' });
      setLoading(false);
      return false;
    }
  };
  
  // データベース統計情報を取得する関数
  const fetchDatabaseStats = async () => {
    try {
      if (!connectionStatus.connected) {
        return;
      }
      
      const statsResult = await databaseService.getStats();
      if (statsResult.success && statsResult.data) {
        setDbStats({
          nodeCount: statsResult.data.nodeCount || 0,
          edgeCount: statsResult.data.edgeCount || 0
        });
      } else if (statsResult.error) {
        console.warn('データベース統計取得エラー:', statsResult.error);
        setDbStats({
          nodeCount: 0,
          edgeCount: 0
        });
      }
    } catch (error) {
      console.warn('データベース統計取得例外:', error);
      setDbStats({
        nodeCount: 0,
        edgeCount: 0
      });
    }
  };
  
  // クエリを実行する関数
  const executeQuery = async (queryString: string) => {
    if (!queryString || queryString.trim() === '') {
      setError('クエリが空です');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // データベース接続がない場合は接続
      if (!connectionStatus.connected) {
        const connected = await connectToDatabase();
        if (!connected) return;
      }
      
      // クエリを実行
      const queryResult = await databaseService.executeDirectQuery(queryString);
      
      if (!queryResult.success) {
        setError(queryResult.error || 'クエリ実行中にエラーが発生しました');
        return;
      }
      
      // 結果を設定
      setQuery(queryString);
      setResult(queryResult.data || []);
      
      // データベース統計を更新
      setTimeout(() => fetchDatabaseStats(), 100);
    } catch (err) {
      console.error('クエリ実行エラー:', err);
      setError(`クエリの実行に失敗しました: ${err.message || '不明なエラー'}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 定義済みクエリ
  const predefinedQueries = {
    connectionTest: `RETURN 'Connection Test' as result`,
    allNodes: `MATCH (n) RETURN n LIMIT 1000`,
    nodesSample: `MATCH (n) RETURN n LIMIT 5`,
    relationshipsSample: `MATCH (a)-[r]->(b) RETURN r LIMIT 5`
  };
  
  // 接続テスト
  const checkConnection = () => executeQuery(predefinedQueries.connectionTest);
  
  // 全ノードIDを取得
  const fetchAllNodeIds = () => executeQuery(predefinedQueries.allNodes);
  
  // テーブル一覧を取得
  const listTables = () => executeQuery(predefinedQueries.nodesSample);
  
  // エッジ一覧を取得
  const listRelationships = () => executeQuery(predefinedQueries.relationshipsSample);
  
  // Kuzuの初期化
  useEffect(() => {
    const initApp = async () => {
      try {
        // データベースに接続
        const connected = await connectToDatabase();
        
        // データベース統計を取得
        if (connected) {
          await fetchDatabaseStats();
        }
      } catch (error) {
        console.error('初期化エラー:', error);
      }
    };
    
    initApp();
    
    // クリーンアップ関数
    return () => {
      // コンポーネントのアンマウント時にリソースをクリーンアップ
      databaseService.disconnect()
        .catch(err => console.error('クリーンアップエラー:', err));
    };
  }, []);

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>Kuzu-Wasm データベースブラウザ</h1>
      
      {/* ステータスセクション */}
      <div style={{ marginBottom: '20px' }}>
        <h2>ステータス</h2>
        {loading && (
          <div style={{ padding: '10px', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
            <p>処理中...</p>
          </div>
        )}
        
        {error && (
          <div style={{ padding: '10px', backgroundColor: '#ffebee', borderRadius: '4px' }}>
            <p style={{ color: '#d32f2f' }}><strong>エラー:</strong> {error}</p>
          </div>
        )}
        
        {/* 接続情報 */}
        <div style={{ 
          padding: '15px', 
          backgroundColor: connectionStatus.connected ? '#e8f5e9' : '#ffebee', 
          borderRadius: '4px',
          marginTop: '10px'
        }}>
          <h3>データベース接続情報</h3>
          <div>
            <p><strong>接続状態:</strong> {connectionStatus.connected ? '✅ 接続済み' : '❌ 未接続'}</p>
            <p><strong>データベースパス:</strong> {connectionStatus.dbPath || '不明'}</p>
            
            {/* 統計情報表示 */}
            <div>
              <p><strong>ノード数:</strong> {dbStats.nodeCount !== null ? String(dbStats.nodeCount) : '取得中...'}</p>
              <p><strong>エッジ数:</strong> {dbStats.edgeCount !== null ? String(dbStats.edgeCount) : '取得中...'}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* データベース操作セクション */}
      <div style={{ marginBottom: '30px' }}>
        <h2>データベース操作</h2>
        
        {/* クエリ操作ボタン */}
        <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
          <button 
            onClick={checkConnection}
            style={{ 
              padding: '8px 12px', 
              backgroundColor: '#673ab7', 
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
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
              cursor: 'pointer'
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
              cursor: 'pointer'
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
        
        {/* 結果表示 */}
        {result && (
          <div style={{ marginTop: '20px' }}>
            {query && (
              <div style={{ marginBottom: '10px' }}>
                <h3>実行クエリ</h3>
                <pre style={{ 
                  backgroundColor: '#f0f0f0', 
                  padding: '10px', 
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  overflow: 'auto'
                }}>
                  {query}
                </pre>
              </div>
            )}
            
            <h3>実行結果</h3>
            <pre style={{ 
              maxHeight: '400px', 
              overflow: 'auto', 
              backgroundColor: '#f5f5f5', 
              padding: '15px', 
              borderRadius: '4px',
              fontFamily: 'monospace'
            }}>
              {JSON.stringify(result, jsonStringifyReplacer, 2)}
            </pre>
          </div>
        )}
      </div>
      
      {/* 環境情報セクション */}
      <div style={{ 
        marginTop: '30px',
        padding: '15px',
        backgroundColor: '#f0f4c3',
        borderRadius: '4px'
      }}>
        <h3>環境情報</h3>
        <ul style={{ listStyleType: 'none', padding: 0 }}>
          <li style={{ padding: '5px 0' }}>
            <strong>WebAssembly:</strong> {typeof WebAssembly !== 'undefined' ? '✅ サポート' : '❌ 未サポート'}
          </li>
          <li style={{ padding: '5px 0' }}>
            <strong>SharedArrayBuffer:</strong> {typeof SharedArrayBuffer !== 'undefined' ? '✅ サポート' : '❌ 未サポート'}
          </li>
          <li style={{ padding: '5px 0' }}>
            <strong>Cross-Origin-Isolation:</strong> {window.crossOriginIsolated ? '✅ 有効' : '❌ 無効'}
          </li>
        </ul>
      </div>
    </div>
  );
};

export default App;