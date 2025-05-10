import * as logger from '../../../../common/infrastructure/logger';
import { executeQuery } from '../../infrastructure/repository/queryExecutor';

export async function seedDefaultData(conn: any): Promise<void> {
  logger.debug('DML実行中...');
  
  try {
    // デフォルトLocationURIデータ
    const defaultLocationUris = [
      // ファイルシステムURI
      { uri_id: 'file:///src/main.ts', scheme: 'file', authority: '', path: '/src/main.ts', fragment: '', query: '' },
      { uri_id: 'file:///src/utils.ts', scheme: 'file', authority: '', path: '/src/utils.ts', fragment: '', query: '' },
      { uri_id: 'file:///src/components/app.tsx', scheme: 'file', authority: '', path: '/src/components/app.tsx', fragment: '', query: '' },
      { uri_id: 'file:///src/components/header.tsx', scheme: 'file', authority: '', path: '/src/components/header.tsx', fragment: '', query: '' },
      { uri_id: 'file:///src/services/api.ts', scheme: 'file', authority: '', path: '/src/services/api.ts', fragment: '', query: '' },
      { uri_id: 'file:///src/types/index.ts', scheme: 'file', authority: '', path: '/src/types/index.ts', fragment: '', query: '' },
      { uri_id: 'file:///src/styles/globals.css', scheme: 'file', authority: '', path: '/src/styles/globals.css', fragment: '', query: '' },
      { uri_id: 'file:///tests/unit/utils.test.ts', scheme: 'file', authority: '', path: '/tests/unit/utils.test.ts', fragment: '', query: '' },
      { uri_id: 'file:///docs/architecture.md', scheme: 'file', authority: '', path: '/docs/architecture.md', fragment: '', query: '' },
      // HTTP URI
      { uri_id: 'http://localhost:3000/api/data', scheme: 'http', authority: 'localhost:3000', path: '/api/data', fragment: '', query: '' },
      { uri_id: 'https://api.example.com/v1/users?page=1', scheme: 'https', authority: 'api.example.com', path: '/v1/users', fragment: '', query: 'page=1' },
      // その他のスキーム
      { uri_id: 'vscode://file/home/user/project/src/main.ts', scheme: 'vscode', authority: 'file', path: '/home/user/project/src/main.ts', fragment: '', query: '' }
    ];
    
    // 各データに対してCREATEクエリを実行
    for (const locationUri of defaultLocationUris) {
      await executeQuery(conn, 'create_locationuri', locationUri);
    }
    
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
