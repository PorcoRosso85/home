/**
 * ツリー表示コンポーネント
 */
import React from 'react';
import TreeNode from './TreeNode';
import type { TreeNodeData } from '../../domain/entity/locationUri';

interface TreeViewProps {
  treeData: TreeNodeData[];
  onNodeClick?: (node: TreeNodeData) => void;
}

export const TreeView: React.FC<TreeViewProps> = ({ treeData, onNodeClick }) => {
  return (
    <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
      <h2>KuzuDB Graph Browser</h2>
      {treeData.length === 0 ? (
        <p>No data available</p>
      ) : (
        treeData.map((node, index) => (
          <TreeNode
            key={`root-${index}`}
            node={node}
            // onNodeClick={onNodeClick}
          />
        ))
      )}
    </div>
  );
};
