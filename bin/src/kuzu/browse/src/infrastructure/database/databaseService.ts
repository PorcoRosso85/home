/**
 * 最小構成のKuzuデータベースサービス
 * Parquet読み込み機能のみサポート
 */

/**
 * データベース初期化の戻り値型
 */
export interface DatabaseInit {
  kuzu: any;
  db: any;
  conn: any;
}

/**
 * データベースエラーの型
 */
export interface DatabaseError {
  code: string;
  message: string;
  stack?: string;
}

/**
 * 初期化結果型
 */
export type DatabaseResult = DatabaseInit | DatabaseError;

/**
 * エラー判定関数
 */
export const isError = (result: DatabaseResult): result is DatabaseError => {
  return 'code' in result && 'message' in result;
};

/**
 * エラー作成関数
 */
export const createError = (code: string, message: string, error?: Error): DatabaseError => {
  return {
    code,
    message,
    stack: error?.stack
  };
};

/**
 * Kuzuデータベースを初期化する
 * @returns DatabaseInit または DatabaseError
 */
export const initializeDatabase = async (): Promise<DatabaseResult> => {
  try {
    console.log('Kuzu-Wasmモジュールのロード開始...');
    
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../../../node_modules/kuzu-wasm");
    console.log('Kuzu-Wasmモジュールのロード完了');
    
    // Kuzuインスタンス化
    console.log('Kuzuインスタンス化開始...');
    const kuzu = kuzuWasm.default || kuzuWasm;
    console.log('Kuzuインスタンス化完了');
    
    try {
      // インメモリデータベースを作成
      console.log('インメモリデータベース作成開始');
      const db = new kuzu.Database("");
      console.log('データベース作成完了');
      
      // グローバルにDBパスを保存
      window.db_path = "memory";
      
      // データベース接続の作成
      console.log('データベース接続開始...');
      const conn = new kuzu.Connection(db);
      console.log('データベース接続完了');
      
      return { kuzu, db, conn };
    } catch (dbError) {
      console.error('データベース作成エラー:', dbError);
      return createError(
        'DB_CREATION_ERROR',
        `データベースの作成中にエラーが発生しました: ${dbError.message}`,
        dbError
      );
    }
  } catch (error) {
    console.error('Kuzu初期化エラー:', error);
    return createError(
      'KUZU_INIT_ERROR',
      `Kuzuの初期化中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};

/**
 * Cypherスクリプトを実行する関数
 * 
 * @param conn データベース接続
 * @param scriptPath スクリプトパス
 * @returns 成功時はtrue、失敗時はエラー
 */
export const executeCypherScript = async (
  conn: any, 
  scriptPath: string
): Promise<boolean | DatabaseError> => {
  try {
    console.log(`Cypherスクリプトを読み込み中: ${scriptPath}`);
    
    // ファイルを取得
    const response = await fetch(scriptPath);
    if (!response.ok) {
      console.error(`スクリプトロードエラー: ${response.status} ${response.statusText}`);
      return createError(
        'SCRIPT_LOAD_ERROR',
        `スクリプトのロードに失敗しました: ${response.status} ${response.statusText}`
      );
    }
    
    const scriptContent = await response.text();
    console.log(`スクリプト読み込み成功: ${scriptPath}、長さ: ${scriptContent.length}文字`);
    
    // スクリプトを行ごとに分割し、コマンドを抽出
    const commands = scriptContent
      .split(';')
      .map(cmd => cmd.trim())
      .filter(cmd => cmd.length > 0 && !cmd.startsWith('--'));
    
    console.log(`実行するコマンド数: ${commands.length}`);
    
    // 各コマンドを順番に実行
    for (const command of commands) {
      try {
        console.log(`Cypherコマンド実行: ${command}`);
        
        if (command.toLowerCase().startsWith('source')) {
          // SOURCEコマンドはファイルを読み込む
          const sourceFilePath = command.match(/['"]([^'"]+)['"]/)?.[1];
          if (sourceFilePath) {
            console.log(`SOURCEコマンドを検出: ${sourceFilePath}`);
            const sourceResult = await executeCypherScript(conn, sourceFilePath);
            if (sourceResult !== true) {
              console.error(`SOURCEファイルの実行に失敗: ${sourceFilePath}`);
              return sourceResult;
            }
          } else {
            console.error(`SOURCEコマンドの形式が不正: ${command}`);
            return createError(
              'INVALID_SOURCE_COMMAND',
              `SOURCEコマンドの形式が不正: ${command}`
            );
          }
        } else {
          // 通常のCypherコマンドを実行
          try {
            await conn.query(command);
          } catch (queryErr) {
            console.error(`クエリ実行エラー: ${queryErr.message}`);
            console.error(`問題のクエリ: ${command}`);
            return createError(
              'QUERY_ERROR',
              `クエリ実行中にエラーが発生しました: ${queryErr.message}\nクエリ: ${command}`,
              queryErr
            );
          }
        }
      } catch (cmdError) {
        console.error(`コマンド実行エラー: ${cmdError.message}`);
        return createError(
          'COMMAND_EXECUTION_ERROR',
          `コマンド実行中にエラーが発生しました: ${cmdError.message}`,
          cmdError
        );
      }
    }
    
    console.log(`スクリプト実行完了: ${scriptPath}`);
    return true;
  } catch (error) {
    console.error(`スクリプト実行エラー: ${error.message}`);
    return createError(
      'SCRIPT_EXECUTION_ERROR',
      `スクリプト実行中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};

/**
 * データベース接続とリソースをクリーンアップする
 * @param conn データベース接続
 * @param db データベースインスタンス
 * @returns エラーがあればDatabaseError、なければnull
 */
export const cleanupDatabaseResources = async (
  conn: any, 
  db: any
): Promise<DatabaseError | null> => {
  try {
    console.log('接続をクローズしています...');
    await conn.close();
    console.log('接続がクローズされました');
    
    await db.close();
    console.log('データベースがクローズされました');
    return null;
  } catch (error) {
    console.error('クリーンアップエラー:', error);
    return createError(
      'CLEANUP_ERROR',
      `データベースリソースのクリーンアップ中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};