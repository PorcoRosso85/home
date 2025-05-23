import type { LocationUri } from '../../domain/entity/locationUri';
import * as logger from '../../../../common/infrastructure/logger';

declare global {
  type Window = {
    kuzu: any;
    conn: any;
  }
}

export async function getLocationUris(): Promise<LocationUri[]> {
  try {
    if (!window.conn) {
      logger.error('データベース接続が初期化されていません');
      throw new Error('データベース接続が初期化されていません');
    }

    logger.debug('グローバル接続を使用');

    // DQLディレクトリのクエリファイルを使用
    const queryPath = '/dql/fetch_all_locationuris.cypher';
    const response = await fetch(queryPath);
    if (!response.ok) {
      logger.error(`クエリファイルの読み込みに失敗: ${response.status} ${response.statusText}`);
      throw new Error(`クエリファイルの読み込みに失敗: ${response.status} ${response.statusText}`);
    }

    const queryText = await response.text();
    logger.debug('クエリファイル読み込み成功');
    logger.debug(`実行するクエリ: ${queryText}`);

    // クエリを実行
    logger.debug('クエリ実行開始...');
    const result = await window.conn.query(queryText);
    const data = await result.getAllObjects();
    logger.debug('クエリ実行完了');
    logger.debug(`クエリ結果: ${JSON.stringify(data)}`);
    
    // 結果を閉じる（重要！）
    await result.close();

    // LocationUriの型に変換
    const locationUris: LocationUri[] = data.map((row: any) => ({
      uri_id: row.uri_id,
      scheme: row.scheme,
      authority: row.authority || '',
      path: row.path,
      fragment: row.fragment || '',
      query: row.query || ''
    }));

    logger.info(`LocationUri取得完了: ${locationUris.length}件`);
    return locationUris;
  } catch (error) {
    logger.error('getLocationUris エラー:', error);
    // throw文を削除し、空配列を返す
    return [];
  }
}
