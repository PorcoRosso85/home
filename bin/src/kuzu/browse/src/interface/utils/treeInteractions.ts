/**
 * 最小構成でツリーの操作ロジックを提供するユーティリティ
 */

import { TreeNode } from '../../domain/types';

/**
 * ノードの展開/折りたたみを切り替える
 */
export function toggleTreeNode(nodes: TreeNode[], nodeId: string): TreeNode[] {
  return nodes.map(node => {
    if (node.id === nodeId) {
      return { ...node, isExpanded: !node.isExpanded };
    } else if (node.children && node.children.length > 0) {
      return { ...node, children: toggleTreeNode(node.children, nodeId) };
    }
    return node;
  });
}

/**
 * ノードのロード状態を設定する
 */
export function setNodeLoading(nodes: TreeNode[], nodeId: string, loading: boolean): TreeNode[] {
  return nodes.map(node => {
    if (node.id === nodeId) {
      return { ...node, isLoading: loading };
    } else if (node.children && node.children.length > 0) {
      return { ...node, children: setNodeLoading(node.children, nodeId, loading) };
    }
    return node;
  });
}

/**
 * ノードに子ノードを追加する
 */
export function addChildrenToNode(nodes: TreeNode[], nodeId: string, children: TreeNode[]): TreeNode[] {
  return nodes.map(node => {
    if (node.id === nodeId) {
      return { ...node, children, isLoading: false, isExpanded: true };
    } else if (node.children && node.children.length > 0) {
      return { ...node, children: addChildrenToNode(node.children, nodeId, children) };
    }
    return node;
  });
}
