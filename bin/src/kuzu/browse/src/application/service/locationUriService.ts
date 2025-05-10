import * as logger from '../../../../common/infrastructure/logger';
import type { LocationUri } from '../../domain/entity/locationUri';
import { executeQuery } from '../../infrastructure/repository/queryExecutor';

export async function insertLocationUris(conn: any, locationURIs: LocationUri[]): Promise<void> {
  logger.debug('LocationURIノードを作成中...');
  
  try {
    for (const locationURI of locationURIs) {
      await executeQuery(conn, 'create_locationuri', locationURI);
    }
    logger.debug('LocationURIデータの挿入完了');
  } catch (error) {
    logger.error('DML実行エラー:', error);
    throw error;
  }
}

export async function bulkInsertLocationUris(conn: any, locationURIs: LocationUri[]): Promise<void> {
  logger.debug('LocationURIバルク挿入開始...');
  
  try {
    for (const locationURI of locationURIs) {
      await executeQuery(conn, 'create_locationuri', locationURI);
    }
    logger.debug('LocationURIバルク挿入完了');
  } catch (error) {
    logger.error('バルク挿入エラー:', error);
    throw error;
  }
}
