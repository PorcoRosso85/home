import React, { useEffect, useState } from 'react';
import { connect, executeScript } from '../application/databaseService';

// シンプルなParquetビューアーアプリケーション
const App = () => {
  const [status, setStatus] = useState<{ message: string; type: string }>({
    message: 'データベース初期化中...',
    type: 'loading'
  });
  const [results, setResults] = useState<any[]>([]);

  // データベースの初期化と接続
  useEffect(() => {
    const initApp = async () => {
      try {
        // データベースに接続
        const connectResult = await connect();
        
        if (!connectResult.success) {
          setStatus({
            message: `データベース接続エラー: ${connectResult.error}`,
            type: 'error'
          });
          return;
        }
        
        setStatus({
          message: 'データベース接続完了。import.cypherを実行中...',
          type: 'success'
        });
        
        // import.cypherスクリプトを実行
        const { conn } = connectResult.data;
        const scriptResult = await executeScript(conn, '/dql/import.cypher');
        
        if (!scriptResult.success) {
          setStatus({
            message: `スクリプト実行エラー: ${scriptResult.error}`,
            type: 'error'
          });
          return;
        }
        
        setStatus({
          message: 'Parquetファイルの読み込みが完了しました',
          type: 'success'
        });
        
        // データベースの基本情報を取得
        try {
          const nodeCountResult = await conn.query('MATCH (n) RETURN count(n) AS nodeCount');
          const edgeCountResult = await conn.query('MATCH ()-[r]->() RETURN count(r) AS relationshipCount');
          
          const nodeCountData = await nodeCountResult.getAllObjects();
          const edgeCountData = await edgeCountResult.getAllObjects();
          
          setResults([
            {
              title: 'データベース統計情報',
              data: {
                nodeCount: nodeCountData[0]?.nodeCount || 0,
                relationshipCount: edgeCountData[0]?.relationshipCount || 0
              }
            }
          ]);
        } catch (statsError) {
          console.error('統計情報取得エラー:', statsError);
        }
      } catch (error) {
        setStatus({
          message: `初期化エラー: ${error.message}`,
          type: 'error'
        });
      }
    };
    
    initApp();
  }, []);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>KuzuDB Parquet Viewer</h1>
      <p>import.cypherスクリプトに基づいたParquetファイル読み込みツール</p>
      
      {/* ステータス表示 */}
      <div 
        style={{ 
          padding: '10px', 
          borderRadius: '4px',
          backgroundColor: status.type === 'loading' ? '#e3f2fd' : 
                          status.type === 'success' ? '#e8f5e9' : 
                          status.type === 'error' ? '#ffebee' : '#f5f5f5',
          marginBottom: '20px'
        }}
      >
        <p>{status.message}</p>
      </div>
      
      {/* 結果表示 */}
      {results.length > 0 && (
        <div>
          {results.map((result, index) => (
            <div key={index} style={{ marginBottom: '20px' }}>
              <h3>{result.title}</h3>
              <pre style={{ 
                padding: '10px', 
                borderRadius: '4px',
                backgroundColor: '#f5f5f5',
                overflow: 'auto'
              }}>
                {JSON.stringify(result.data, (key, value) => 
                  typeof value === 'bigint' ? value.toString() : value, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default App;