/**
 * 最小構成でバージョンツリーの構築に関連する機能を提供する
 */

import type { TreeNode, VersionState } from '../../domain/types';
import * as logger from '../../../../common/infrastructure/logger';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';

/**
 * データベースからバージョン履歴を取得する
 */
export async function getVersionHistory(dbConnection: any): Promise<VersionState[]> {
  try {
    const result = await executeDQLQuery(dbConnection, 'get_all_versions', {});
    
    if (!result.success || !result.data) {
      logger.error('バージョン履歴取得エラー:', result.error);
      return [];
    }
    
    const queryResult = await result.data.getAllObjects();
    
    return queryResult.map(row => ({
      id: row.version_id,
      timestamp: row.timestamp || new Date().toISOString(),
      description: row.description || '',
      change_reason: row.change_reason || ''
    }));
  } catch (error) {
    logger.error('バージョン履歴取得エラー:', error);
    return [];
  }
}

/**
 * バージョン間のFOLLOWS関係を取得する
 */
export async function getVersionFollows(dbConnection: any): Promise<Array<{ from: string; to: string }>> {
  try {
    const result = await executeDQLQuery(dbConnection, 'version_follows_relation', {});
    
    if (!result.success || !result.data) {
      logger.error('FOLLOWS関係取得エラー:', result.error);
      return [];
    }
    
    const queryResult = await result.data.getAllObjects();
    
    return queryResult.map(row => ({
      from: row.from_version_id,
      to: row.to_version_id
    }));
  } catch (error) {
    logger.error('FOLLOWS関係取得エラー:', error);
    return [];
  }
}

/**
 * バージョンの親子関係が存在するか判定する
 */
function isParentChild(parentId: string, childId: string): boolean {
  // バージョン形式を考慮した親子関係の判定
  const parentParts = parentId.replace(/^v/, '').split('.').map(Number);
  const childParts = childId.replace(/^v/, '').split('.').map(Number);
  
  // 子のセグメント数が親より少ない場合は親子関係にない
  if (childParts.length <= parentParts.length) {
    return false;
  }
  
  // 親のすべてのセグメントが子のセグメントと一致するか確認
  for (let i = 0; i < parentParts.length; i++) {
    if (parentParts[i] !== childParts[i]) {
      return false;
    }
  }
  
  return true;
}

/**
 * バージョンツリーを構築する
 */
function constructVersionTree(versions: VersionState[], follows: Array<{ from: string; to: string }> = []): TreeNode[] {
  // バージョンノードのマップを作成
  const nodeMap: Record<string, TreeNode> = {};
  
  // バージョンノードを作成
  versions.forEach(version => {
    nodeMap[version.id] = {
      id: version.id,
      name: version.id,
      nodeType: 'version',
      children: [],
      description: version.description,
      change_reason: version.change_reason,
      timestamp: version.timestamp,
      isExpanded: false
    };
  });
  
  // FOLLOWS関係が存在する場合はそれを使用
  const childToParent: Record<string, string> = {};
  
  if (follows.length > 0) {
    // FOLLOWS関係から親子マップを構築
    follows.forEach(relation => {
      childToParent[relation.from] = relation.to;
    });
  } else {
    // FOLLOWS関係がない場合はバージョン形式から親子関係を推測
    versions.forEach(version => {
      for (const otherVersion of versions) {
        if (version.id !== otherVersion.id && isParentChild(otherVersion.id, version.id)) {
          childToParent[version.id] = otherVersion.id;
          break;
        }
      }
    });
  }
  
  // ツリー構造を構築
  const rootNodes: TreeNode[] = [];
  
  Object.keys(nodeMap).forEach(versionId => {
    const parentId = childToParent[versionId];
    
    if (parentId && nodeMap[parentId]) {
      // 親が存在する場合は、親ノードの子として追加
      nodeMap[parentId].children.push(nodeMap[versionId]);
    } else {
      // 親が存在しない場合はルートノードとして追加
      rootNodes.push(nodeMap[versionId]);
    }
  });
  
  return rootNodes;
}

/**
 * バージョンツリーを構築する
 */
export async function buildVersionTreeUsecase(dbConnection: any): Promise<TreeNode[]> {
  if (!dbConnection) {
    logger.error('データベース接続がありません');
    return [];
  }
  
  try {
    // バージョン履歴を取得
    const versions = await getVersionHistory(dbConnection);
    
    if (versions.length === 0) {
      logger.debug('バージョンデータが存在しません');
      return [];
    }
    
    // FOLLOWS関係を取得
    const follows = await getVersionFollows(dbConnection);
    
    // ツリー構造を構築
    return constructVersionTree(versions, follows);
  } catch (error) {
    logger.error('バージョンツリー構築エラー:', error);
    return [];
  }
}
