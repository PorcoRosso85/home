/**
 * ツリー表示コンポーネント（薄いPresentation）
 * Core関数を使用し、React表示のみに責務を限定
 */
import React from 'react';
import Node from './Node';
import type { NodeData, NodeClickEvent } from '../../domain/types';
import { computeTreeStateCore, generateTreeNodeKeyCore } from './tree';

type TreeProps = {
  treeData: NodeData[];
  onNodeClick?: (clickEvent: NodeClickEvent) => void;
};

export const Tree: React.FC<TreeProps> = ({ treeData, onNodeClick }) => {
  // Core関数でツリー状態を計算
  const treeState = computeTreeStateCore({ treeData, onNodeClick });

  return (
    <div style={{ flex: 1, overflowY: 'auto' }}>
      {!treeState.hasData ? (
        <p>{treeState.emptyMessage}</p>
      ) : (
        treeState.renderableNodes.map((node, index) => (
          <Node
            key={generateTreeNodeKeyCore(node.id, index)}
            node={node}
            onNodeClick={onNodeClick}
          />
        ))
      )}
    </div>
  );
};
