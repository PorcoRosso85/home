/**
 * ツリー表示コンポーネント
 */
import React from 'react';
import TreeNode from './TreeNode';
import type { TreeNode as TreeNodeData } from '../../domain/types';

interface TreeViewProps {
  treeData: TreeNodeData[];
  onNodeClick?: (node: TreeNodeData) => void;
}

export const TreeView: React.FC<TreeViewProps> = ({ treeData, onNodeClick }) => {
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
          />
        ))
      )}
    </div>
  );
};
