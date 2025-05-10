import * as logger from '../../../../common/infrastructure/logger';

export async function createSchema(conn: any): Promise<void> {
  logger.debug('DDLスキーマ読み込み中...');
  
  try {
    const ddlResponse = await fetch('/ddl/schema.cypher');
    const ddlContent = await ddlResponse.text();
    logger.debug(`DDL内容: ${ddlContent.substring(0, 100)}...`);
    
    // DDLコマンドを分割して実行
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
    
    logger.debug(`DDLコマンド数: ${ddlCommands.length}`);
    
    for (const command of ddlCommands) {
      logger.debug(`DDL実行中: ${command.substring(0, 50)}...`);
      const result = await conn.query(command);
      await result.close();
    }
    
    logger.info('DDL実行完了');
  } catch (error) {
    logger.error('DDL実行エラー:', error);
    throw error;
  }
}
