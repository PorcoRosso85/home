import React, { useState, useEffect } from 'https://esm.sh/react@18.2.0';

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
        
        // Kuzu-Wasmのロード
        console.log('Kuzu-Wasmモジュールのロード開始...');
        const kuzuWasm = await import('https://unpkg.com/@kuzu/kuzu-wasm@0.0.8/dist/kuzu-browser.js');
        console.log('Kuzu-Wasmモジュールのロード完了');
        
        // Kuzuのインスタンス化
        console.log('Kuzuインスタンス化開始...');
        const kuzu = await kuzuWasm.default();
        console.log('Kuzuインスタンス化完了');
        
        // インメモリデータベースの作成
        console.log('データベース作成開始...');
        const db = await kuzu.Database();
        console.log('データベース作成完了');
        
        // データベース接続の作成
        console.log('データベース接続開始...');
        const conn = await kuzu.Connection(db);
        console.log('データベース接続完了');
        
        // 基本的なサンプルデータを作成
        await conn.execute(`CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))`);
        await conn.execute(`CREATE (u:User {name: 'Alice', age: 35})`);
        await conn.execute(`CREATE (u:User {name: 'Bob', age: 42})`);
        
        // クエリの実行とデータ表示
        const queryResult = await conn.execute(`MATCH (a:User) RETURN a.*;`);
        const resultJson = JSON.parse(queryResult.table.toString());
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