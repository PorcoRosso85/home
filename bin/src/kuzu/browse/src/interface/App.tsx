import React, { useEffect, useState } from 'react';
import { connect, executeScript } from '../application/databaseService';

// シンプルなParquetビューアーアプリケーション
const App = () => {
  const [status, setStatus] = useState<{ message: string; type: string }>({
    message: 'データベース初期化中...',
    type: 'loading'
  });
  const [importCypherScript, setImportCypherScript] = useState<string>('');

  // Cypherスクリプトを読み込む関数
  const loadCypherScript = async (path: string): Promise<string> => {
    try {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`ファイル読み込みエラー: ${response.status} ${response.statusText}`);
      }
      return await response.text();
    } catch (error) {
      console.error(`スクリプト読み込みエラー: ${error.message}`);
      return '';
    }
  };

  // import.cypherスクリプトを読み込む
  useEffect(() => {
    const loadScript = async () => {
      const script = await loadCypherScript('/dql/import.cypher');
      setImportCypherScript(script);
    };
    
    loadScript();
  }, []);

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
        } else {
          setStatus({
            message: 'Parquetファイルの読み込みが完了しました',
            type: 'success'
          });
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
      
      {/* import.cypherスクリプト表示 */}
      {importCypherScript && (
        <div style={{ marginTop: '30px' }}>
          <h3>実行されたimport.cypherスクリプト:</h3>
          <pre style={{ 
            padding: '10px', 
            borderRadius: '4px',
            backgroundColor: '#f5f5f5',
            overflow: 'auto',
            maxHeight: '400px'
          }}>
            {importCypherScript}
          </pre>
        </div>
      )}
    </div>
  );
};

export default App;