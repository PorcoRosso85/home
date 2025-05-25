import React from 'react';
import type { TreeNode as TreeNodeData } from '../../domain/types';

interface TreeNodeProps {
  node: TreeNodeData;
  onNodeClick?: (node: TreeNodeData) => void;
  parentOpacity?: number; // 親からの透明度を受け取る
}

/**
 * 再帰的にツリーノードとその子要素を表示するコンポーネント
 * 親要素の重なりが子要素にも適用される実装
 */
const TreeNode: React.FC<TreeNodeProps> = ({ node, onNodeClick, parentOpacity = 0 }) => {
  const hasChildren = node.children && node.children.length > 0;
  
  // 現在の要素の透明度：親からの透明度 + 自分の透明度
  const currentOpacity = parentOpacity + 0.02;
  
  // 実際の背景色を計算
  const backgroundOpacity = Math.min(currentOpacity, 0.3); // 最大30%まで
  let backgroundColor = `rgba(0, 0, 0, ${backgroundOpacity})`;
  
  // 未完了の場合、薄赤色の背景色にする
  if (!hasChildren && node.isCompleted === false) {
    backgroundColor = `rgba(255, 200, 200, 0.3)`; // 薄赤色
  }
  
  // バージョンノードの場合、異なる背景色を使用
  if (node.nodeType === 'version') {
    backgroundColor = `rgba(230, 240, 255, ${backgroundOpacity + 0.2})`;
  }
  
  // 背景の暗さに応じて文字色を調整
  const textColor = backgroundOpacity > 0.15 || (!hasChildren && node.isCompleted === false) ? 'white' : 'black';
  const secondaryTextColor = backgroundOpacity > 0.15 || (!hasChildren && node.isCompleted === false) ? '#ccc' : '#666';
  const tertiaryTextColor = backgroundOpacity > 0.15 || (!hasChildren && node.isCompleted === false) ? '#aaa' : '#888';
  
  // バージョン情報による色分け
  const nodeTextColor = node.isCurrentVersion ? '#0066cc' : textColor;
  
  // ノードクリックのハンドラ
  const handleClick = () => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  return (
    <div 
      style={{
        position: 'relative',
        padding: '8px',
        margin: '4px 0',
        borderRadius: '4px',
        // 計算された背景色を適用
        background: backgroundColor,
        cursor: onNodeClick ? 'pointer' : 'default'
      }}
      onClick={handleClick}
    >
      {/* コンテンツ */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <strong style={{ color: nodeTextColor }}>{node.name}</strong> 
            {node.from_version && (
              <span style={{ fontSize: '0.8em', color: secondaryTextColor, marginLeft: '8px' }}>
                ({node.from_version})
              </span>
            )}
            {node.description && (
              <span style={{ fontSize: '0.8em', color: secondaryTextColor, marginLeft: '8px' }}>
                ({node.description})
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.8em', color: tertiaryTextColor }}>
            {node.id}
          </div>
        </div>
      </div>
      
      {/* 子要素 */}
      {hasChildren && (
        <div style={{ paddingLeft: '20px', marginTop: '4px' }}>
          {node.children!.map((child, index) => (
            <TreeNode
              key={`${child.id || index}-${index}`}
              node={child}
              parentOpacity={currentOpacity} // 親の透明度を子に渡す
              onNodeClick={onNodeClick} // 子ノードにもクリックハンドラを渡す
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TreeNode;
