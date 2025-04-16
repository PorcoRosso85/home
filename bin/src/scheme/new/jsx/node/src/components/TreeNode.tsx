import React from 'react';
import { FrontendNodeType, HighlightDataType } from '../types';
import LeftBox from './LeftBox';
import RightBox from './RightBox';
import ChildrenContainer from './ChildrenContainer';

// 深さに基づいて動的に色を計算する関数
export function calculateDynamicColor(level: number, maxLevel: number): string {
  const factor = Math.min(level / maxLevel, 1);
  const colorValue = Math.round(255 - (factor * 127));
  return `rgb(${colorValue}, ${colorValue}, ${colorValue})`;
}

interface TreeNodeProps {
  node: FrontendNodeType;
  level?: number;
  maxDepth: number;
  highlightData?: HighlightDataType;
  onNodeClick?: (node: FrontendNodeType) => void;
}

// ツリーノードコンポーネント
const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level = 0,
  maxDepth,
  highlightData,
  onNodeClick
}) => {
  const hasChildren = node.children && node.children.length > 0;
  
  // 関数ノードかどうかの判定（:::を含むパスは関数）
  const isFunction = node.path.includes(':::');
  
  // パスは元のファイルパスを使用
  const currentPath = node.path;
  
  // 関数名を取得（関数ノードの場合）
  let displayName = node.name;
  if (isFunction) {
    // パスから関数名を取得
    const functionName = node.path.split(':::')[1];
    if (functionName) {
      displayName = functionName;
    }
  }
  
  // 深さに基づいて背景色を動的に計算
  const backgroundColor = calculateDynamicColor(level, maxDepth);
  
  // このノードに対するハイライトを取得
  const nodeHighlight = highlightData && highlightData[currentPath];
  
  return (
    <div 
      style={{
        backgroundColor,
        borderRadius: '4px',
        margin: '5px 0 0 0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        cursor: 'pointer'
      }}
      onClick={(e) => {
        e.stopPropagation();
        onNodeClick && onNodeClick(node);
      }}
    >
      <div style={{
        display: 'flex',
        justifyContent: 'flex-start',
        position: 'relative',
        width: '100%'
      }}>
        <LeftBox 
          path={currentPath} 
          name={displayName} 
          backgroundColor={backgroundColor} 
        />
        <RightBox 
          isFunction={isFunction} 
          highlightIndex={nodeHighlight} 
          backgroundColor={backgroundColor}
          highlightData={highlightData}
        />
      </div>
      
      {hasChildren && (
        <ChildrenContainer>
          {node.children.map((child, index) => (
            <TreeNode
              key={index}
              node={child}
              level={level + 1}
              maxDepth={maxDepth}
              highlightData={highlightData}
              onNodeClick={onNodeClick}
            />
          ))}
        </ChildrenContainer>
      )}
    </div>
  );
};

export default TreeNode;
