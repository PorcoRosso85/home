/**
 * ツリー表示コンポーネント
 * 遅延ロード機能を追加
 * 
 * TODO: 非同期処理中の状態を適切に処理し、モックデータを使用しない
 */

import React, { useCallback } from 'react';
import TreeNode from './TreeNode';
import type { TreeNode as TreeNodeData } from '../../domain/types';

interface TreeViewProps {
  treeData: TreeNodeData[];
  onNodeClick?: (nodeId: string) => void;
  onNodeToggle?: (nodeId: string) => void;
  onNodeSelect?: (nodeId: string) => void;
  loading?: boolean;
  error?: string | null;
}

/**
 * ツリービューコンポーネント
 */
export const TreeView: React.FC<TreeViewProps> = ({
  treeData,
  onNodeClick,
  onNodeToggle,
  onNodeSelect,
  loading = false,
  error = null
}) => {
  // ノードクリックハンドラ
  const handleNodeClick = useCallback((nodeId: string) => {
    if (onNodeClick) {
      onNodeClick(nodeId);
    }
  }, [onNodeClick]);
  
  // ノードトグルハンドラ
  const handleNodeToggle = useCallback((nodeId: string) => {
    if (onNodeToggle) {
      onNodeToggle(nodeId);
    }
  }, [onNodeToggle]);
  
  // ノード選択ハンドラ
  const handleNodeSelect = useCallback((nodeId: string) => {
    if (onNodeSelect) {
      onNodeSelect(nodeId);
    }
  }, [onNodeSelect]);
  
  // ローディング状態
  if (loading) {
    return (
      <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
        <h2>KuzuDB Graph Browser</h2>
        <p>データを読み込んでいます...</p>
      </div>
    );
  }
  
  // エラー状態
  if (error) {
    return (
      <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
        <h2>KuzuDB Graph Browser</h2>
        <p style={{ color: 'red' }}>エラーが発生しました: {error}</p>
      </div>
    );
  }
  
  return (
    <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
      <h2>KuzuDB Graph Browser</h2>
      {treeData.length === 0 ? (
        <p>データがありません</p>
      ) : (
        treeData.map((node, index) => (
          <TreeNode
            key={`root-${index}-${node.id}`}
            node={node}
            onNodeClick={handleNodeClick}
            onNodeToggle={handleNodeToggle}
            onNodeSelect={handleNodeSelect}
          />
        ))
      )}
    </div>
  );
};

export default TreeView;
