/**
 * ノード詳細表示パネルコンポーネント
 */
import React from 'react';
import { TreeNodeData } from './TreeNode';

interface NodeDetailsPanelProps {
  selectedNode: TreeNodeData | null;
}

export const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({ selectedNode }) => {
  if (!selectedNode) {
    return null;
  }

  return (
    <div style={{ 
      flex: 1, 
      padding: '15px',
      backgroundColor: '#f5f5f5',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h3>Node Details</h3>
      <div>
        <p><strong>ID:</strong> {selectedNode.id}</p>
        <p><strong>Type:</strong> {selectedNode.type}</p>
        <p><strong>Name:</strong> {selectedNode.name}</p>
        <p><strong>URI:</strong> {selectedNode.uri}</p>
        <h4>Properties:</h4>
        <pre style={{ 
          backgroundColor: '#e8e8e8', 
          padding: '10px', 
          borderRadius: '4px' 
        }}>
          {JSON.stringify(selectedNode.properties, null, 2)}
        </pre>
      </div>
    </div>
  );
};
