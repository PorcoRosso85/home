import React, { useState, useEffect } from 'https://esm.sh/react@18.2.0';
import { QueryResult } from '../domain/types.ts';

// Kuzu-Wasm メインアプリケーション
const App = () => {
  // ステート
  const [kuzu, setKuzu] = useState<any>(null);
  const [db, setDb] = useState<any>(null);
  const [conn, setConn] = useState<any>(null);
  const [query, setQuery] = useState<string>('MATCH (a:User) RETURN a.*;');
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState<boolean>(false);

  // Kuzuの初期化
  useEffect(() => {
    const initKuzu = async () => {
      try {
        setLoading(true);
        
        // Kuzu-Wasmのロード
        const kuzuWasm = await import('https://unpkg.com/@kuzu/kuzu-wasm@latest/dist/kuzu-browser.js');
        const kuzu = await kuzuWasm.default();
        setKuzu(kuzu);
        
        // インメモリデータベースの作成
        const db = await kuzu.Database();
        setDb(db);
        
        // データベース接続の作成
        const conn = await kuzu.Connection(db);
        setConn(conn);
        
        // 基本的なサンプルデータを作成
        await conn.execute(`CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))`);
        await conn.execute(`CREATE (u:User {name: 'Alice', age: 35})`);
        await conn.execute(`CREATE (u:User {name: 'Bob', age: 42})`);
        
        // Person テーブルの作成
        await conn.execute(`CREATE NODE TABLE Person(id INT64, name STRING, country STRING, PRIMARY KEY (id))`);
        
        setInitialized(true);
        setResult({ columns: ['status'], rows: [['データベースが初期化されました']] });
      } catch (error) {
        console.error('Kuzu初期化エラー:', error);
        setError('Kuzuの初期化中にエラーが発生しました: ' + error.message);
      } finally {
        setLoading(false);
      }
    };
    
    initKuzu();
  }, []);

  // クエリ実行
  const executeQuery = async () => {
    if (!conn) {
      setError('データベース接続がまだ初期化されていません');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await conn.execute(query);
      const resultJson = JSON.parse(result.table.toString());
      setResult(resultJson);
    } catch (error) {
      console.error('クエリ実行エラー:', error);
      setError('クエリ実行中にエラーが発生しました: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // リモートデータのロード
  const loadRemoteData = async () => {
    if (!conn) {
      setError('データベース接続がまだ初期化されていません');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // リモートCSVファイルをロード
      // このURLはビルドサーバーに合わせる必要があります
      const remoteDataUrl = '/public/remote_data.csv';
      const loadQuery = `COPY FROM '${remoteDataUrl}' (HEADER=true) TO Person;`;
      
      await conn.execute(loadQuery);
      setResult({ columns: ['status'], rows: [['リモートデータがロードされました']] });
    } catch (error) {
      console.error('リモートデータロードエラー:', error);
      setError('リモートデータのロード中にエラーが発生しました: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Kuzu-Wasm Deno Demo</h1>
      
      <div className="button-group">
        <button onClick={loadRemoteData} disabled={!initialized || loading}>
          リモートデータをロード
        </button>
      </div>
      
      <div>
        <h2>クエリ実行</h2>
        <textarea
          rows={4}
          cols={50}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <br />
        <button onClick={executeQuery} disabled={!initialized || loading}>
          実行
        </button>
      </div>
      
      <div>
        <h2>結果</h2>
        {loading && <p>処理中...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {result && (
          <pre>{JSON.stringify(result, null, 2)}</pre>
        )}
      </div>
      
      <div>
        <h3>サンプルクエリ</h3>
        <ul>
          <li><code>MATCH (a:User) RETURN a.*;</code> - Userテーブルのすべてのデータを表示</li>
          <li><code>MATCH (a:Person) RETURN a.*;</code> - リモートからロードしたPersonテーブルのデータを表示</li>
          <li><code>MATCH (a:Person) WHERE a.country = 'Japan' RETURN a.*;</code> - 日本出身の人のデータを表示</li>
        </ul>
      </div>
    </div>
  );
};

export default App;