import React from 'react';
import type { TreeNodeData } from '../../domain/entity/locationUri';

interface TreeNodeProps {
  node: TreeNodeData;
  level?: number;
  maxDepth?: number;
  onNodeClick?: (node: TreeNodeData) => void;
}

/**
 * 深さに基づいて背景色を計算する関数
 */
export const calculateBackgroundColor = (level: number, maxDepth: number = 10): string => {
  const factor = Math.min(level / maxDepth, 1);
  const colorValue = Math.round(255 - (factor * 40));
  return `rgb(${colorValue}, ${colorValue}, ${colorValue})`;
};

/**
 * 再帰的にツリーノードとその子要素を表示するコンポーネント
 */
const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level = 0,
  maxDepth = 10,
  onNodeClick
}) => {
  const hasChildren = node.children && node.children.length > 0;
  const backgroundColor = calculateBackgroundColor(level, maxDepth);

  return (
    <div 
      style={{
        backgroundColor,
        borderRadius: '4px',
        padding: '8px',
        margin: '4px 0',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        cursor: 'pointer'
      }}
      onClick={(e) => {
        e.stopPropagation();
        onNodeClick && onNodeClick(node);
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <strong>{node.name}</strong> 
          <span style={{ fontSize: '0.8em', color: '#666', marginLeft: '8px' }}>
            {node.type}
          </span>
        </div>
        <div style={{ fontSize: '0.8em', color: '#888' }}>
          {node.id}
        </div>
      </div>
      
      {hasChildren && (
        <div style={{ paddingLeft: '20px', marginTop: '4px' }}>
          {node.children!.map((child, index) => (
            <TreeNode
              key={`${child.id}-${index}`}
              node={child}
              level={level + 1}
              maxDepth={maxDepth}
              onNodeClick={onNodeClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TreeNode;
