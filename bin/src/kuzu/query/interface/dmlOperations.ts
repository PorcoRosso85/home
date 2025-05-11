/**
 * DML Operations - DML操作用API
 * 
 * データ操作言語（DML）に特化した操作関数群
 */

import type { QueryResult } from '../domain/entities/queryResult';
import type { LocationUriEntity } from '../domain/entities/locationUri';
import type { VersionStateEntity } from '../domain/entities/versionState';
import { createQueryRepository } from '../infrastructure/factories/repositoryFactory';
import { validateLocationUri, validateLocationUriObject } from '../domain/valueObjects/uriValidation';

/**
 * DML操作の基本インターフェース
 */
export type DmlOperations = {
  /**
   * LocationURIノードを作成
   */
  createLocationURI: (
    connection: any,
    uriId: string,
    scheme: string,
    path: string,
    authority?: string,
    fragment?: string,
    query?: string
  ) => Promise<QueryResult<LocationUriEntity>>;
  
  /**
   * CodeEntityノードを作成
   */
  createCodeEntity: (
    connection: any,
    persistentId: string,
    type: string,
    signature: string,
    name: string,
    startPosition: number,
    endPosition: number,
    complexity?: number
  ) => Promise<QueryResult<any>>;
  
  /**
   * RequirementEntityノードを作成
   */
  createRequirement: (
    connection: any,
    id: string,
    title: string,
    description: string,
    priority: string,
    requirementType: string
  ) => Promise<QueryResult<any>>;
  
  /**
   * VersionStateノードを作成
   */
  createVersionState: (
    connection: any,
    id: string,
    timestamp: string,
    description: string
  ) => Promise<QueryResult<VersionStateEntity>>;
  
  /**
   * HAS_LOCATIONエッジを作成
   */
  createHasLocation: (
    connection: any,
    codeEntityId: string,
    locationUriId: string
  ) => Promise<QueryResult<any>>;
  
  /**
   * IS_IMPLEMENTED_BYエッジを作成
   */
  createIsImplementedBy: (
    connection: any,
    requirementId: string,
    codeEntityId: string,
    implementationType: string
  ) => Promise<QueryResult<any>>;
  
  /**
   * REFERENCES_CODEエッジを作成
   */
  createReferencesCode: (
    connection: any,
    fromCodeId: string,
    toCodeId: string,
    refType: string
  ) => Promise<QueryResult<any>>;
  
  /**
   * TRACKS_STATE_OF_CODEエッジを作成
   */
  trackStateOfCode: (
    connection: any,
    versionId: string,
    codeEntityId: string
  ) => Promise<QueryResult<any>>;
  
  /**
   * TRACKS_STATE_OF_REQエッジを作成
   */
  trackStateOfReq: (
    connection: any,
    versionId: string,
    requirementId: string
  ) => Promise<QueryResult<any>>;
  
  /**
   * 完全なデモデータセットを実行
   */
  executeInOrder: (connection: any) => Promise<QueryResult<void>>;
  
  /**
   * 要件の検証を実行
   */
  validateRequirement: (connection: any, requirementId: string) => Promise<QueryResult<any>>;
};

/**
 * DML操作を実装する
 */
export async function createDmlOperations(): Promise<DmlOperations> {
  const repository = await createQueryRepository();
  
  return {
    async createLocationURI(
      connection: any,
      uriId: string,
      scheme: string,
      path: string,
      authority?: string,
      fragment?: string,
      query?: string
    ): Promise<QueryResult<LocationUriEntity>> {
      try {
        // バリデーション：入力URIの検証
        const parsedUri = validateLocationUri(uriId);
        if (!parsedUri.isValid) {
          return {
            success: false,
            error: `Invalid URI: ${uriId} - ${parsedUri.error}`
          };
        }
        
        // LocationUriオブジェクトの構築
        const locationUri: LocationUriEntity = {
          uri_id: uriId,
          scheme: scheme,
          authority: authority || '',
          path: path,
          fragment: fragment || '',
          query: query || ''
        };
        
        // バリデーション：LocationUriオブジェクトの検証
        const objectValidation = validateLocationUriObject(locationUri);
        if (!objectValidation.isValid) {
          return {
            success: false,
            error: `Invalid LocationUri object: ${objectValidation.error}`
          };
        }
        
        const result = await repository.executeQuery(connection, 'create_locationuri', locationUri);
        
        if (result.success) {
          return {
            success: true,
            data: locationUri
          };
        }
        
        return result as QueryResult<LocationUriEntity>;
      } catch (error) {
        return {
          success: false,
          error: `Error creating LocationURI: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async createCodeEntity(
      connection: any,
      persistentId: string,
      type: string,
      signature: string,
      name: string,
      startPosition: number,
      endPosition: number,
      complexity: number = 1
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          persistent_id: persistentId,
          name,
          type,
          signature,
          complexity,
          start_position: startPosition,
          end_position: endPosition
        };
        
        return await repository.executeQuery(connection, 'create_codeentity', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating CodeEntity: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async createRequirement(
      connection: any,
      id: string,
      title: string,
      description: string,
      priority: string,
      requirementType: string
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          id,
          title,
          description,
          priority,
          requirement_type: requirementType
        };
        
        return await repository.executeQuery(connection, 'create_requiremententity', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating Requirement: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async createVersionState(
      connection: any,
      id: string,
      timestamp: string,
      description: string
    ): Promise<QueryResult<VersionStateEntity>> {
      try {
        const params = { id, timestamp, description };
        
        const result = await repository.executeQuery(connection, 'create_versionstate', params);
        
        if (result.success) {
          const versionState: VersionStateEntity = {
            id,
            timestamp,
            description
          };
          
          return {
            success: true,
            data: versionState
          };
        }
        
        return result as QueryResult<VersionStateEntity>;
      } catch (error) {
        return {
          success: false,
          error: `Error creating VersionState: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async createHasLocation(
      connection: any,
      codeEntityId: string,
      locationUriId: string
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          from_id: codeEntityId,
          to_id: locationUriId
        };
        
        return await repository.executeQuery(connection, 'create_has_location', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating HAS_LOCATION: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async createIsImplementedBy(
      connection: any,
      requirementId: string,
      codeEntityId: string,
      implementationType: string
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          from_id: requirementId,
          to_id: codeEntityId,
          implementation_type: implementationType
        };
        
        return await repository.executeQuery(connection, 'create_is_implemented_by', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating IS_IMPLEMENTED_BY: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async createReferencesCode(
      connection: any,
      fromCodeId: string,
      toCodeId: string,
      refType: string
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          from_id: fromCodeId,
          to_id: toCodeId,
          ref_type: refType
        };
        
        return await repository.executeQuery(connection, 'create_references_code', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating REFERENCES_CODE: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async trackStateOfCode(
      connection: any,
      versionId: string,
      codeEntityId: string
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          from_id: versionId,
          to_id: codeEntityId
        };
        
        return await repository.executeQuery(connection, 'create_tracks_state_of_code', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating TRACKS_STATE_OF_CODE: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async trackStateOfReq(
      connection: any,
      versionId: string,
      requirementId: string
    ): Promise<QueryResult<any>> {
      try {
        const params = {
          from_id: versionId,
          to_id: requirementId
        };
        
        return await repository.executeQuery(connection, 'create_tracks_state_of_req', params);
      } catch (error) {
        return {
          success: false,
          error: `Error creating TRACKS_STATE_OF_REQ: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async executeInOrder(connection: any): Promise<QueryResult<void>> {
      try {
        console.log('=== KuzuDB DML実行開始 ===');
        
        // 1. LocationURIノードを作成
        console.log('1. LocationURIノードを作成中...');
        const locationUriResults = await Promise.all([
          this.createLocationURI(connection, 'file:///src/main.ts', 'file', '/src/main.ts'),
          this.createLocationURI(connection, 'file:///src/utils.ts', 'file', '/src/utils.ts'),
          this.createLocationURI(connection, 'file:///src/components/app.tsx', 'file', '/src/components/app.tsx')
        ]);
        
        if (locationUriResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create LocationURI nodes'
          };
        }
        
        // 2. CodeEntityノードを作成
        console.log('2. CodeEntityノードを作成中...');
        const codeEntityResults = await Promise.all([
          this.createCodeEntity(connection, 'main_function', 'function', 'function main()', 'main.ts', 10, 50),
          this.createCodeEntity(connection, 'utils_helper', 'function', 'function helper()', 'utils.ts', 20, 35),
          this.createCodeEntity(connection, 'app_component', 'class', 'class App extends React.Component', 'app.tsx', 5, 150)
        ]);
        
        if (codeEntityResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create CodeEntity nodes'
          };
        }
        
        // 3. RequirementEntityノードを作成
        console.log('3. RequirementEntityノードを作成中...');
        const requirementResults = await Promise.all([
          this.createRequirement(connection, 'REQ-001', 'アプリケーション起動', 'アプリケーションの正常起動要件', 'high', 'functional'),
          this.createRequirement(connection, 'REQ-002', 'ユーティリティ関数', 'ヘルパー関数の実装要件', 'medium', 'functional')
        ]);
        
        if (requirementResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create Requirement nodes'
          };
        }
        
        // 4. HAS_LOCATIONエッジを作成
        console.log('4. HAS_LOCATIONリレーションシップを作成中...');
        const hasLocationResults = await Promise.all([
          this.createHasLocation(connection, 'main_function', 'file:///src/main.ts'),
          this.createHasLocation(connection, 'utils_helper', 'file:///src/utils.ts'),
          this.createHasLocation(connection, 'app_component', 'file:///src/components/app.tsx')
        ]);
        
        if (hasLocationResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create HAS_LOCATION relationships'
          };
        }
        
        // 5. IS_IMPLEMENTED_BYエッジを作成
        console.log('5. IS_IMPLEMENTED_BYリレーションシップを作成中...');
        const implementationResults = await Promise.all([
          this.createIsImplementedBy(connection, 'REQ-001', 'main_function', 'direct'),
          this.createIsImplementedBy(connection, 'REQ-002', 'utils_helper', 'direct'),
          this.createIsImplementedBy(connection, 'REQ-001', 'app_component', 'indirect')
        ]);
        
        if (implementationResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create IS_IMPLEMENTED_BY relationships'
          };
        }
        
        // 6. REFERENCES_CODEエッジを作成
        console.log('6. REFERENCES_CODEリレーションシップを作成中...');
        const referenceResults = await Promise.all([
          this.createReferencesCode(connection, 'main_function', 'utils_helper', 'function_call'),
          this.createReferencesCode(connection, 'app_component', 'main_function', 'import')
        ]);
        
        if (referenceResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create REFERENCES_CODE relationships'
          };
        }
        
        // 7. VersionStateノードとTRACKS_STATE_OFエッジを作成
        console.log('7. バージョン管理情報を作成中...');
        const versionResult = await this.createVersionState(connection, 'v1.0.0', '2025-05-10T10:00:00Z', '初回リリース');
        
        if (!versionResult.success) {
          return {
            success: false,
            error: 'Failed to create VersionState node'
          };
        }
        
        const trackingResults = await Promise.all([
          this.trackStateOfCode(connection, 'v1.0.0', 'main_function'),
          this.trackStateOfCode(connection, 'v1.0.0', 'utils_helper'),
          this.trackStateOfCode(connection, 'v1.0.0', 'app_component'),
          this.trackStateOfReq(connection, 'v1.0.0', 'REQ-001'),
          this.trackStateOfReq(connection, 'v1.0.0', 'REQ-002')
        ]);
        
        if (trackingResults.some(r => !r.success)) {
          return {
            success: false,
            error: 'Failed to create TRACKS_STATE_OF relationships'
          };
        }
        
        console.log('=== DML実行完了 ===');
        
        return {
          success: true,
          data: undefined
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to execute DML operations: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async validateRequirement(connection: any, requirementId: string): Promise<QueryResult<any>> {
      try {
        console.log(`\n=== 要件 ${requirementId} の検証開始 ===`);
        
        // 1. 要件の実装を確認
        const implementations = await repository.executeQuery(connection, 'find_requirement_implementations', {
          requirement_id: requirementId
        });
        
        if (implementations.success && implementations.data) {
          console.log('実装コード:');
          for (const impl of implementations.data) {
            console.log(`  - ${impl.code_entity_id} (${impl.implementation_type})`);
          }
        }
        
        // 2. コード間の依存関係を確認
        const dependencies = await repository.executeQuery(connection, 'find_code_dependencies', {
          requirement_id: requirementId
        });
        
        if (dependencies.success && dependencies.data) {
          console.log('コード依存関係:');
          for (const dep of dependencies.data) {
            console.log(`  - ${dep.from_code} -> ${dep.to_code} (${dep.ref_type})`);
          }
        }
        
        // 3. バージョン情報を確認
        const versions = await repository.executeQuery(connection, 'find_requirement_versions', {
          requirement_id: requirementId
        });
        
        if (versions.success && versions.data) {
          console.log('関連バージョン:');
          for (const version of versions.data) {
            console.log(`  - ${version.version_id}: ${version.description}`);
          }
        }
        
        console.log(`=== 要件 ${requirementId} の検証完了 ===\n`);
        
        return {
          success: true,
          data: {
            implementations: implementations.data,
            dependencies: dependencies.data,
            versions: versions.data
          }
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to validate requirement: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    }
  };
}

/**
 * デモ実行関数
 */
export async function runDMLDemo(connection: any): Promise<QueryResult<void>> {
  try {
    const dmlOps = await createDmlOperations();
    
    // 基本データの構築
    const executeResult = await dmlOps.executeInOrder(connection);
    if (!executeResult.success) {
      return executeResult;
    }
    
    // 特定要件の検証
    const validationResults = await Promise.all([
      dmlOps.validateRequirement(connection, 'REQ-001'),
      dmlOps.validateRequirement(connection, 'REQ-002')
    ]);
    
    if (validationResults.some(r => !r.success)) {
      return {
        success: false,
        error: 'Some validation operations failed'
      };
    }
    
    return {
      success: true,
      data: undefined
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to run DML demo: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}
