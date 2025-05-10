/**
 * 最小構成のKuzuデータベースサービス
 * Parquet読み込み機能のみサポート
 */

// 共通loggerをインポート
import * as logger from '../../../../common/infrastructure/logger';

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
    logger.info('Kuzu-Wasmモジュールのロード開始...');
    
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../../../node_modules/kuzu-wasm");
    logger.info('Kuzu-Wasmモジュールのロード完了');
    
    // Kuzuインスタンス化
    logger.info('Kuzuインスタンス化開始...');
    const kuzu = kuzuWasm.default || kuzuWasm;
    logger.info('Kuzuインスタンス化完了');
    
    try {
      // インメモリデータベースを作成
      logger.info('インメモリデータベース作成開始');
      const db = new kuzu.Database("");
      logger.info('データベース作成完了');
      
      // グローバルにDBパスを保存
      window.db_path = "memory";
      
      // データベース接続の作成
      logger.info('データベース接続開始...');
      const conn = new kuzu.Connection(db);
      logger.info('データベース接続完了');
      
      return { kuzu, db, conn };
    } catch (dbError) {
      logger.error('データベース作成エラー:', dbError);
      return createError(
        'DB_CREATION_ERROR',
        `データベースの作成中にエラーが発生しました: ${dbError.message}`,
        dbError
      );
    }
  } catch (error) {
    logger.error('Kuzu初期化エラー:', error);
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
    logger.info(`Cypherスクリプトを読み込み中: ${scriptPath}`);
    
    // ファイルを取得
    const response = await fetch(scriptPath);
    if (!response.ok) {
      logger.error(`スクリプトロードエラー: ${response.status} ${response.statusText}`);
      return createError(
        'SCRIPT_LOAD_ERROR',
        `スクリプトのロードに失敗しました: ${response.status} ${response.statusText}`
      );
    }
    
    const scriptContent = await response.text();
    logger.info(`スクリプト読み込み成功: ${scriptPath}、長さ: ${scriptContent.length}文字`);
    
    // スクリプトを行ごとに分割し、コマンドを抽出
    const commands = scriptContent
      .split(';')
      .map(cmd => cmd.trim())
      .filter(cmd => cmd.length > 0 && !cmd.startsWith('--'));
    
    if (commands.length === 0) {
      return createError(
        'EMPTY_SCRIPT',
        `スクリプトに有効なコマンドが含まれていません: ${scriptPath}`
      );
    }
    
    logger.info(`実行するコマンド数: ${commands.length}`);
    
    let successCount = 0;
    let failureCount = 0;
    let parquetLoadFailed = false;
    let lastError = null;
    
    // 各コマンドを順番に実行
    for (const command of commands) {
      try {
        logger.info(`Cypherコマンド実行: ${command}`);
        
        if (command.toLowerCase().startsWith('source')) {
          // SOURCEコマンドはファイルを読み込む
          const sourceFilePath = command.match(/['"]([^'"]+)['"]/)?.[1];
          if (sourceFilePath) {
            logger.info(`SOURCEコマンドを検出: ${sourceFilePath}`);
            const sourceResult = await executeCypherScript(conn, sourceFilePath);
            if (sourceResult !== true) {
              logger.error(`SOURCEファイルの実行に失敗: ${sourceFilePath}`);
              failureCount++;
              lastError = sourceResult;
              
              // SOURCEファイルのエラーは重要なので即座に返す
              return sourceResult;
            }
            successCount++;
          } else {
            logger.error(`SOURCEコマンドの形式が不正: ${command}`);
            failureCount++;
            lastError = createError(
              'INVALID_SOURCE_COMMAND',
              `SOURCEコマンドの形式が不正: ${command}`
            );
            return lastError;
          }
        } else if (command.toLowerCase().startsWith('copy')) {
          // COPYコマンドはparquetファイルを処理している可能性が高い
          const filePath = command.match(/FROM\s+["']([^"']+)["']/i)?.[1];
          const tableName = command.match(/COPY\s+[`"]?([^`"\s(]+)[`"]?/i)?.[1];
          
          try {
            logger.info(`Parquetファイル読み込み試行: ${filePath || 'ファイル名不明'} → ${tableName || 'テーブル名不明'}`);
            await conn.query(command);
            logger.info(`Parquetファイル読み込み成功: ${filePath || 'ファイル名不明'}`);
            successCount++;
            
            // 読み込んだテーブルの内容をチェック
            if (tableName) {
              try {
                const countQuery = `MATCH (n:${tableName}) RETURN count(n) as count`;
                const countResult = await conn.query(countQuery);
                const countData = await countResult.getAllObjects();
                const count = countData[0]?.count || 0;
                
                if (count === 0) {
                  logger.warn(`警告: ${tableName} テーブルにデータがありません (${filePath || 'ファイル名不明'})`);
                } else {
                  logger.info(`${tableName} テーブルに ${count} 件のデータを読み込みました`);
                }
              } catch (countErr) {
                logger.warn(`テーブル ${tableName} の件数確認エラー:`, countErr);
              }
            }
          } catch (copyErr) {
            logger.error(`Parquetファイル読み込みエラー: ${filePath || 'ファイル名不明'} - ${copyErr.message}`);
            failureCount++;
            parquetLoadFailed = true;
            lastError = createError(
              'PARQUET_LOAD_ERROR',
              `Parquetファイルの読み込みに失敗しました: ${filePath || 'ファイル名不明'} - ${copyErr.message}`,
              copyErr
            );
          }
        } else {
          // 通常のCypherコマンドを実行
          try {
            await conn.query(command);
            successCount++;
          } catch (queryErr) {
            logger.error(`クエリ実行エラー: ${queryErr.message}`);
            logger.error(`問題のクエリ: ${command}`);
            failureCount++;
            lastError = createError(
              'QUERY_ERROR',
              `クエリ実行中にエラーが発生しました: ${queryErr.message}\nクエリ: ${command}`,
              queryErr
            );
          }
        }
      } catch (cmdError) {
        logger.error(`コマンド実行エラー: ${cmdError.message}`);
        failureCount++;
        lastError = createError(
          'COMMAND_EXECUTION_ERROR',
          `コマンド実行中にエラーが発生しました: ${cmdError.message}`,
          cmdError
        );
      }
    }
    
    // 結果のサマリー
    if (failureCount > 0) {
      if (parquetLoadFailed) {
        logger.error(`スクリプト実行中にParquetファイルの読み込みに失敗しました (${successCount}成功/${failureCount}失敗)`);
        return createError(
          'PARQUET_LOAD_FAILED',
          `Parquetファイルの読み込みに失敗しました。詳細: ${lastError?.message || 'エラーの詳細は不明です'}`
        );
      } else {
        logger.error(`スクリプト実行中にエラーが発生しました (${successCount}成功/${failureCount}失敗)`);
        return lastError || createError(
          'SCRIPT_PARTIAL_FAILURE',
          `スクリプトの一部コマンドが失敗しました (${successCount}成功/${failureCount}失敗)`
        );
      }
    }
    
    logger.info(`スクリプト実行完了: ${scriptPath} (${successCount}コマンド成功)`);
    return true;
  } catch (error) {
    logger.error(`スクリプト実行エラー: ${error.message}`);
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
    logger.info('接続をクローズしています...');
    await conn.close();
    logger.info('接続がクローズされました');
    
    await db.close();
    logger.info('データベースがクローズされました');
    return null;
  } catch (error) {
    logger.error('クリーンアップエラー:', error);
    return createError(
      'CLEANUP_ERROR',
      `データベースリソースのクリーンアップ中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};