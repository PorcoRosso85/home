/**
 * ツリー表示コンポーネント
 */
import React from 'react';
import Node from './Node';
import type { NodeData } from '../../domain/types';

interface TreeProps {
  treeData: NodeData[];
  onNodeClick?: (node: NodeData) => void;
}

export const Tree: React.FC<TreeProps> = ({ treeData, onNodeClick }) => {
  return (
    <div style={{ flex: 1, overflowY: 'auto' }}>
      {treeData.length === 0 ? (
        <p>No data available</p>
      ) : (
        treeData.map((node, index) => (
          <Node
            key={`root-${index}`}
            node={node}
            onNodeClick={onNodeClick}
          />
        ))
      )}
    </div>
  );
};
