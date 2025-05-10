import * as logger from '../../../../common/infrastructure/logger';
import { insertLocationUris } from '../service/locationUriService';
import { getSampleLocationUris } from '../../domain/entity/sampleLocationUris';

export async function seedLocationUris(conn: any): Promise<void> {
  logger.debug('DML実行中...');
  
  try {
    // サンプルデータを挿入
    const sampleData = getSampleLocationUris();
    await insertLocationUris(conn, sampleData);
    
    // テーブル確認
    logger.debug('テーブル確認中...');
    const checkResult = await conn.query("MATCH (n:LocationURI) RETURN count(n) as count");
    const checkData = await checkResult.getAllObjects();
    logger.debug(`LocationURIノード数: ${JSON.stringify(checkData)}`);
    await checkResult.close();
    
    logger.debug('データベース初期化完了（接続は保持）');
  } catch (error) {
    logger.error('DML実行エラー:', error);
    throw error;
  }
}
