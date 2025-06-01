/**
 * ノード表示コンポーネント（薄いPresentation）
 */
import React from 'react';
import type { NodeData, NodeClickEvent } from '../../domain/types';
import { computeNodeStateCore, generateNodeKeyCore } from './node';

type NodeProps = {
  node: NodeData;
  onNodeClick?: (clickEvent: NodeClickEvent) => void;
  parentOpacity: number;
};

const Node: React.FC<NodeProps> = ({ node, onNodeClick, parentOpacity }) => {
  const nodeState = computeNodeStateCore({ node, onNodeClick, parentOpacity });

  return (
    <div 
      style={{
        position: 'relative',
        padding: '8px',
        margin: '4px 0',
        borderRadius: '4px',
        background: nodeState.styles.backgroundColor,
        cursor: onNodeClick ? 'pointer' : 'default'
      }}
      onClick={nodeState.handleClick}
      onContextMenu={nodeState.handleContextMenu}
    >
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <strong style={{ color: nodeState.styles.nodeTextColor }}>{node.name}</strong> 
            {node.from_version && (
              <span style={{ fontSize: '0.8em', color: nodeState.styles.secondaryTextColor, marginLeft: '8px' }}>
                ({node.from_version})
              </span>
            )}
            {node.description && (
              <span style={{ fontSize: '0.8em', color: nodeState.styles.secondaryTextColor, marginLeft: '8px' }}>
                ({node.description})
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.8em', color: nodeState.styles.tertiaryTextColor }}>
            {node.id}
          </div>
        </div>
      </div>
      
      {nodeState.hasChildren && (
        <div style={{ paddingLeft: '20px', marginTop: '4px' }}>
          {node.children!.map((child, index) => (
            <Node
              key={generateNodeKeyCore(child.id, index)}
              node={child}
              parentOpacity={nodeState.styles.currentOpacity}
              onNodeClick={onNodeClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Node;
