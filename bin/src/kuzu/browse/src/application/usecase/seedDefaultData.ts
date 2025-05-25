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

export const createDatabaseData = {
  async testDefault(conn: any): Promise<void> {
    await conn.query("BEGIN TRANSACTION");
    
    try {
      await defaultTest(conn);
      await conn.query("COMMIT");
      logger.debug('データベース初期化完了（testDefault）');
    } catch (error) {
      logger.error('DML実行エラー（testDefault）:', error);
      
      try {
        await conn.query("ROLLBACK");
        logger.debug('トランザクションをロールバックしました');
      } catch (rollbackError) {
        logger.error('ロールバックエラー:', rollbackError);
      }
      
      throw error;
    }
  },

  async kuzuBrowse(conn: any): Promise<void> {
    await conn.query("BEGIN TRANSACTION");
    
    try {
      await kuzuBrowse(conn);
      await conn.query("COMMIT");
      logger.debug('データベース初期化完了（kuzuBrowse）');
    } catch (error) {
      logger.error('DML実行エラー（kuzuBrowse）:', error);
      
      try {
        await conn.query("ROLLBACK");
        logger.debug('トランザクションをロールバックしました');
      } catch (rollbackError) {
        logger.error('ロールバックエラー:', rollbackError);
      }
      
      throw error;
    }
  }
};

// 後方互換性のための旧関数（deprecated）
export async function seedDefaultData(conn: any): Promise<void> {
  logger.warn('seedDefaultData is deprecated. Use createDatabaseData.testDefault() instead.');
  await createDatabaseData.testDefault(conn);
}

async function defaultTest(conn: any): Promise<void> {
  logger.debug('DML実行中（4バージョン分のデータ）...');
  
  // v1.0.0のバージョンデータ
  // REFACTORED: 新しい最小化LocationURIスキーマに対応
  const version1Data: VersionedLocationData = {
    version_id: 'v1.0.0',
    location_uris: [
      // ファイルシステムURI
      { id: 'file:///src/main.ts' },
      { id: 'file:///src/utils.ts' },
      { id: 'file:///src/components/app.tsx' },
      // HTTP URI
      { id: 'http://localhost:3000/api/data' },
    ]
  };

  // v1.1.0のバージョンデータ（v1.0.0からの変更）
  const version2Data: VersionedLocationData = {
    version_id: 'v1.1.0',
    location_uris: [
      // 継続するファイル
      { id: 'file:///src/main.ts#main_v1.1' },
      { id: 'file:///src/utils.ts' },
      // 新規追加
      { id: 'file:///src/components/header.tsx' },
      { id: 'file:///src/services/api.ts' },
      // HTTPの更新
      { id: 'https://api.example.com/v1/users?page=1' },
    ],
    previous_version_id: 'v1.0.0'
  };

  // v1.2.0のバージョンデータ（v1.1.0からの変更）
  const version3Data: VersionedLocationData = {
    version_id: 'v1.2.0',
    location_uris: [
      // 継続するファイル
      { id: 'file:///src/main.ts#main_v1.2' },
      { id: 'file:///src/utils.ts#updated_utils' },
      { id: 'file:///src/services/api.ts' },
      // 新規追加
      { id: 'file:///src/types/index.ts' },
      { id: 'file:///tests/unit/utils.test.ts' },
      { id: 'file:///docs/architecture.md' }
      // VSCodeスキーム削除（許可されていない）
    ],
    previous_version_id: 'v1.1.0'
  };

  // v1.2.1のバージョンデータ（v1.2.0からの変更）
  const version4Data: VersionedLocationData = {
    version_id: 'v1.2.1',
    location_uris: [
      // 継続するファイル
      { id: 'file:///src/main.ts' },
      { id: 'file:///src/utils.ts' },
      { id: 'file:///src/services/api.ts' },
      { id: 'file:///src/types/index.ts' },
      { id: 'file:///tests/unit/utils.test.ts' },
      { id: 'file:///docs/architecture.md' },
      
      // 新規追加: kuzu/browseディレクトリ構造
      { id: 'file:///home/nixos/bin/src/kuzu/browse' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/entity' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/logger' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public/dql' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public/export_data' },
    ],
    previous_version_id: 'v1.2.0'
  };

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
    { parent_id: 'file:///src', child_id: 'file:///src/main.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///src', child_id: 'file:///src/utils.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///src/components', child_id: 'file:///src/components/app.tsx', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///src/components', child_id: 'file:///src/components/header.tsx', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///src/services', child_id: 'file:///src/services/api.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///tests/unit', child_id: 'file:///tests/unit/utils.test.ts', relation_type: 'file_hierarchy' },
    
    // v1.2.1で追加されたkuzu/browseディレクトリ構造の階層
    { parent_id: 'file:///home/nixos/bin/src/kuzu', child_id: 'file:///home/nixos/bin/src/kuzu/browse', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/entity', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/logger', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/public', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public/dql', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/public', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public/export_data', relation_type: 'directory_hierarchy' },
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
  
  logger.debug('defaultTest: データ作成完了（4バージョン分のデータ挿入完了）');
}

async function kuzuBrowse(conn: any): Promise<void> {
  logger.debug('kuzuBrowse: プロジェクトデータの作成中...');
  
  // v0.1.0のkuzuBrowseプロジェクトデータ
  const kuzuBrowseData: VersionedLocationData = {
    version_id: 'v0.1.0',
    location_uris: [
      // プロジェクトルート
      { id: 'file:///home/nixos/bin/src/kuzu/browse' },
      
      // 設定ファイル
      { id: 'file:///home/nixos/bin/src/kuzu/browse/build.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/deno.json' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/mod.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/index.html' },
      
      // ドキュメント
      { id: 'file:///home/nixos/bin/src/kuzu/browse/CONVENTION.md' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/TODO.md' },
      
      // publicディレクトリ
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public/index.html' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public/dql' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/public/export_data' },
      
      // メインソースディレクトリ
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/index.tsx' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/main.ts' },
      
      // アプリケーション層
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks/useLocationUriTree.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks/useTreeData.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks/useVersionData.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks/useVersionTreeData.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/services' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/services/VersionCompletionService.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/buildLocationTree.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/buildVersionTree.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/createSchema.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/getLocationUrisByScheme.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/getLocationUris.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/getVersionedLocationUris.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/seedDefaultData.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/validation' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase/validation/versionBatchValidation.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/utils' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/utils/cacheUtils.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/utils/versionComparator.ts' },
      
      // ドメイン層
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/types.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/constants' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/constants/versionFormats.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service/locationTreeBuilder.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service/locationUriGrouper.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service/locationUriParser.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service/locationUriValidator.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service/versionParser.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service/versionTreeBuilder.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation/semverValidator.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation/validationError.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation/validationResult.ts' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation/node' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation/node/locationUriValidation.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation/node/versionStateValidation.ts' },
      
      // インフラストラクチャ層
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database/databaseEvent.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database/useDatabaseConnection.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database/queries' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/logger' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository/databaseConnection.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository/queryExecutor.ts' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository/VersionProgressRepository.ts' },
      
      // インターフェース層
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/App.tsx' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components/ErrorView.tsx' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components/LoadingView.tsx' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components/NodeDetailsPanel.tsx' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components/TreeNode.tsx' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components/TreeView.tsx' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components/VersionTreeView.tsx' },
      
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/pages' },
      { id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/utils' },
    ]
  };

  // バリデーション実行
  const validationResult = validateVersionBatch(kuzuBrowseData);
  if (!validationResult.isValid) {
    if (validationResult.errors) {
      logger.error(`${kuzuBrowseData.version_id}のバリデーションエラー:`, validationResult.errors);
    }
    
    const validationError = createValidationError(
      validationResult.error || 'Validation failed',
      'kuzuBrowseData',
      'BATCH_VALIDATION_FAILED'
    );
    
    logger.error(`${kuzuBrowseData.version_id}のバリデーションエラー詳細:`, 
      getValidationErrorDetails(validationError));
    
    throw validationError;
  }
  
  // kuzuBrowseプロジェクトデータを作成
  const batchParams = {
    version_id: kuzuBrowseData.version_id,
    timestamp: new Date().toISOString(),
    description: `kuzu-browse project v0.1.0 - Initial version management system`,
    change_reason: '初期開発: グラフデータベースブラウザアプリケーション',
    location_uris: kuzuBrowseData.location_uris
  };
  
  const result = await executeDMLQuery(conn, 'version_batch_operations', batchParams);
  logger.debug(`${kuzuBrowseData.version_id}作成結果:`, result);
  
  // 階層構造を作成
  logger.debug('kuzuBrowseプロジェクト階層構造の作成中...');
  const hierarchies = [
    // プロジェクトルート
    { parent_id: 'file:///home/nixos/bin/src/kuzu', child_id: 'file:///home/nixos/bin/src/kuzu/browse', relation_type: 'project_hierarchy' },
    
    // 第1階層
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public', relation_type: 'directory_hierarchy' },
    
    // 設定ファイル
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/build.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/deno.json', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/mod.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/index.html', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/CONVENTION.md', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse', child_id: 'file:///home/nixos/bin/src/kuzu/browse/TODO.md', relation_type: 'file_hierarchy' },
    
    // publicディレクトリ
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/public', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public/index.html', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/public', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public/dql', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/public', child_id: 'file:///home/nixos/bin/src/kuzu/browse/public/export_data', relation_type: 'directory_hierarchy' },
    
    // srcディレクトリ
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/index.tsx', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/main.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', relation_type: 'directory_hierarchy' },
    
    // アプリケーション層
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/hooks', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/services', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/usecase', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/application/utils', relation_type: 'directory_hierarchy' },
    
    // ドメイン層
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/types.ts', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/constants', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/service', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/domain/validation', relation_type: 'directory_hierarchy' },
    
    // インフラストラクチャ層  
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/database', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/logger', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/infrastructure/repository', relation_type: 'directory_hierarchy' },
    
    // インターフェース層
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/App.tsx', relation_type: 'file_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/components', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/pages', relation_type: 'directory_hierarchy' },
    { parent_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface', child_id: 'file:///home/nixos/bin/src/kuzu/browse/src/interface/utils', relation_type: 'directory_hierarchy' },
  ];
  
  // 階層構造を作成
  await executeDMLQuery(conn, 'create_location_hierarchy', { hierarchies });
  
  logger.debug('kuzuBrowse: データ作成完了');
}
