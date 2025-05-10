/**
 * KuzuDB DML実行アプリケーション（関数ベース）
 * 
 * このモジュールは、生成されたDMLクエリを順序立てて実行し、
 * 階層型トレーサビリティモデルのデータを構築します。
 */

import { executeQuery } from '../dmlGeneratorBrowser';

type QueryResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
};

/**
 * クエリ実行結果のハンドリング
 */
function handleResult(result: QueryResult<any>, operation: string): void {
  if (result.success) {
    console.log(`  ✓ ${operation}`);
  } else {
    console.error(`  ✗ ${operation}: ${result.error}`);
    throw new Error(`Failed to execute: ${operation}`);
  }
}

/**
 * LocationURIノードを作成
 */
async function createLocationURI(
  connection: any,
  uriId: string, 
  scheme: string, 
  path: string,
  authority?: string,
  fragment?: string,
  query?: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_locationuri', {
    uri_id: uriId,
    scheme: scheme,
    authority: authority || '',
    path: path,
    fragment: fragment || '',
    query: query || ''
  });
  
  handleResult(result, `LocationURI: ${uriId}`);
}

/**
 * CodeEntityノードを作成
 */
async function createCodeEntity(
  connection: any,
  persistentId: string, 
  type: string, 
  signature: string,
  name: string,
  startPosition: number,
  endPosition: number,
  complexity: number = 1
): Promise<void> {
  const result = await executeQuery(connection, 'create_codeentity', {
    persistent_id: persistentId,
    name: name,
    type: type,
    signature: signature,
    complexity: complexity,
    start_position: startPosition,
    end_position: endPosition
  });
  
  handleResult(result, `CodeEntity: ${persistentId}`);
}

/**
 * RequirementEntityノードを作成
 */
async function createRequirement(
  connection: any,
  id: string,
  title: string,
  description: string,
  priority: string,
  requirementType: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_requiremententity', {
    id: id,
    title: title,
    description: description,
    priority: priority,
    requirement_type: requirementType
  });
  
  handleResult(result, `RequirementEntity: ${id}`);
}

/**
 * HAS_LOCATIONエッジを作成
 */
async function createHasLocation(
  connection: any,
  codeEntityId: string, 
  locationUriId: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_has_location', {
    from_id: codeEntityId,
    to_id: locationUriId
  });
  
  handleResult(result, `HAS_LOCATION: ${codeEntityId} -> ${locationUriId}`);
}

/**
 * IS_IMPLEMENTED_BYエッジを作成
 */
async function createIsImplementedBy(
  connection: any,
  requirementId: string, 
  codeEntityId: string, 
  implementationType: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_is_implemented_by', {
    from_id: requirementId,
    to_id: codeEntityId,
    implementation_type: implementationType
  });
  
  handleResult(result, `IS_IMPLEMENTED_BY: ${requirementId} -> ${codeEntityId}`);
}

/**
 * REFERENCES_CODEエッジを作成
 */
async function createReferencesCode(
  connection: any,
  fromCodeId: string, 
  toCodeId: string, 
  refType: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_references_code', {
    from_id: fromCodeId,
    to_id: toCodeId,
    ref_type: refType
  });
  
  handleResult(result, `REFERENCES_CODE: ${fromCodeId} -> ${toCodeId}`);
}

/**
 * VersionStateノードを作成
 */
async function createVersionState(
  connection: any,
  id: string, 
  timestamp: string, 
  description: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_versionstate', {
    id: id,
    timestamp: timestamp,
    description: description
  });
  
  handleResult(result, `VersionState: ${id}`);
}

/**
 * TRACKS_STATE_OF_CODEエッジを作成
 */
async function trackStateOfCode(
  connection: any,
  versionId: string, 
  codeEntityId: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_tracks_state_of_code', {
    from_id: versionId,
    to_id: codeEntityId
  });
  
  handleResult(result, `TRACKS_STATE_OF_CODE: ${versionId} -> ${codeEntityId}`);
}

/**
 * TRACKS_STATE_OF_REQエッジを作成
 */
async function trackStateOfReq(
  connection: any,
  versionId: string, 
  requirementId: string
): Promise<void> {
  const result = await executeQuery(connection, 'create_tracks_state_of_req', {
    from_id: versionId,
    to_id: requirementId
  });
  
  handleResult(result, `TRACKS_STATE_OF_REQ: ${versionId} -> ${requirementId}`);
}

/**
 * デモデータの作成と挿入を順次実行
 */
export async function executeInOrder(connection: any): Promise<void> {
  console.log('=== KuzuDB DML実行開始 ===');
  
  try {
    // 1. LocationURIノードを作成
    console.log('1. LocationURIノードを作成中...');
    await createLocationURI(connection, 'file:///src/main.ts', 'file', '/src/main.ts');
    await createLocationURI(connection, 'file:///src/utils.ts', 'file', '/src/utils.ts');
    await createLocationURI(connection, 'file:///src/components/app.tsx', 'file', '/src/components/app.tsx');
    
    // 2. CodeEntityノードを作成
    console.log('2. CodeEntityノードを作成中...');
    await createCodeEntity(connection, 'main_function', 'function', 'function main()', 'main.ts', 10, 50);
    await createCodeEntity(connection, 'utils_helper', 'function', 'function helper()', 'utils.ts', 20, 35);
    await createCodeEntity(connection, 'app_component', 'class', 'class App extends React.Component', 'app.tsx', 5, 150);
    
    // 3. RequirementEntityノードを作成
    console.log('3. RequirementEntityノードを作成中...');
    await createRequirement(connection, 'REQ-001', 'アプリケーション起動', 'アプリケーションの正常起動要件', 'high', 'functional');
    await createRequirement(connection, 'REQ-002', 'ユーティリティ関数', 'ヘルパー関数の実装要件', 'medium', 'functional');
    
    // 4. HAS_LOCATIONエッジを作成（コードエンティティの位置情報）
    console.log('4. HAS_LOCATIONリレーションシップを作成中...');
    await createHasLocation(connection, 'main_function', 'file:///src/main.ts');
    await createHasLocation(connection, 'utils_helper', 'file:///src/utils.ts');
    await createHasLocation(connection, 'app_component', 'file:///src/components/app.tsx');
    
    // 5. IS_IMPLEMENTED_BYエッジを作成（要件の実装関係）
    console.log('5. IS_IMPLEMENTED_BYリレーションシップを作成中...');
    await createIsImplementedBy(connection, 'REQ-001', 'main_function', 'direct');
    await createIsImplementedBy(connection, 'REQ-002', 'utils_helper', 'direct');
    await createIsImplementedBy(connection, 'REQ-001', 'app_component', 'indirect');
    
    // 6. REFERENCES_CODEエッジを作成（コード間参照）
    console.log('6. REFERENCES_CODEリレーションシップを作成中...');
    await createReferencesCode(connection, 'main_function', 'utils_helper', 'function_call');
    await createReferencesCode(connection, 'app_component', 'main_function', 'import');
    
    // 7. VersionStateノードとTRACKS_STATE_OFエッジを作成
    console.log('7. バージョン管理情報を作成中...');
    await createVersionState(connection, 'v1.0.0', '2025-05-10T10:00:00Z', '初回リリース');
    await trackStateOfCode(connection, 'v1.0.0', 'main_function');
    await trackStateOfCode(connection, 'v1.0.0', 'utils_helper');
    await trackStateOfCode(connection, 'v1.0.0', 'app_component');
    await trackStateOfReq(connection, 'v1.0.0', 'REQ-001');
    await trackStateOfReq(connection, 'v1.0.0', 'REQ-002');
    
    console.log('=== DML実行完了 ===');
  } catch (error) {
    console.error('DML実行中にエラーが発生しました:', error);
    throw error;
  }
}

/**
 * 特定の要件に関連するデータの検証
 */
export async function validateRequirement(connection: any, requirementId: string): Promise<void> {
  console.log(`\n=== 要件 ${requirementId} の検証開始 ===`);
  
  // 1. 要件の実装を確認
  const implementations = await executeQuery(connection, 'find_requirement_implementations', {
    requirement_id: requirementId
  });
  
  if (implementations.success && implementations.data) {
    console.log('実装コード:');
    for (const impl of implementations.data) {
      console.log(`  - ${impl.code_entity_id} (${impl.implementation_type})`);
    }
  }
  
  // 2. コード間の依存関係を確認
  const dependencies = await executeQuery(connection, 'find_code_dependencies', {
    requirement_id: requirementId
  });
  
  if (dependencies.success && dependencies.data) {
    console.log('コード依存関係:');
    for (const dep of dependencies.data) {
      console.log(`  - ${dep.from_code} -> ${dep.to_code} (${dep.ref_type})`);
    }
  }
  
  // 3. バージョン情報を確認
  const versions = await executeQuery(connection, 'find_requirement_versions', {
    requirement_id: requirementId
  });
  
  if (versions.success && versions.data) {
    console.log('関連バージョン:');
    for (const version of versions.data) {
      console.log(`  - ${version.version_id}: ${version.description}`);
    }
  }
  
  console.log(`=== 要件 ${requirementId} の検証完了 ===\n`);
}

/**
 * デモ実行関数
 */
export async function runDMLDemo(connection: any): Promise<void> {
  // 基本データの構築
  await executeInOrder(connection);
  
  // 特定要件の検証
  await validateRequirement(connection, 'REQ-001');
  await validateRequirement(connection, 'REQ-002');
}

/**
 * メイン実行エントリーポイント
 */
if (typeof require !== 'undefined' && require.main === module) {
  console.log('KuzuDB DMLデモの実行');
  // TODO: 実際のKuzuDBコネクション初期化
  // const connection = await getKuzuConnection();
  // await runDMLDemo(connection);
}
