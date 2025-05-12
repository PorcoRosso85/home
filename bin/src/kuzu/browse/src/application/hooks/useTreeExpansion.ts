/**
 * 最小構成でツリーの展開状態を管理するフック
 */

import { useReducer, useCallback } from 'react';
import { TreeNode } from '../../domain/types';
import { toggleTreeNode, setNodeLoading, addChildrenToNode } from '../../interface/utils/treeInteractions';

// アクションタイプ
type Action = 
  | { type: 'TOGGLE_NODE'; nodeId: string }
  | { type: 'SET_LOADING'; nodeId: string; loading: boolean }
  | { type: 'ADD_CHILDREN'; nodeId: string; children: TreeNode[] }
  | { type: 'SET_TREE'; tree: TreeNode[] };

// リデューサー
function treeReducer(state: TreeNode[], action: Action): TreeNode[] {
  switch (action.type) {
    case 'TOGGLE_NODE':
      return toggleTreeNode(state, action.nodeId);
    case 'SET_LOADING':
      return setNodeLoading(state, action.nodeId, action.loading);
    case 'ADD_CHILDREN':
      return addChildrenToNode(state, action.nodeId, action.children);
    case 'SET_TREE':
      return action.tree;
    default:
      return state;
  }
}

/**
 * ツリーの展開状態を管理するフック
 */
export function useTreeExpansion(initialTree: TreeNode[] = []) {
  const [tree, dispatch] = useReducer(treeReducer, initialTree);
  
  const setTree = useCallback((newTree: TreeNode[]) => {
    dispatch({ type: 'SET_TREE', tree: newTree });
  }, []);
  
  const toggleNode = useCallback((nodeId: string) => {
    dispatch({ type: 'TOGGLE_NODE', nodeId });
  }, []);
  
  const setNodeLoading = useCallback((nodeId: string, loading: boolean) => {
    dispatch({ type: 'SET_LOADING', nodeId, loading });
  }, []);
  
  const addChildrenToNode = useCallback((nodeId: string, children: TreeNode[]) => {
    dispatch({ type: 'ADD_CHILDREN', nodeId, children });
  }, []);
  
  return {
    tree,
    setTree,
    toggleNode,
    setNodeLoading,
    addChildrenToNode
  };
}
