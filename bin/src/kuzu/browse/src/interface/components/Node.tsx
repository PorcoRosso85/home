import React from 'react';
import type { NodeData } from '../../domain/types';

interface NodeProps {
  node: NodeData;
  onNodeClick?: (node: NodeData) => void;
  parentOpacity?: number; // 親からの透明度を受け取る
}

/**
 * 再帰的にツリーノードとその子要素を表示するコンポーネント
 * 親要素の重なりが子要素にも適用される実装
 */
const Node: React.FC<NodeProps> = ({ node, onNodeClick, parentOpacity = 0 }) => {
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
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // 常にイベント伝播を停止
    console.log(`クリックされたノード: ${node.name}, タイプ: ${node.nodeType}`);
    // versionノードの場合のみ開閉処理を行う
    if (node.nodeType === 'version' && onNodeClick) {
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
        cursor: node.nodeType === 'version' && onNodeClick ? 'pointer' : 'default'
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
            <Node
              key={`${child.id || index}-${index}`}
              node={child}
              parentOpacity={currentOpacity} // 親の透明度を子に渡す
              onNodeClick={child.nodeType === 'version' ? onNodeClick : undefined} // versionノードのみクリックハンドラを渡す
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Node;
