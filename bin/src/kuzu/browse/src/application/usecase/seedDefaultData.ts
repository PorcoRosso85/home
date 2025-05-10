import * as logger from '../../../../common/infrastructure/logger';
import { executeQuery } from '../../infrastructure/repository/queryExecutor';
import { VersionedLocationData, LocationURI } from '../../domain/types';

export async function seedDefaultData(conn: any): Promise<void> {
  logger.debug('DML実行中（3バージョン分のデータ）...');
  
  try {
    // v1.0.0のバージョンデータ
    const version1Data: VersionedLocationData = {
      version_id: 'v1.0.0',
      location_uris: [
        // ファイルシステムURI
        { uri_id: 'file:///src/main.ts', scheme: 'file', authority: '', path: '/src/main.ts', fragment: '', query: '' },
        { uri_id: 'file:///src/utils.ts', scheme: 'file', authority: '', path: '/src/utils.ts', fragment: '', query: '' },
        { uri_id: 'file:///src/components/app.tsx', scheme: 'file', authority: '', path: '/src/components/app.tsx', fragment: '', query: '' },
        // HTTP URI
        { uri_id: 'http://localhost:3000/api/data', scheme: 'http', authority: 'localhost:3000', path: '/api/data', fragment: '', query: '' },
      ]
    };

    // v1.1.0のバージョンデータ（v1.0.0からの変更）
    const version2Data: VersionedLocationData = {
      version_id: 'v1.1.0',
      location_uris: [
        // 継続するファイル
        { uri_id: 'file:///src/main.ts', scheme: 'file', authority: '', path: '/src/main.ts', fragment: 'main_v1.1', query: '' },
        { uri_id: 'file:///src/utils.ts', scheme: 'file', authority: '', path: '/src/utils.ts', fragment: '', query: '' },
        // 新規追加
        { uri_id: 'file:///src/components/header.tsx', scheme: 'file', authority: '', path: '/src/components/header.tsx', fragment: '', query: '' },
        { uri_id: 'file:///src/services/api.ts', scheme: 'file', authority: '', path: '/src/services/api.ts', fragment: '', query: '' },
        // HTTPの更新
        { uri_id: 'https://api.example.com/v1/users', scheme: 'https', authority: 'api.example.com', path: '/v1/users', fragment: '', query: 'page=1' },
      ],
      previous_version_id: 'v1.0.0'
    };

    // v1.2.0のバージョンデータ（v1.1.0からの変更）
    const version3Data: VersionedLocationData = {
      version_id: 'v1.2.0',
      location_uris: [
        // 継続するファイル
        { uri_id: 'file:///src/main.ts', scheme: 'file', authority: '', path: '/src/main.ts', fragment: 'main_v1.2', query: '' },
        { uri_id: 'file:///src/utils.ts', scheme: 'file', authority: '', path: '/src/utils.ts', fragment: 'updated_utils', query: '' },
        { uri_id: 'file:///src/services/api.ts', scheme: 'file', authority: '', path: '/src/services/api.ts', fragment: '', query: '' },
        // 新規追加
        { uri_id: 'file:///src/types/index.ts', scheme: 'file', authority: '', path: '/src/types/index.ts', fragment: '', query: '' },
        { uri_id: 'file:///tests/unit/utils.test.ts', scheme: 'file', authority: '', path: '/tests/unit/utils.test.ts', fragment: '', query: '' },
        { uri_id: 'file:///docs/architecture.md', scheme: 'file', authority: '', path: '/docs/architecture.md', fragment: '', query: '' },
        // VSCodeスキーム
        { uri_id: 'vscode://file/project/src/main.ts', scheme: 'vscode', authority: 'file', path: '/project/src/main.ts', fragment: '', query: '' },
      ],
      previous_version_id: 'v1.1.0'
    };

    // 各バージョンを順次作成
    // NOTE: 2025-05-10 - 複雑な処理を分離
    // 経緯: FOREACHによる条件付きFOLLOWS関係作成がparserエラーで失敗
    // 対策: 1) VersionState+LocationURI作成 2) FOLLOWS関係作成 の2段階に分離
    const versions = [version1Data, version2Data, version3Data];
    
    for (const versionData of versions) {
      logger.debug(`${versionData.version_id}のデータ作成中...`);
      
      // ステップ1: VersionStateとLocationURIを作成
      // NOTE: MERGEでLocationURIの重複を回避（複数バージョンで共有のため）
      const batchParams = {
        version_id: versionData.version_id,
        timestamp: new Date().toISOString(),
        description: `Version ${versionData.version_id} release`,
        location_uris: versionData.location_uris
      };
      
      const result = await executeQuery(conn, 'version_batch_operations', batchParams);
      logger.debug(`${versionData.version_id}作成結果:`, result);
      
      // ステップ2: 前のバージョンがある場合、FOLLOWS関係を作成
      if (versionData.previous_version_id) {
        const followsResult = await executeQuery(conn, 'create_follows', {
          from_version_id: versionData.previous_version_id,
          to_version_id: versionData.version_id
        });
        logger.debug(`FOLLOWS関係作成結果 (${versionData.previous_version_id} → ${versionData.version_id}):`, followsResult);
      }
    }
    
    // LocationURI階層構造を作成
    logger.debug('LocationURI階層構造の作成中...');
    const hierarchies = [
      // ファイル階層
      { parent_uri: 'file:///src', child_uri: 'file:///src/main.ts', relation_type: 'file_hierarchy' },
      { parent_uri: 'file:///src', child_uri: 'file:///src/utils.ts', relation_type: 'file_hierarchy' },
      { parent_uri: 'file:///src/components', child_uri: 'file:///src/components/app.tsx', relation_type: 'file_hierarchy' },
      { parent_uri: 'file:///src/components', child_uri: 'file:///src/components/header.tsx', relation_type: 'file_hierarchy' },
      { parent_uri: 'file:///src/services', child_uri: 'file:///src/services/api.ts', relation_type: 'file_hierarchy' },
      { parent_uri: 'file:///tests/unit', child_uri: 'file:///tests/unit/utils.test.ts', relation_type: 'file_hierarchy' },
    ];
    
    // 階層構造を作成
    await executeQuery(conn, 'create_location_hierarchy', { hierarchies });
    
    // データ確認
    logger.debug('データベース確認中...');
    const versionCheckResult = await conn.query("MATCH (v:VersionState) RETURN count(v) as version_count");
    const versionCheckData = await versionCheckResult.getAllObjects();
    
    const locationCheckResult = await conn.query("MATCH (l:LocationURI) RETURN count(l) as location_count");
    const locationCheckData = await locationCheckResult.getAllObjects();
    
    const relationshipCheckResult = await conn.query("MATCH (v:VersionState)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI) RETURN count(*) as relationship_count");
    const relationshipCheckData = await relationshipCheckResult.getAllObjects();
    
    logger.debug(`VersionStateノード数: ${JSON.stringify(versionCheckData)}`);
    logger.debug(`LocationURIノード数: ${JSON.stringify(locationCheckData)}`);
    logger.debug(`TRACKS_STATE_OF_LOCATED_ENTITY関係数: ${JSON.stringify(relationshipCheckData)}`);
    
    await versionCheckResult.close();
    await locationCheckResult.close();
    await relationshipCheckResult.close();
    
    logger.debug('データベース初期化完了（3バージョン分のデータ挿入完了）');
  } catch (error) {
    logger.error('DML実行エラー:', error);
    throw error;
  }
}
