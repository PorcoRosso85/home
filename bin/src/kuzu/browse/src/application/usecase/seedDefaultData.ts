import * as logger from '../../../../common/infrastructure/logger';
import { executeDMLQuery } from '../../infrastructure/repository/queryExecutor';
import { createValidationError, isValidationError, getValidationErrorDetails } from '../../domain/validation/validationError';
import { validateVersionBatch, type VersionedLocationData } from './validation/versionBatchValidation';

/**
 * バージョンIDに基づいて適切な変更理由を生成する
 */
function getChangeReasonForVersion(versionId: string, previousVersionId?: string): string {
  if (!previousVersionId) {
    return '新規開発';
  }

  // バージョンIDから変更理由を推測
  if (versionId.includes('.1') || versionId.includes('.2')) {
    return 'マイナーアップデート: 新機能追加';
  } else if (versionId.includes('.0.1') || versionId.includes('.0.2')) {
    return 'パッチリリース: バグフィックス';
  } else if (versionId.includes('2.0')) {
    return 'メジャーアップデート: アーキテクチャ刷新';
  } else {
    return '要件変更に伴う機能改修';
  }
}

export async function seedDefaultData(conn: any): Promise<void> {
  logger.debug('DML実行中（4バージョン分のデータ）...');
  
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
        // VSCodeスキーム削除（許可されていない）
      ],
      previous_version_id: 'v1.1.0'
    };

    // v1.2.1のバージョンデータ（v1.2.0からの変更）
    const version4Data: VersionedLocationData = {
      version_id: 'v1.2.1',
      location_uris: [
        // 継続するファイル
        { uri_id: 'file:///src/main.ts', scheme: 'file', authority: '', path: '/src/main.ts', fragment: 'main_v1.2.1', query: '' },
        { uri_id: 'file:///src/utils.ts', scheme: 'file', authority: '', path: '/src/utils.ts', fragment: 'updated_utils', query: '' },
        { uri_id: 'file:///src/services/api.ts', scheme: 'file', authority: '', path: '/src/services/api.ts', fragment: '', query: '' },
        { uri_id: 'file:///src/types/index.ts', scheme: 'file', authority: '', path: '/src/types/index.ts', fragment: '', query: '' },
        { uri_id: 'file:///tests/unit/utils.test.ts', scheme: 'file', authority: '', path: '/tests/unit/utils.test.ts', fragment: '', query: '' },
        { uri_id: 'file:///docs/architecture.md', scheme: 'file', authority: '', path: '/docs/architecture.md', fragment: '', query: '' },
        
        // 新規追加: kuzu/browseディレクトリ構造
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/application', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/application/hooks', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/application/usecase', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/domain', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/entity', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/domain/entity', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/domain/service', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/infrastructure', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/infrastructure/database', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/logger', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/infrastructure/logger', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/infrastructure/repository', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/interface', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/src/interface/components', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/public', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/public', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/public/dql', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/public/dql', fragment: '', query: '' },
        { uri_id: 'file:///home/nixos/bin/src/kuzu/browse/public/export_data', scheme: 'file', authority: '', path: '/home/nixos/bin/src/kuzu/browse/public/export_data', fragment: '', query: '' },
      ],
      previous_version_id: 'v1.2.0'
    };

    // FIXME: バリデーションルール違反のテストケース - 動作確認完了後は削除予定
    // NOTE: このデータはバリデーションエラーを意図的に発生させてアプリケーションをクラッシュさせます
    /*
    const validationTestData: VersionedLocationData = {
      version_id: '', // 違反1: 空のversion_id
      location_uris: [
        // 違反2: 許可されないvscodeスキーム
        { uri_id: 'vscode://file/project/src/main.ts', scheme: 'vscode', authority: 'file', path: '/project/src/main.ts', fragment: '', query: '' },
        // 違反3: uri_idが空
        { uri_id: '', scheme: 'file', authority: '', path: '/empty/uri/test.ts', fragment: '', query: '' },
        // 違反4: 必須フィールドpathが空
        { uri_id: 'file:///invalid/path', scheme: 'file', authority: '', path: '', fragment: '', query: '' },
        // 違反5: 許可されないスキーム
        { uri_id: 'custom://illegal/scheme', scheme: 'custom', authority: '', path: '/test', fragment: '', query: '' },
      ],
      previous_version_id: 'v1.2.1'
    };
    */

    // 各バージョンを順次作成
    const versions = [version1Data, version2Data, version3Data, version4Data];
    
    for (const versionData of versions) {
      logger.debug(`${versionData.version_id || '(empty version_id)'}のデータ作成中...`);
      
      // バリデーション実行
      const validationResult = validateVersionBatch(versionData);
      if (!validationResult.isValid) {
        // バリデーションエラーの詳細ログ
        if (validationResult.errors) {
          logger.error(`${versionData.version_id || '(empty version_id)'}のバリデーションエラー:`, validationResult.errors);
        }
        
        const validationError = createValidationError(
          validationResult.error || 'Validation failed',
          'versionData',
          'BATCH_VALIDATION_FAILED'
        );
        
        // バリデーションエラー詳細をログ出力してからエラーをスロー
        logger.error(`${versionData.version_id || '(empty version_id)'}のバリデーションエラー詳細:`, 
          getValidationErrorDetails(validationError));
        
        // クラッシュさせる（スキップせずにエラーをスロー）
        throw validationError;
      }
      
      // ステップ1: VersionStateとLocationURIを作成
      const batchParams = {
        version_id: versionData.version_id,
        timestamp: new Date().toISOString(),
        description: `Version ${versionData.version_id} release`,
        change_reason: getChangeReasonForVersion(versionData.version_id, versionData.previous_version_id),
        location_uris: versionData.location_uris
      };
      
      const result = await executeDMLQuery(conn, 'version_batch_operations', batchParams);
      logger.debug(`${versionData.version_id}作成結果:`, result);
      
      // ステップ2: 前のバージョンがある場合、FOLLOWS関係を作成
      if (versionData.previous_version_id) {
        const followsResult = await executeDMLQuery(conn, 'create_follows', {
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
      
      // v1.2.1で追加されたkuzu/browseディレクトリ構造の階層
      { parent_uri: 'file:///home/nixos/bin/src/kuzu', child_uri: 'file:///home/nixos/bin/src/kuzu/browse', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/public', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/application', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/entity', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/logger', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/public', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/public/dql', relation_type: 'directory_hierarchy' },
      { parent_uri: 'file:///home/nixos/bin/src/kuzu/browse/public', child_uri: 'file:///home/nixos/bin/src/kuzu/browse/public/export_data', relation_type: 'directory_hierarchy' },
    ];
    
    // 階層構造を作成
    await executeDMLQuery(conn, 'create_location_hierarchy', { hierarchies });
    
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
    
    logger.debug('データベース初期化完了（4バージョン分のデータ挿入完了）');
  } catch (error) {
    logger.error('DML実行エラー:', error);
    throw error;
  }
}
