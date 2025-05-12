/**
 * 再帰的にツリーノードとその子要素を表示するコンポーネント
 * 親要素の重なりが子要素にも適用される実装
 */

import React, { useCallback } from 'react';
import type { TreeNode as TreeNodeData } from '../../domain/types';
import { getNodeStyle, getTextColors } from '../utils/nodeRenderers';
import { formatVersionForDisplay } from '../../domain/service/versionParser';

interface TreeNodeProps {
  node: TreeNodeData;
  onNodeClick?: (nodeId: string) => void;
  onNodeToggle?: (nodeId: string) => void;
  onNodeSelect?: (nodeId: string) => void;
  parentOpacity?: number; // 親からの透明度を受け取る
}

/**
 * ツリーノードコンポーネント
 */
const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  onNodeClick,
  onNodeToggle,
  onNodeSelect,
  parentOpacity = 0
}) => {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = node.isExpanded !== false; // デフォルトは展開状態
  const isLoading = node.isLoading === true;
  const nodeType = node.nodeType || 'location'; // デフォルトはlocation
  
  // 背景透明度の計算（LocationURIノードのみ）
  const currentOpacity = nodeType === 'location' ? parentOpacity + 0.02 : 0;
  const backgroundOpacity = Math.min(currentOpacity, 0.3); // 最大30%まで
  
  // 実際の背景色を計算
  const backgroundColor = nodeType === 'version' 
    ? (node.isCurrentVersion ? 'rgba(0, 102, 204, 0.1)' : 'rgba(0, 0, 0, 0.05)')
    : (!hasChildren && node.isCompleted === false 
        ? 'rgba(255, 200, 200, 0.3)' 
        : `rgba(0, 0, 0, ${backgroundOpacity})`);
  
  // テキスト色を取得
  const textColors = getTextColors(node, backgroundOpacity);
  
  // ノードクリックハンドラ
  const handleNodeClick = useCallback((event: React.MouseEvent) => {
    if (onNodeClick) {
      onNodeClick(node.id);
    }
    
    if (onNodeToggle) {
      onNodeToggle(node.id);
    }
    
    if (onNodeSelect) {
      onNodeSelect(node.id);
    }
    
    event.stopPropagation();
  }, [node.id, onNodeClick, onNodeToggle, onNodeSelect]);
  
  return (
    <div>
      <div
        style={{
          position: 'relative',
          padding: '8px',
          margin: '4px 0',
          borderRadius: '4px',
          background: backgroundColor,
          borderLeft: nodeType === 'version' && node.isCurrentVersion ? '3px solid #0066cc' : undefined,
          cursor: 'pointer',
        }}
        onClick={handleNodeClick}
      >
        {/* コンテンツ */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <strong style={{ color: nodeType === 'version' && node.isCurrentVersion ? '#0066cc' : textColors.primary }}>
                {nodeType === 'version' 
                  ? formatVersionForDisplay(node.name) 
                  : node.name}
              </strong>
              
              {nodeType === 'version' && node.description && (
                <span style={{ fontSize: '0.8em', color: textColors.secondary, marginLeft: '8px' }}>
                  ({node.description})
                </span>
              )}
              
              {nodeType === 'location' && node.from_version && (
                <span style={{ fontSize: '0.8em', color: textColors.secondary, marginLeft: '8px' }}>
                  ({formatVersionForDisplay(node.from_version)})
                </span>
              )}
            </div>
            
            <div style={{ fontSize: '0.8em', color: textColors.tertiary }}>
              {nodeType === 'version' ? node.change_reason : node.id}
            </div>
          </div>
          
          {isLoading && (
            <span style={{ 
              fontSize: '12px', 
              color: '#999', 
              fontStyle: 'italic',
              marginLeft: '8px'
            }}>
              ロード中...
            </span>
          )}
        </div>
      </div>
      
      {/* 子要素 - ノードが展開されている場合のみレンダリング */}
      {hasChildren && isExpanded && (
        <div style={{ paddingLeft: '20px', marginTop: '4px' }}>
          {node.children.map((child, index) => (
            <TreeNode
              key={`${child.id}-${index}`}
              node={child}
              onNodeClick={onNodeClick}
              onNodeToggle={onNodeToggle}
              onNodeSelect={onNodeSelect}
              parentOpacity={currentOpacity} // 親の透明度を子に渡す
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TreeNode;
