import React, { useState, useEffect } from 'react';
import { 
  initializeDatabase, 
  setupUserTable, 
  isError,
  loadCsvData,
  cleanupDatabaseResources
} from '../infrastructure/database/databaseService';

// 最小構成のKuzu-Wasmアプリケーション
const App = () => {
  // ステート
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<string>('MATCH (a:User) RETURN a.*;');

  // Kuzuの初期化
  useEffect(() => {
    const initKuzu = async () => {
      try {
        setLoading(true);
        console.log('Kuzu初期化開始...');
        
        // 統一されたデータベース初期化処理
        const dbResult = await initializeDatabase();
        
        // エラーチェック
        if (isError(dbResult)) {
          setError(dbResult.message);
          return;
        }
        
        const { kuzu, db, conn } = dbResult;
        
        // ユーザーテーブルのセットアップ
        const setupError = await setupUserTable(conn);
        if (setupError) {
          setError(setupError.message);
          await cleanupDatabaseResources(conn, db);
          return;
        }
        
        // CSVデータの読み込み (オプション)
        // const csvError = await loadCsvData(conn, kuzu);
        // if (csvError) {
        //   console.warn(csvError.message);
        // }
        
        // クエリの実行とデータ表示
        const queryResult = await conn.query(`MATCH (a:User) RETURN a.*;`);
        
        // 結果の取得（結果形式によって処理を分岐）
        let resultJson;
        if (queryResult.table) {
          // tableプロパティを持つ場合
          const resultTable = queryResult.table.toString();
          resultJson = JSON.parse(resultTable);
        } else if (queryResult.getAllObjects) {
          // getAllObjects()メソッドを持つ場合
          resultJson = await queryResult.getAllObjects();
        } else {
          // その他の場合はオブジェクトとして扱う
          resultJson = queryResult;
        }
        
        setResult(resultJson);
        
        // グローバル変数として保存（デバッグ用）
        window.kuzu = kuzu;
        window.db = db;
        window.conn = conn;
        
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
      if (window.conn && window.db) {
        cleanupDatabaseResources(window.conn, window.db)
          .catch(err => console.error('クリーンアップエラー:', err));
      }
    };
  }, []);

  return (
    <div>
      <h1>Kuzu-Wasm 最小構成デモ</h1>
      
      <div>
        <h2>ステータス</h2>
        {loading && <p>処理中...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>
      
      <div>
        <h2>クエリ結果</h2>
        {result && (
          <pre>{JSON.stringify(result, null, 2)}</pre>
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