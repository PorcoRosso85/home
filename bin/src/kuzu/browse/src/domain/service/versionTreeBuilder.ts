/**
 * バージョン間のFOLLOWS関係に基づいてツリー構造を構築する関数
 * 
 * TODO: バージョンノードごとにid, name, nodeType, childrenプロパティを設定
 */

import type { TreeNode, VersionState } from '../types';
import { isParentChildRelationship } from '../../application/utils/versionComparator';

/**
 * バージョンツリーのノードを構築する
 */
export function buildVersionNode(version: VersionState): TreeNode {
  return {
    id: version.id,
    name: `v${version.id.replace(/^v/, '')}`,
    nodeType: 'version' as const,
    children: [],
    description: version.description,
    change_reason: version.change_reason,
    timestamp: version.timestamp,
    isExpanded: false,
    isLoading: false
  };
}

/**
 * バージョン間の親子関係を検出し、ツリー構造を構築する
 */
export function buildVersionTreeFromList(versions: VersionState[]): TreeNode[] {
  const nodes: Record<string, TreeNode> = {};
  const rootNodes: TreeNode[] = [];
  
  // バージョンノードを作成
  versions.forEach(version => {
    nodes[version.id] = buildVersionNode(version);
  });
  
  // バージョンをソート（セマンティックバージョニング順）
  const sortedVersions = [...versions].sort((a, b) => {
    const aParts = a.id.replace(/^v/, '').split('.').map(Number);
    const bParts = b.id.replace(/^v/, '').split('.').map(Number);
    
    // セグメント単位で比較
    const minLength = Math.min(aParts.length, bParts.length);
    for (let i = 0; i < minLength; i++) {
      if (aParts[i] !== bParts[i]) {
        return aParts[i] - bParts[i];
      }
    }
    
    // セグメント数で比較
    return aParts.length - bParts.length;
  });
  
  // 親子関係を構築
  sortedVersions.forEach(version => {
    let foundParent = false;
    
    for (let i = sortedVersions.length - 1; i >= 0; i--) {
      const potentialParent = sortedVersions[i];
      
      if (version.id === potentialParent.id) {
        continue; // 自分自身はスキップ
      }
      
      if (isParentChildRelationship(potentialParent.id, version.id)) {
        nodes[potentialParent.id].children.push(nodes[version.id]);
        foundParent = true;
        break;
      }
    }
    
    // 親が見つからない場合はルートノードに追加
    if (!foundParent) {
      rootNodes.push(nodes[version.id]);
    }
  });
  
  return rootNodes;
}

/**
 * FOLLOWS関係からバージョンツリーを構築する
 * バージョン間のFOLLOWS関係が明示的に定義されている場合に使用
 */
export function buildVersionTreeFromFollows(
  versions: VersionState[],
  follows: Array<{ from: string; to: string }>
): TreeNode[] {
  const nodes: Record<string, TreeNode> = {};
  const childToParent: Record<string, string> = {};
  
  // バージョンノードを作成
  versions.forEach(version => {
    nodes[version.id] = buildVersionNode(version);
  });
  
  // FOLLOWS関係から親子マップを構築
  follows.forEach(relation => {
    childToParent[relation.from] = relation.to;
  });
  
  // ツリー構造を構築
  const rootNodes: TreeNode[] = [];
  
  versions.forEach(version => {
    const parentId = childToParent[version.id];
    
    if (parentId && nodes[parentId]) {
      // 親が存在する場合は、親ノードの子として追加
      nodes[parentId].children.push(nodes[version.id]);
    } else {
      // 親が存在しない場合はルートノードとして追加
      rootNodes.push(nodes[version.id]);
    }
  });
  
  return rootNodes;
}

/**
 * バージョンと明示的な親子関係情報からツリーを構築する
 * バージョンの形式とFOLLOWS関係の両方を考慮
 */
export function buildVersionTree(
  versions: VersionState[],
  follows?: Array<{ from: string; to: string }>
): TreeNode[] {
  // FOLLOWS関係が提供されている場合はそれを使用
  if (follows && follows.length > 0) {
    return buildVersionTreeFromFollows(versions, follows);
  }
  
  // そうでなければ、バージョン形式から親子関係を推測
  return buildVersionTreeFromList(versions);
}
