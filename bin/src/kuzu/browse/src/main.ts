// KuzuDBデータブラウザ - シンプル版
// parquetファイルを読み込むためのライト版アプリケーション

console.log("KuzuDB Parquet Viewer - 初期化中...");

interface StatusMessage {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
}

// ステータス表示関数
function updateStatus(message: StatusMessage): void {
  const rootElement = document.getElementById('root');
  if (!rootElement) return;

  const statusDiv = document.createElement('div');
  statusDiv.className = `status ${message.type}`;
  statusDiv.textContent = message.text;
  
  rootElement.appendChild(statusDiv);
  console.log(`[${message.type}] ${message.text}`);
}

// Kuzuデータベースを初期化する関数
async function initializeDatabase() {
  try {
    updateStatus({ text: 'Kuzu-WASM モジュールを読み込み中...', type: 'loading' });
    
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../node_modules/kuzu-wasm");
    const kuzu = kuzuWasm.default || kuzuWasm;
    
    updateStatus({ text: 'インメモリデータベースを初期化中...', type: 'loading' });
    
    // インメモリデータベースを作成
    const db = new kuzu.Database("");
    window.db_path = "memory";
    
    // データベース接続の作成
    const conn = new kuzu.Connection(db);
    
    updateStatus({ text: 'データベース初期化完了', type: 'success' });
    
    return { kuzu, db, conn };
  } catch (error) {
    const errorMsg = `データベース初期化エラー: ${error.message}`;
    updateStatus({ text: errorMsg, type: 'error' });
    throw error;
  }
}

// Cypherスクリプトファイルを読み込み、実行する関数
async function loadAndExecuteCypherScript(conn: any, scriptPath: string) {
  try {
    updateStatus({ text: `Cypherスクリプトを読み込み中: ${scriptPath}`, type: 'loading' });
    
    // ファイルを取得
    const response = await fetch(scriptPath);
    if (!response.ok) {
      throw new Error(`ファイル読み込みエラー: ${response.status} ${response.statusText}`);
    }
    
    const scriptContent = await response.text();
    updateStatus({ text: `スクリプト読み込み成功: ${scriptPath}`, type: 'info' });
    
    // スクリプトを行ごとに分割し、コマンドを抽出
    const commands = scriptContent
      .split(';')
      .map(cmd => cmd.trim())
      .filter(cmd => cmd.length > 0 && !cmd.startsWith('--'));
    
    updateStatus({ text: `実行するコマンド数: ${commands.length}`, type: 'info' });
    
    // 各コマンドを順番に実行
    for (const command of commands) {
      try {
        // SOURCEコマンドの処理
        if (command.toLowerCase().startsWith('source')) {
          const sourceFilePath = command.match(/['"]([^'"]+)['"]/)?.[1];
          if (sourceFilePath) {
            updateStatus({ text: `SOURCEコマンドを検出: ${sourceFilePath}`, type: 'info' });
            await loadAndExecuteCypherScript(conn, sourceFilePath);
          } else {
            throw new Error(`SOURCEコマンドの形式が不正: ${command}`);
          }
        } else {
          // 通常のCypherコマンドを実行
          updateStatus({ text: `Cypherコマンド実行: ${command.substring(0, 50)}${command.length > 50 ? '...' : ''}`, type: 'loading' });
          const result = await conn.query(command);
          const resultData = await result.getAllObjects();
          
          // 実行結果を表示
          const resultDiv = document.createElement('div');
          resultDiv.innerHTML = `<h4>クエリ結果:</h4><pre>${JSON.stringify(resultData, (key, value) => 
            typeof value === 'bigint' ? value.toString() : value, 2)}</pre>`;
          document.getElementById('root')?.appendChild(resultDiv);
        }
      } catch (cmdError) {
        updateStatus({ text: `コマンド実行エラー: ${cmdError.message}`, type: 'error' });
        // エラーが発生しても続行
      }
    }
    
    updateStatus({ text: `スクリプト実行完了: ${scriptPath}`, type: 'success' });
    return true;
  } catch (error) {
    updateStatus({ text: `スクリプト実行エラー: ${error.message}`, type: 'error' });
    return false;
  }
}

// アプリケーション初期化
document.addEventListener("DOMContentLoaded", async () => {
  try {
    // タイトルと説明を追加
    const rootElement = document.getElementById('root');
    if (rootElement) {
      rootElement.innerHTML = `
        <h1>KuzuDB Parquet Viewer</h1>
        <p>import.cypherに基づくParquetファイルの読み込みツール</p>
      `;
    }
    
    // データベース初期化
    const { conn } = await initializeDatabase();
    
    // デフォルトのCypherスクリプトを実行
    await loadAndExecuteCypherScript(conn, '/dql/import.cypher');
  } catch (error) {
    console.error('初期化エラー:', error);
    updateStatus({ text: `初期化中にエラーが発生しました: ${error.message}`, type: 'error' });
  }
});

// グローバル定義（TypeScript用）
declare global {
  interface Window {
    db_path: string;
  }
}
