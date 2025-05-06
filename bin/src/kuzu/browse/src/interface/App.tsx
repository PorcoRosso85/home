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
      
      // アプリケーション層のデータベースサービスを使用して接続
      // importParquet=true でサンプルデータを自動的にインポート
      const connectResult = await databaseService.connect(true);
      
      if (!connectResult.success) {
        setError(connectResult.error || 'データベース接続に失敗しました');
        console.error('データベース接続エラー:', connectResult.error);
        setConnectionStatus({ connected: false, dbPath: '' });
        setLoading(false);
        return false;
      }
      
      // 接続情報を更新
      const dbPath = window.db_path || 'memory';
      setConnectionStatus({ 
        connected: true, 
        dbPath: dbPath
      });
      
      console.log('インメモリモードでデータベースに接続しました', dbPath);
      
      // 接続成功後にデータベース統計を再取得
      try {
        await fetchDatabaseStats();
      } catch (statsErr) {
        console.warn('データベース統計取得エラー:', statsErr);
      }
      
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
        console.log('クエリ実行前に接続が必要です');
        const connected = await connectToDatabase();
        if (!connected) {
          setError('データベースに接続できないためクエリを実行できません');
          setLoading(false);
          return;
        }
      } else {
        // 接続済みの場合も軽量な接続確認を行う
        console.log('クエリ実行前の接続状態確認');
        try {
          // クイックチェック
          const quickCheck = await databaseService.executeDirectQuery('RETURN 1 AS test');
          if (!quickCheck.success) {
            console.warn('クイック接続チェック失敗 - 再接続が必要です');
            setConnectionStatus({ connected: false, dbPath: '' });
            const reconnected = await connectToDatabase();
            if (!reconnected) {
              setError('データベース接続が切断されていて再接続できませんでした');
              setLoading(false);
              return;
            }
          }
        } catch (checkErr) {
          console.warn('クイック接続チェックエラー - 再接続を試みます:', checkErr);
          setConnectionStatus({ connected: false, dbPath: '' });
          const reconnected = await connectToDatabase();
          if (!reconnected) {
            setError('データベース接続の検証に失敗し、再接続もできませんでした');
            setLoading(false);
            return;
          }
        }
      }
      
      // クエリを実行
      console.log(`クエリを実行: ${queryString}`);
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
  const checkConnection = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // データベース接続テスト
      const testResult = await databaseService.testConnection();
      
      if (!testResult.success) {
        setError(testResult.error || 'データベース接続テストに失敗しました');
        return;
      }
      
      // 接続情報を更新
      setConnectionStatus({ 
        connected: true, 
        dbPath: window.db_path || 'unknown'
      });
      
      // 結果を表示
      if (testResult.data) {
        setResult(testResult.data);
        setQuery('データベース接続診断');
        
        // より詳細な接続状態を設定
        const diagnosticData = testResult.data;
        setConnectionStatus({ 
          connected: testResult.success, 
          dbPath: diagnosticData.dbPath || window.db_path || 'unknown'
        });
        
        // データベース統計も更新
        if (typeof diagnosticData.nodeCount !== 'undefined' && 
            typeof diagnosticData.edgeCount !== 'undefined') {
          setDbStats({
            nodeCount: diagnosticData.nodeCount,
            edgeCount: diagnosticData.edgeCount
          });
        } else {
          // 診断データにない場合は別途取得
          await fetchDatabaseStats();
        }
      } else {
        setResult({
          message: testResult.error || 'データベース接続診断結果が不明です',
          success: false
        });
        setQuery('データベース接続診断');
      }
      
    } catch (error) {
      console.error('接続テストエラー:', error);
      setError(`接続テストに失敗しました: ${error.message || '不明なエラー'}`);
    } finally {
      setLoading(false);
    }
  };
  
  // 全ノードIDを取得
  const fetchAllNodeIds = () => executeQuery(predefinedQueries.allNodes);
  
  // テーブル一覧を取得
  const listTables = () => executeQuery(predefinedQueries.nodesSample);
  
  // エッジ一覧を取得
  const listRelationships = () => executeQuery(predefinedQueries.relationshipsSample);
  
  // 定期的な接続状態確認用の変数
  const [connectionCheckTimer, setConnectionCheckTimer] = useState<number | null>(null);

  // 定期的に接続状態を確認する関数
  const startConnectionCheck = () => {
    console.log('定期的な接続状態確認を開始');
    
    // 既存のタイマーをクリア
    if (connectionCheckTimer !== null) {
      clearInterval(connectionCheckTimer);
    }
    
    // 30秒ごとに接続状態を確認
    const timerId = window.setInterval(async () => {
      // すでに接続済みと表示されている場合に限り確認
      if (connectionStatus.connected) {
        console.log('定期的な接続状態確認を実行中...');
        try {
          // 簡易的な接続テスト (エラー表示なし)
          const testResult = await databaseService.testConnection();
          
          if (!testResult.success) {
            console.warn('定期チェックで接続エラーを検出:', testResult.error);
            // 接続が失敗している場合は状態を更新
            setConnectionStatus({ connected: false, dbPath: '' });
            // エラーメッセージを表示 (静かに行う)
            setError('自動チェックで接続状態の問題を検出しました。再接続してください。');
          }
        } catch (error) {
          console.error('定期的接続チェックエラー:', error);
          setConnectionStatus({ connected: false, dbPath: '' });
        }
      }
    }, 30000); // 30秒ごと
    
    setConnectionCheckTimer(timerId);
  };

  // Kuzuの初期化
  useEffect(() => {
    const initApp = async () => {
      try {
        // データベースに接続 (Parquetデータを自動的にインポート)
        const connected = await connectToDatabase();
        
        // データベース統計を取得
        if (connected) {
          await fetchDatabaseStats();
          // 接続状態の定期確認を開始
          startConnectionCheck();
          
          // インポートの状態を表示
          const dbStats = await databaseService.getStats();
          if (dbStats.success && dbStats.data) {
            if (dbStats.data.nodeCount === 0 || dbStats.data.edgeCount === 0) {
              console.log('データベースは空のようです。Parquetデータのインポートが必要かもしれません。');
              setError('データベースは空です。Parquetデータのインポートが必要かもしれません。');
            } else {
              console.log('データベースには既にデータが存在します。', dbStats.data);
            }
          }
        }
      } catch (error) {
        console.error('初期化エラー:', error);
      }
    };
    
    initApp();
    
    // クリーンアップ関数
    return () => {
      // 接続確認タイマーをクリア
      if (connectionCheckTimer !== null) {
        clearInterval(connectionCheckTimer);
      }
      
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
            <p>
              <strong>接続状態:</strong> 
              {connectionStatus.connected ? 
                <>
                  ✅ 接続済み 
                  <span style={{ 
                    display: 'inline-block',
                    marginLeft: '5px', 
                    backgroundColor: '#e0f2f1', 
                    padding: '2px 6px', 
                    borderRadius: '3px',
                    fontSize: '0.8rem',
                    fontWeight: 'bold',
                    color: '#00796b'
                  }}>
                    読み取り専用
                  </span>
                  <button 
                    onClick={checkConnection}
                    style={{ 
                      marginLeft: '10px',
                      padding: '4px 8px', 
                      backgroundColor: '#81c784',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.8rem'
                    }}
                    disabled={loading}
                  >
                    再検証
                  </button>
                  <button 
                    onClick={() => {
                      setLoading(true);
                      setError(null);
                      databaseService.importParquetData()
                        .then(result => {
                          if (result.success) {
                            setResult(result.data);
                            setQuery('サンプルデータ初期化');
                            fetchDatabaseStats();
                          } else {
                            setError(result.error);
                          }
                        })
                        .catch(err => setError(`サンプルデータ初期化エラー: ${err.message}`))
                        .finally(() => setLoading(false));
                    }}
                    style={{ 
                      marginLeft: '10px',
                      padding: '4px 8px', 
                      backgroundColor: '#7e57c2',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.8rem'
                    }}
                    disabled={loading}
                  >
                    サンプルデータを作成
                  </button>
                </> : 
                <>
                  ❌ 未接続
                  <button 
                    onClick={connectToDatabase}
                    style={{ 
                      marginLeft: '10px',
                      padding: '4px 8px', 
                      backgroundColor: '#ef5350',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.8rem'
                    }}
                    disabled={loading}
                  >
                    接続する
                  </button>
                </>
              }
            </p>
            <p><strong>データベースパス:</strong> {connectionStatus.dbPath || '不明'}</p>
            
            {/* 統計情報表示 */}
            <div>
              <p><strong>ノード数:</strong> {dbStats.nodeCount !== null ? String(dbStats.nodeCount) : '取得中...'}</p>
              <p><strong>エッジ数:</strong> {dbStats.edgeCount !== null ? String(dbStats.edgeCount) : '取得中...'}</p>
            </div>
            
            {/* 接続エラー時のヒント */}
            {!connectionStatus.connected && error && (
              <div style={{ 
                marginTop: '10px', 
                padding: '8px', 
                backgroundColor: 'rgba(255, 236, 236, 0.5)', 
                borderLeft: '3px solid #f44336',
                borderRadius: '2px'
              }}>
                <p style={{ margin: '0', fontSize: '0.9rem' }}>
                  <strong>ヒント:</strong> データベースファイルが正しく配置されているか確認してください。
                  公開サーバー上の <code>/db</code> ディレクトリには、Kuzuのデータベースファイル
                  （MANIFEST、database.iniなど）が含まれている必要があります。
                </p>
              </div>
            )}
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
          <li style={{ padding: '5px 0' }}>
            <strong>動作モード:</strong> 簡易インメモリモード（Parquetファイルではなくサンプルデータを使用）
          </li>
        </ul>
        <div style={{ 
          marginTop: '10px', 
          padding: '8px', 
          backgroundColor: 'rgba(255, 248, 225, 0.7)', 
          borderLeft: '3px solid #ffa000',
          borderRadius: '2px'
        }}>
          <p style={{ margin: '0', fontSize: '0.9rem' }}>
            <strong>注意:</strong> 現在、簡易インメモリモードで動作しています。Parquetファイルからのインポートではなく、最小限のサンプルデータを使用しています。
            リアルデータを表示する場合は、サンプルデータ作成ボタンをクリックして、サンプルグラフを生成してください。
          </p>
        </div>
      </div>
    </div>
  );
};

export default App;