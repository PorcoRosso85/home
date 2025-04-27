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
        setResult({ message: 'データベースに接続しました', connection: 'OK' });
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
        <h2>データベース情報</h2>
        {result && (
          <div>
            {query && <p>クエリ: {query}</p>}
            <pre style={{ maxHeight: '400px', overflow: 'auto' }}>{JSON.stringify(result, null, 2)}</pre>
            
            {/* DB接続情報の追加表示 */}
            <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <h3>データベース接続情報</h3>
              <div>
                <p><strong>接続状態:</strong> {window.conn ? '✅ 接続済み' : '❌ 未接続'}</p>
                <p><strong>データベースパス:</strong> {window.db_path || '不明'}</p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div>
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