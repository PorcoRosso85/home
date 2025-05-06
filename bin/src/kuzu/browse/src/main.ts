// KuzuDBデータブラウザ - シンプル版
// parquetファイルを読み込むためのライト版アプリケーション

console.log("KuzuDB Parquet Viewer - 初期化中...");

interface StatusMessage {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
}

// ステータス表示関数
function updateStatus(message: StatusMessage): void {
  // コンソールログのみ残す
  console.log(`[${message.type}] ${message.text}`);
}

// Parquetファイルをfetchしてwasm ファイルシステムに書き込む
async function preloadParquetFiles(kuzu: any) {
  updateStatus({ text: 'Parquetファイルをプリロード中...', type: 'loading' });
  
  // 必要なParquetファイルのリスト
  const parquetFiles = [
    'EntityAggregationView.parquet',
    'RequirementVerification.parquet',
    'LocationURI.parquet',
    'VersionState.parquet',
    'ReferenceEntity.parquet',
    'CodeEntity.parquet',
    'RequirementEntity.parquet',
    'DEPENDS_ON.parquet',
    'VERIFICATION_IS_IMPLEMENTED_BY.parquet',
    'AGGREGATES_CODE.parquet',
    'IS_IMPLEMENTED_BY.parquet',
    'CONTAINS_LOCATION.parquet',
    'HAS_LOCATION.parquet',
    'REQUIREMENT_HAS_LOCATION.parquet',
    'TRACKS_STATE_OF_REF.parquet',
    'USES.parquet',
    'AGGREGATES_REQ.parquet',
    'TRACKS_STATE_OF_REQ.parquet',
    'FOLLOWS.parquet',
    'TRACKS_STATE_OF_CODE.parquet',
    'CONTAINS_CODE.parquet',
    'REFERENCES_CODE.parquet',
    'VERIFIED_BY.parquet',
    'REFERENCES_EXTERNAL.parquet',
    'REFERENCE_HAS_LOCATION.parquet'
  ];
  
  let successCount = 0;
  let failCount = 0;
  
  for (const fileName of parquetFiles) {
    try {
      // HTTPでファイルを取得
      const response = await fetch(`/export_data/${fileName}`);
      if (!response.ok) {
        throw new Error(`HTTPエラー: ${response.status}`);
      }
      
      // バイナリデータを取得
      const fileData = await response.arrayBuffer();
      
      // WASM仮想ファイルシステムに書き込む
      kuzu.FS.writeFile(`/${fileName}`, new Uint8Array(fileData));
      
      successCount++;
      console.log(`Parquetファイルプリロード成功: ${fileName}`);
    } catch (error) {
      failCount++;
      console.error(`Parquetファイルプリロード失敗: ${fileName} - ${error.message}`);
      updateStatus({ text: `Parquetファイルプリロード失敗: ${fileName} - ${error.message}`, type: 'error' });
    }
  }
  
  // WASM FSの内容を確認（デバッグ用）
  try {
    const files = kuzu.FS.readdir('/');
    console.log("WASM FSのファイル一覧:", files);
  } catch (err) {
    console.error("WASM FSの内容確認エラー:", err);
  }
  
  updateStatus({ 
    text: `Parquetファイルプリロード完了 (${successCount}成功/${failCount}失敗)`, 
    type: failCount > 0 ? 'error' : 'success' 
  });
  
  return successCount > 0;
}

// Kuzuデータベースを初期化する関数
async function initializeDatabase() {
  try {
    updateStatus({ text: 'Kuzu-WASM モジュールを読み込み中...', type: 'loading' });
    
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../node_modules/kuzu-wasm");
    const kuzu = kuzuWasm.default || kuzuWasm;
    
    // グローバルにkuzuオブジェクトを設定（FS APIのために必要）
    window.kuzu = kuzu;
    
    updateStatus({ text: 'Parquetファイルを仮想ファイルシステムに転送中...', type: 'loading' });
    
    // Parquetファイルをプリロード
    await preloadParquetFiles(kuzu);
    
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

// Cypherスクリプトからコマンドを正しく抽出する関数
function extractCommands(scriptContent: string): string[] {
  // スクリプトの行を取得
  const lines = scriptContent.split('\n');
  
  let currentCommand = '';
  const commands: string[] = [];
  
  // 各行を処理
  for (let line of lines) {
    // コメント行や空行はスキップ
    if (line.trim().startsWith('--') || line.trim() === '') {
      continue;
    }
    
    // 現在のコマンドに行を追加
    currentCommand += line.trim() + ' ';
    
    // セミコロンが含まれている場合は、コマンドの終了とみなす
    if (line.trim().endsWith(';')) {
      // セミコロンまでを一つのコマンドとして追加
      commands.push(currentCommand.trim());
      // 次のコマンドのために初期化
      currentCommand = '';
    }
  }
  
  // 最後にセミコロンがない未完了のコマンドが残っている場合も追加
  if (currentCommand.trim()) {
    commands.push(currentCommand.trim());
  }
  
  // 空ではないコマンドのみを返す
  return commands.filter(cmd => cmd.trim() !== '');
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
    console.log(`読み込まれたCypherスクリプト(${scriptPath}):\n${scriptContent}`);
    updateStatus({ text: `スクリプト読み込み成功: ${scriptPath}`, type: 'info' });
    
    // 改良: 新しい方法でスクリプトをコマンドに分割
    const commands = extractCommands(scriptContent);
    
    console.log("分割されたコマンド:", commands);
    
    if (commands.length === 0) {
      throw new Error(`スクリプトに有効なコマンドが含まれていません: ${scriptPath}`);
    }
    
    updateStatus({ text: `実行するコマンド数: ${commands.length}`, type: 'info' });
    
    let successCount = 0;
    let failureCount = 0;
    let parquetImportFailed = false;
    
    // 各コマンドを順番に実行
    for (const command of commands) {
      try {
        // SOURCEコマンドの処理
        if (command.toLowerCase().startsWith('source')) {
          const sourceFilePath = command.match(/['"]([^'"]+)['"]/)?.[1];
          if (sourceFilePath) {
            updateStatus({ text: `SOURCEコマンドを検出: ${sourceFilePath}`, type: 'info' });
            const sourceResult = await loadAndExecuteCypherScript(conn, sourceFilePath);
            if (!sourceResult) {
              failureCount++;
              throw new Error(`SOURCEファイルの実行に失敗しました: ${sourceFilePath}`);
            }
            successCount++;
          } else {
            failureCount++;
            throw new Error(`SOURCEコマンドの形式が不正: ${command}`);
          }
        } else if (command.toLowerCase().startsWith('copy')) {
          // COPYコマンドはparquetファイルを処理している
          // ファイルパスを抽出
          const filePath = command.match(/FROM\s+["']([^"']+)["']/i)?.[1];
          const tableName = command.match(/COPY\s+[`"]?([^`"\s(]+)[`"]?/i)?.[1];
          
          updateStatus({ text: `Parquetファイル読み込み中: ${tableName} (${filePath})`, type: 'loading' });
          console.log(`Parquetファイル読み込みクエリ: ${command}`);
          
          try {
            const result = await conn.query(command);
            const resultData = await result.getAllObjects();
            
            // 結果をコンソールに出力
            console.log(`Parquetファイル読み込み結果:`, resultData);
            
            successCount++;
            
            updateStatus({ text: `Parquetファイル読み込み成功: ${filePath}`, type: 'success' });
          } catch (copyError) {
            failureCount++;
            parquetImportFailed = true;
            const tableName = command.match(/COPY\s+[`"]?([^`"\s(]+)[`"]?/i)?.[1] || 'Unknown';
            const filePath = command.match(/FROM\s+["']([^"']+)["']/i)?.[1] || 'Unknown';
            const errorMessage = `Parquetファイル読み込みエラー: テーブル=${tableName}, ファイル=${filePath} - ${copyError.message}`;
            
            console.error(`COPY失敗: ${errorMessage}`, copyError);
            console.error(`実行されたクエリ: ${command}`);
            
            updateStatus({ text: errorMessage, type: 'error' });
            
            // エラーは記録するが、処理は続行
          }
        } else {
          // 通常のCypherコマンドを実行
          updateStatus({ text: `クエリ実行中: ${command.substring(0, 50)}${command.length > 50 ? '...' : ''}`, type: 'loading' });
          
          try {
            const result = await conn.query(command);
            const resultData = await result.getAllObjects();
            
            // コンソールにのみデータを出力
            console.log(`クエリ実行結果:`, command);
            console.log(resultData);
            
            successCount++;
          } catch (queryError) {
            failureCount++;
            
            console.error(`クエリ実行エラー: ${queryError.message} (${command})`);
            updateStatus({ text: `クエリ実行エラー: ${queryError.message}`, type: 'error' });
          }
        }
      } catch (cmdError) {
        failureCount++;
        updateStatus({ text: `コマンド実行エラー: ${cmdError.message}`, type: 'error' });
        console.error(`コマンド実行エラー:`, command);
        console.error(`エラー内容:`, cmdError.message);
        
        // エラーは記録するが、処理は続行
      }
    }
    
    // 結果のサマリーをコンソールにのみ表示
    if (failureCount > 0) {
      if (parquetImportFailed) {
        // Parquetファイルの読み込み失敗
        updateStatus({ 
          text: `スクリプト実行完了 (${successCount}成功/${failureCount}失敗): Parquetファイルの読み込みに失敗しました`, 
          type: 'error' 
        });
        
        console.error(`Parquetファイルの読み込みに失敗しました。以下の理由が考えられます:
- 指定されたパスにParquetファイルが存在しない
- Parquetファイルの形式が正しくない
- ファイルへのアクセス権限がない
- テーブル定義とParquetファイルの構造が一致していない
コンソールログを確認して詳細なエラー情報を参照してください。`);
        
        return false;
      } else {
        // その他のエラー
        updateStatus({ 
          text: `スクリプト実行完了 (${successCount}成功/${failureCount}失敗): 一部のコマンドでエラーが発生しました`, 
          type: 'error' 
        });
      }
    } else {
      // すべて成功
      updateStatus({ 
        text: `スクリプト実行完了: ${scriptPath} (${successCount}コマンド成功)`, 
        type: 'success' 
      });
      
      console.log(`すべてのクエリが正常に実行されました。
Parquetファイルからのデータ読み込みが完了しました。
各テーブルにデータが表示されていれば、Parquetファイルが正常に読み込まれています。
テーブルは存在するがレコード数が0の場合は、Parquetファイルは存在するが中身が空である可能性があります。`);
    }
    
    return failureCount === 0;
  } catch (error) {
    updateStatus({ text: `スクリプト実行エラー: ${error.message}`, type: 'error' });
    return false;
  }
}

// アプリケーション初期化
document.addEventListener("DOMContentLoaded", async () => {
  try {
    console.log("KuzuDB Parquet Viewer - コマンドライン版");
    console.log("import.cypherに基づくParquetファイルの読み込みツール");
    
    // ファイルパス確認のためにフェッチテスト
    console.log("=== ファイルパステスト開始 ===");
    
    // 様々なパスパターンでフェッチしてみる
    const pathsToTest = [
      '/export_data/EntityAggregationView.parquet',
      './export_data/EntityAggregationView.parquet',
      '../export_data/EntityAggregationView.parquet',
      '/public/export_data/EntityAggregationView.parquet',
      'public/export_data/EntityAggregationView.parquet',
      '/home/nixos/bin/src/kuzu/db/export_data/EntityAggregationView.parquet',
      '/home/nixos/bin/src/kuzu/browse/public/export_data/EntityAggregationView.parquet'
    ];
    
    for (const path of pathsToTest) {
      try {
        const response = await fetch(path, { method: 'HEAD' });
        console.log(`パステスト: ${path} - ${response.ok ? '成功' : '失敗'} (${response.status})`);
      } catch (error) {
        console.log(`パステスト: ${path} - エラー (${error.message})`);
      }
    }
    
    // export_dataディレクトリ一覧の取得を試みる
    try {
      const indexResponse = await fetch('/export_data/');
      console.log(`/export_data/ ディレクトリインデックス取得: ${indexResponse.ok ? '成功' : '失敗'} (${indexResponse.status})`);
      if (indexResponse.ok) {
        const html = await indexResponse.text();
        console.log("ディレクトリ内容:", html);
      }
    } catch (error) {
      console.log(`ディレクトリインデックス取得エラー: ${error.message}`);
    }
    
    try {
      const publicDirResponse = await fetch('/public/');
      console.log(`/public/ ディレクトリインデックス取得: ${publicDirResponse.ok ? '成功' : '失敗'} (${publicDirResponse.status})`);
      if (publicDirResponse.ok) {
        const html = await publicDirResponse.text();
        console.log("ディレクトリ内容:", html);
      }
    } catch (error) {
      console.log(`ディレクトリインデックス取得エラー: ${error.message}`);
    }
    
    // ファイルが実際に存在するか確認するため、schema.cypherを取得してみる
    try {
      const schemaResponse = await fetch('/export_data/schema.cypher');
      console.log(`/export_data/schema.cypher 取得: ${schemaResponse.ok ? '成功' : '失敗'} (${schemaResponse.status})`);
      if (schemaResponse.ok) {
        const content = await schemaResponse.text();
        console.log("schema.cypher内容:", content.substring(0, 200) + "...");
      }
    } catch (error) {
      console.log(`schema.cypher取得エラー: ${error.message}`);
    }
    
    console.log("=== ファイルパステスト終了 ===");
    
    // データベース初期化（KuzuとFS APIを含む）
    console.log("データベースとWASM FS初期化中...");
    const { conn } = await initializeDatabase();
    
    // WASM FSの内容を確認
    console.log("=== WASM FSテスト開始 ===");
    try {
      if (window.kuzu && window.kuzu.FS) {
        const files = window.kuzu.FS.readdir('/');
        console.log("WASM FSのファイル一覧:", files);
        
        // 特定のファイルの存在を確認
        const testFiles = ['EntityAggregationView.parquet', 'CodeEntity.parquet'];
        for (const file of testFiles) {
          try {
            const stat = window.kuzu.FS.stat(`/${file}`);
            console.log(`WASM FS内ファイル確認: /${file} - 存在します (サイズ: ${stat.size} バイト)`);
          } catch (statErr) {
            console.error(`WASM FS内ファイル確認: /${file} - 存在しません (${statErr.message})`);
          }
        }
      } else {
        console.error("WASM FSがまだ初期化されていません");
      }
    } catch (err) {
      console.error("WASM FSテストエラー:", err);
    }
    console.log("=== WASM FSテスト終了 ===");
    
    // デフォルトのインポートスクリプトを実行し、失敗したらエラーを表示する
    try {
      // 通常のインポート処理を試す
      await loadAndExecuteCypherScript(conn, '/dql/import.cypher');
    } catch (error) {
      console.error("Parquetファイルのインポートに失敗しました:", error);
      updateStatus({ 
        text: `Parquetファイルのインポートに失敗しました: ${error.message}`, 
        type: 'error' 
      });
      console.error(`Parquetファイルの読み込みに失敗しました
ファイルが見つからないか、アクセスできません。以下を確認してください:
- 指定されたパスにParquetファイルが存在するか
- ファイルへのアクセス権限があるか
- ファイルパスが正しく指定されているか`);
    }
  } catch (error) {
    console.error('初期化エラー:', error);
    updateStatus({ text: `初期化中にエラーが発生しました: ${error.message}`, type: 'error' });
  }
  
  console.log("KuzuDB Parquet Viewerの処理が完了しました。console.logを確認してください。");
});

// グローバル定義（TypeScript用）
declare global {
  interface Window {
    db_path: string;
    kuzu: any; // Kuzu WASMオブジェクト
  }
}
