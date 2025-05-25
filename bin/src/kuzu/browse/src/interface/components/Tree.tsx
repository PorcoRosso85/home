/**
 * ツリー表示コンポーネント
 */
import React from 'react';
import TreeNode from './Node';
import type { TreeNode as TreeNodeData } from '../../domain/types';

interface TreeViewProps {
  treeData: TreeNodeData[];
  onNodeClick?: (node: TreeNodeData) => void;
  selectedVersionId?: string;
  onRightClick?: (e: React.MouseEvent) => void;
}

export const TreeView: React.FC<TreeViewProps> = ({ 
  treeData, 
  onNodeClick, 
  selectedVersionId, 
  onRightClick 
}) => {
  return (
    <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
      {treeData.length === 0 ? (
        <p>No data available</p>
      ) : (
        treeData.map((node, index) => (
          <TreeNode
            key={`root-${index}`}
            node={node}
            onNodeClick={onNodeClick}
            selectedVersionId={selectedVersionId}
            onRightClick={onRightClick}
          />
        ))
      )}
    </div>
  );
};
