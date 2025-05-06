/**
 * 最小構成のKuzuデータベースサービス
 * データベースの初期化と接続管理を担当します
 */

import { DB_DIR, DB_CONNECTION } from '../variables';

/**
 * WebサーバーからのDBファイルが存在するか確認する関数
 * @param dbPath データベースパス（通常は/db）
 * @returns 存在確認の結果、見つからなかったファイルリスト
 */
export const checkDbFilesExistence = async (dbPath: string): Promise<{ 
  valid: boolean, 
  missingFiles: string[], 
  error?: string 
}> => {
  try {
    // publicディレクトリから配信されるファイルのベースURLを構築
    const baseDbUrl = dbPath.startsWith('/') ? dbPath : `/${dbPath}`;
    
    // 必要なデータベースファイルのリスト
    const requiredFiles = DB_CONNECTION.REQUIRED_DB_FILES;
    
    // ファイルの存在確認を行うためのプロミス配列
    const fileChecks = requiredFiles.map(filename => {
      return new Promise<{ file: string, exists: boolean }>((resolveFile) => {
        // ファイルの存在を確認するためのHTTPリクエスト
        const xhr = new XMLHttpRequest();
        xhr.open('HEAD', `${baseDbUrl}/${filename}`, true);
        
        xhr.onload = function() {
          resolveFile({
            file: filename,
            exists: xhr.status === 200
          });
        };
        
        xhr.onerror = function() {
          resolveFile({
            file: filename,
            exists: false
          });
        };
        
        xhr.send();
      });
    });
    
    // すべてのファイルチェックを実行
    const results = await Promise.all(fileChecks);
    const missingFiles = results
      .filter(result => !result.exists)
      .map(result => result.file);
    
    return {
      valid: missingFiles.length === 0,
      missingFiles,
      error: missingFiles.length > 0 
        ? `データベースディレクトリに必要なファイルがありません: ${missingFiles.join(', ')}` 
        : undefined
    };
  } catch (err) {
    console.error('ファイル確認中にエラーが発生:', err);
    return {
      valid: false,
      missingFiles: [],
      error: `ファイル確認中にエラーが発生: ${err.message}`
    };
  }
};

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
      // オプションなしでインメモリデータベースを作成
      console.log('インメモリデータベース作成開始... (オプションなし)');
      const db = new kuzu.Database("");
      console.log('データベース作成完了');
      
      // グローバルにDBパスを保存（UI表示用）
      window.db_path = "memory";
      
      // データベース接続の作成
      console.log('データベース接続開始...');
      const conn = new kuzu.Connection(db);
      console.log('データベース接続完了');
      
      // 接続テスト
      const testQuery = "RETURN 1 AS test";
      console.log(`接続テストクエリ実行: ${testQuery}`);
      
      try {
        const testResult = await conn.query(testQuery);
        console.log('接続テスト結果:', testResult);
        
        return { kuzu, db, conn };
      } catch (testErr) {
        console.error('テストクエリ実行中のエラー:', testErr);
        return createError(
          'QUERY_ERROR',
          `テストクエリの実行中にエラーが発生しました: ${testErr.message}`,
          testErr
        );
      }
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
 * @param scriptPath スクリプトパス（URLまたはファイルパス）
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
      console.error(`スクリプトロードエラー: ステータス ${response.status} - ${response.statusText}`);
      console.error(`スクリプトパス: ${scriptPath}`);
      return createError(
        'SCRIPT_LOAD_ERROR',
        `スクリプトのロードに失敗しました: ${response.status} ${response.statusText}`
      );
    }
    
    const scriptContent = await response.text();
    console.log(`スクリプト読み込み成功: ${scriptPath}, 長さ: ${scriptContent.length}文字`);
    console.log(`スクリプト内容のプレビュー: ${scriptContent.substring(0, 100)}...`);
    
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
          // SOURCEコマンドはファイルの読み込みを行うため、再帰的に実行
          const sourceFilePath = command.match(/['"]([^'"]+)['"]/)?.[1];
          if (sourceFilePath) {
            console.log(`SOURCEコマンドを検出: ${sourceFilePath}`);
            const sourceResult = await executeCypherScript(conn, sourceFilePath);
            if (sourceResult !== true) {
              console.warn(`SOURCEファイルの実行に失敗: ${sourceFilePath}`, sourceResult);
            }
          } else {
            console.warn(`SOURCEコマンドの形式が不正: ${command}`);
          }
        } else {
          // 通常のCypherコマンドを実行
          try {
            console.log(`クエリ実行前 (${command.length}文字)...`);
            const result = await conn.query(command);
            console.log(`クエリ実行成功: ${command.substring(0, 50)}${command.length > 50 ? '...' : ''}`);
            
            if (result && result.getAllObjects) {
              const objects = await result.getAllObjects();
              console.log('クエリ結果 (objects):', objects);
            }
          } catch (queryErr) {
            console.error(`クエリ実行エラー: ${queryErr.message}`);
            console.error(`問題のクエリ: ${command}`);
            throw queryErr;  // エラーを再スローして上位でキャッチ
          }
        }
      } catch (cmdError) {
        console.error(`コマンド実行エラー: ${cmdError.message}`);
        console.error(`問題のコマンド: ${command}`);
        // エラーを返して処理を中断
        return createError(
          'COMMAND_EXECUTION_ERROR',
          `コマンド実行中にエラーが発生しました: ${cmdError.message}\nコマンド: ${command}`,
          cmdError
        );
      }
    }
    
    console.log(`スクリプト実行完了: ${scriptPath}`);
    return true;
  } catch (error) {
    console.error(`スクリプト実行エラー: ${error.message}`);
    console.error(`スクリプトパス: ${scriptPath}`);
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