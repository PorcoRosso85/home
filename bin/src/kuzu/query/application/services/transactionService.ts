/**
 * トランザクション管理サービス（最小構成）
 * 2段階実行: バリデーション → 安全実行
 */

import type { QueryResult } from '../../domain/types/queryTypes';

export type HierarchyData = {
  parent_id: string;
  child_id: string;
  relation_type: string;
};

export type TransactionResult = {
  success: boolean;
  data?: any;
  errors?: string[];
  validation_errors?: any[];
  rollback?: boolean;
};

/**
 * 安全な階層作成（2段階実行）
 * Step 1: validate_hierarchy_batch.cypher でバリデーション
 * Step 2: create_location_hierarchy_safe.cypher で実行
 */
export async function createHierarchySafe(
  connection: any,
  hierarchies: HierarchyData[]
): Promise<TransactionResult> {
  try {
    // Step 1: バリデーション
    const validationResult = await connection.query(`
      CALL {
        LOAD_CYPHER 'dml/validate_hierarchy_batch.cypher' WITH $hierarchies
      }
    `, { hierarchies });
    
    const validation = await validationResult.getAll();
    const validationData = validation[0]?.validation_result;    
    if (!validationData?.is_valid) {
      return {
        success: false,
        errors: validationData?.errors || ['Unknown validation error'],
        validation_errors: validationData?.errors,
        rollback: true
      };
    }

    // Step 2: 安全実行
    const creationResult = await connection.query(`
      CALL {
        LOAD_CYPHER 'dml/create_location_hierarchy_safe.cypher' WITH $hierarchies
      }
    `, { hierarchies });
    
    const creation = await creationResult.getAll();
    
    return {
      success: true,
      data: creation
    };
    
  } catch (error: any) {
    // 自動ロールバック（Connection終了で実現）
    return {
      success: false,
      errors: [error.message || 'Transaction execution failed'],
      rollback: true
    };
  }
}
/**
 * レガシー互換: 既存APIを保持（後方互換性）
 */
export async function createLocationHierarchy(
  connection: any,
  hierarchies: HierarchyData[]
): Promise<QueryResult> {
  try {
    const result = await connection.query(`
      CALL {
        LOAD_CYPHER 'dml/create_location_hierarchy.cypher' WITH $hierarchies
      }
    `, { hierarchies });
    
    const data = await result.getAll();
    return { status: 'success', data };
    
  } catch (error: any) {
    return {
      status: 'execution_error',
      message: error.message,
      code: 'HIERARCHY_CREATION_FAILED'
    };
  }
}
