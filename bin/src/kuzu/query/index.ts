/**
 * メインエントリーポイント
 * 
 * KuzuDBクエリ操作の統一エントリーポイント
 */

// Infrastructure層
export * from './infrastructure/repositories/browserQueryRepository';
export * from './infrastructure/repositories/nodeQueryRepository';
export * from './infrastructure/repositories/denoQueryRepository';
export * from './infrastructure/factories/repositoryFactory';
export * from './infrastructure/tools/dmlGenerator';

// Domain層
export * from './domain/entities/queryResult';
export * from './domain/entities/locationUri';
export * from './domain/entities/versionState';
export * from './domain/valueObjects/uriValue';
export * from './domain/valueObjects/uriValidation';
export * from './domain/repositories/queryRepository';
export * from './domain/repositories/fileRepository';

// Application層
export * from './application/services/integratedDmlService';
export * from './application/commands/executeQuery';
export * from './application/commands/generateQueries';

// Interface層
export * from './interface/queryClient';
export * from './interface/dmlOperations';
export * from './interface/queryExecutor';

// 便利な初期化関数のエクスポート
import { initializeGlobalQueryClient } from './interface/queryClient';
import { initializeGlobalQueryExecutor } from './interface/queryExecutor';
import { createDmlOperations } from './interface/dmlOperations';

/**
 * KuzuDBクライアントを初期化する（オールインワン）
 */
export async function initializeKuzu(connection?: any) {
  // クライアントの初期化
  const queryClient = await initializeGlobalQueryClient(connection);
  const queryExecutor = await initializeGlobalQueryExecutor(connection);
  const dmlOperations = await createDmlOperations();
  
  return {
    queryClient,
    queryExecutor,
    dmlOperations
  };
}

/**
 * 開発用便利関数
 */
export const dev = {
  /**
   * 全てのレイヤーをテストする
   */
  async testAll(connection: any) {
    console.log('=== KuzuDBクライアントのテスト開始 ===');
    
    try {
      // 1. Infrastructure層のテスト
      console.log('1. Infrastructure層のテスト...');
      const { createQueryRepository } = await import('./infrastructure/factories/repositoryFactory');
      const repository = await createQueryRepository();
      const queries = await repository.getAvailableQueries();
      console.log('  ✓ 利用可能なクエリ数:', queries.length);
      
      // 2. Domain層のテスト
      console.log('2. Domain層のテスト...');
      const { createLocationUri } = await import('./domain/entities/locationUri');
      const { validateLocationUri } = await import('./domain/valueObjects/uriValidation');
      const testUri = createLocationUri('file:///test.ts', 'file', '/test.ts');
      const validation = validateLocationUri(testUri.uri_id);
      console.log('  ✓ LocationURIエンティティの作成とバリデーション:', validation.isValid);
      
      // 3. Application層のテスト
      console.log('3. Application層のテスト...');
      const { executeQuery } = await import('./application/commands/executeQuery');
      console.log('  ✓ コマンド層の初期化完了');
      
      // 4. Interface層のテスト
      console.log('4. Interface層のテスト...');
      const kuzu = await initializeKuzu(connection);
      console.log('  ✓ KuzuDBクライアントの初期化完了');
      
      console.log('=== テスト完了 ===');
      return true;
    } catch (error) {
      console.error('テスト失敗:', error);
      return false;
    }
  },
  
  /**
   * デモデータを実行する
   */
  async runDemo(connection: any) {
    console.log('=== デモデータの実行開始 ===');
    
    try {
      const { runDMLDemo } = await import('./interface/dmlOperations');
      const result = await runDMLDemo(connection);
      
      if (result.success) {
        console.log('✓ デモデータの実行が完了しました');
      } else {
        console.error('✗ デモデータの実行に失敗しました:', result.error);
      }
      
      return result;
    } catch (error) {
      console.error('デモ実行中にエラーが発生しました:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }
};

// デフォルトエクスポート
export default {
  initialize: initializeKuzu,
  dev,
  // よく使う関数のエイリアス
  createQueryClient: initializeGlobalQueryClient,
  createQueryExecutor: initializeGlobalQueryExecutor,
  createDmlOperations,
};
