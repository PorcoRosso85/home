/**
 * DuckLakeテーブル取得サンプル
 * 複数テーブルを並列でロードする使用例
 */
import { loadTablesFromDuck, loadTableFromDuck } from '../application/usecase/loadTableFromDuck';
import { createDuckApiClient } from './duckApiClient';
import { env } from '../config/variables';

/**
 * DuckLakeから全テーブルを取得してKuzuにロード
 * 
 * @param conn - Kuzu接続
 * @param version - スナップショットバージョン
 * @param onProgress - 進捗コールバック
 */
export async function loadAllDuckLakeTables(
  conn: any,
  version: number,
  onProgress?: (completed: number, total: number, tableName?: string) => void
): Promise<void> {
  // 1. Duck APIクライアントを作成
  const duckApiClient = createDuckApiClient({
    host: env.DUCK_API_HOST,
    port: env.DUCK_API_PORT
  });
  
  // 2. テーブル一覧を取得
  const tablesUrl = `http://${env.DUCK_API_HOST}:${env.DUCK_API_PORT}/api/snapshot/${version}/tables`;
  const response = await fetch(tablesUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch tables list: ${response.statusText}`);
  }
  
  const data = await response.json();
  const existingTables = data.tables
    .filter(t => t.exists)
    .map(t => t.name);
  
  console.log(`Found ${existingTables.length} tables in version ${version}:`, existingTables);
  
  // 3. 並列でロード
  const results = await loadTablesFromDuck(
    conn,
    version,
    existingTables,
    (completed, total) => {
      if (onProgress) {
        const currentTable = existingTables[completed - 1];
        onProgress(completed, total, currentTable);
      }
    }
  );
  
  // 4. 結果のサマリー
  const successful = results.filter(r => 'loadedCount' in r.result);
  const failed = results.filter(r => 'code' in r.result);
  
  console.log('Load complete:');
  successful.forEach(s => {
    if ('loadedCount' in s.result) {
      console.log(`  ✓ ${s.table}: ${s.result.loadedCount} records`);
    }
  });
  
  if (failed.length > 0) {
    console.error('Failed tables:');
    failed.forEach(f => {
      if ('code' in f.result) {
        console.error(`  ✗ ${f.table}: ${f.result.message}`);
      }
    });
  }
}

/**
 * 特定のテーブルのみロード
 */
export async function loadSpecificTables(
  conn: any,
  version: number,
  tableNames: string[]
): Promise<void> {
  const results = await loadTablesFromDuck(conn, version, tableNames);
  
  results.forEach(result => {
    if ('loadedCount' in result.result) {
      console.log(`Loaded ${result.table}: ${result.result.loadedCount} records`);
    } else {
      console.error(`Failed to load ${result.table}: ${result.result.message}`);
    }
  });
}

/**
 * Reactコンポーネントでの使用例
 */
export function useMultiTableLoad() {
  const [loading, setLoading] = React.useState(false);
  const [progress, setProgress] = React.useState({ completed: 0, total: 0, currentTable: '' });
  const [error, setError] = React.useState<Error | null>(null);
  
  const loadAllTables = React.useCallback(async (conn: any, version: number) => {
    setLoading(true);
    setError(null);
    
    try {
      await loadAllDuckLakeTables(conn, version, (completed, total, tableName) => {
        setProgress({ completed, total, currentTable: tableName || '' });
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { loading, progress, error, loadAllTables };
}
