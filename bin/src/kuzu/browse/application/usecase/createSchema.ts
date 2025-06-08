import * as logger from '../../../common/infrastructure/logger';

// エラー型定義（Tagged Union）
type SchemaLoadSuccess = {
  status: "success";
  data: void;
};

type FetchError = {
  status: "fetch_error";
  message: string;
  url: string;
};

type QueryExecutionError = {
  status: "query_execution_error";
  message: string;
  command: string;
};

type SchemaResult = SchemaLoadSuccess | FetchError | QueryExecutionError;

/**
 * DDLスキーマを読み込んで実行する
 * 規約準拠: try-catch禁止、throw文禁止、共用体型エラーハンドリング
 */
export async function createSchema(conn: any): Promise<SchemaResult> {
  logger.info('DDLスキーマ読み込み開始...');
  
  // DDLファイルを安全に取得
  const fetchResult = await fetchDdlFileSafely('/ddl/schema.cypher');
  if (fetchResult.status === "fetch_error") {
    logger.error('DDLファイルの取得に失敗:', fetchResult.message);
    return fetchResult;
  }
  
  const ddlContent = fetchResult.data;
  logger.info(`DDL内容の長さ: ${ddlContent.length}文字`);
  logger.info(`DDL内容（最初の200文字）: ${ddlContent.substring(0, 200)}...`);
  
  // DDLコマンドを分割
  const ddlCommands = parseDdlCommands(ddlContent);
  logger.info(`DDLコマンド数: ${ddlCommands.length}`);
  
  // コマンドを順次実行
  for (const command of ddlCommands) {
    logger.info(`DDL実行中: ${command.substring(0, 100)}...`);
    
    const executionResult = await executeCommandSafely(conn, command);
    if (executionResult.status === "query_execution_error") {
      logger.error('DDL実行エラー:', executionResult.message);
      return executionResult;
    }
  }
  
  logger.info('DDL実行完了');
  return { status: "success", data: undefined as void };
}

/**
 * DDLファイルを安全に取得する内部関数
 */
async function fetchDdlFileSafely(url: string): Promise<{ status: "success"; data: string } | FetchError> {
  const response = await fetch(url);
  
  if (!response.ok) {
    return {
      status: "fetch_error",
      message: `DDLファイルの取得に失敗しました: ${response.status} ${response.statusText}`,
      url
    };
  }
  
  const content = await response.text();
  return { status: "success", data: content };
}

/**
 * DDLコマンドを解析する内部関数
 */
function parseDdlCommands(ddlContent: string): string[] {
  const lines = ddlContent.split('\n');
  let currentCommand = '';
  const ddlCommands = [];
  
  for (const line of lines) {
    // コメント行や空行をスキップ
    if (line.trim().startsWith('--') || line.trim().startsWith('//') || line.trim() === '') {
      continue;
    }
    
    // 現在のコマンドに行を追加
    currentCommand += line.trim() + ' ';
    
    // セミコロンで終わる行でコマンドを確定
    if (line.trim().endsWith(';')) {
      if (currentCommand.trim()) {
        ddlCommands.push(currentCommand.trim());
      }
      currentCommand = '';
    }
  }
  
  // 最後にセミコロンがない場合のコマンドも追加
  if (currentCommand.trim()) {
    ddlCommands.push(currentCommand.trim());
  }
  
  return ddlCommands;
}

/**
 * コマンドを安全に実行する内部関数
 */
async function executeCommandSafely(conn: any, command: string): Promise<{ status: "success" } | QueryExecutionError> {
  const result = await conn.query(command);
  await result.close();
  return { status: "success" };
}
