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
  const backgroundColor = `rgba(0, 0, 0, ${backgroundOpacity})`;
  
  // 背景の暗さに応じて文字色を調整
  const textColor = backgroundOpacity > 0.15 ? 'white' : 'black';
  const secondaryTextColor = backgroundOpacity > 0.15 ? '#ccc' : '#666';
  const tertiaryTextColor = backgroundOpacity > 0.15 ? '#aaa' : '#888';
  
  // バージョン情報による色分け
  const nodeTextColor = node.isCurrentVersion ? '#0066cc' : textColor;
  
  // 完了状態のアイコンとスタイル
  const getCompletionIcon = () => {
    if (hasChildren) {
      // 親ノードの場合、進捗率を表示
      const completionRate = node.totalCount > 0 
        ? Math.round((node.completedCount! / node.totalCount!) * 100) 
        : 0;
      return `${completionRate}%`;
    } else {
      // リーフノードの場合、チェックマークまたは未チェック
      return node.isCompleted ? '✓' : '○';
    }
  };
  
  const getCompletionColor = () => {
    if (hasChildren) {
      const completionRate = node.totalCount > 0 
        ? node.completedCount! / node.totalCount! 
        : 0;
      if (completionRate === 1) return '#28a745'; // 完了時は緑
      if (completionRate > 0) return '#ffc107'; // 進行中は黄色
      return '#6c757d'; // 未開始はグレー
    } else {
      return node.isCompleted ? '#28a745' : '#6c757d';
    }
  };

  return (
    <div style={{
      position: 'relative',
      padding: '8px',
      margin: '4px 0',
      borderRadius: '4px',
      // 計算された背景色を適用
      background: backgroundColor,
    }}>
      {/* コンテンツ */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span 
              style={{ 
                color: getCompletionColor(), 
                fontWeight: 'bold',
                marginRight: '8px',
                minWidth: '24px',
                display: 'inline-block',
                textAlign: 'center'
              }}
            >
              {getCompletionIcon()}
            </span>
            <strong style={{ color: nodeTextColor }}>{node.name}</strong> 
            {node.from_version && (
              <span style={{ fontSize: '0.8em', color: secondaryTextColor, marginLeft: '8px' }}>
                ({node.from_version})
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
              key={`${child.id}-${index}`}
              node={child}
              parentOpacity={currentOpacity} // 親の透明度を子に渡す
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TreeNode;
