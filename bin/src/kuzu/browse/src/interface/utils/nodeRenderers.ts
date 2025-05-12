/**
 * スタイル生成を行うユーティリティ関数
 */

import { CSSProperties } from 'react';
import { TreeNode } from '../../domain/types';

/**
 * ノードのタイプに基づいたスタイルを生成する
 */
export function getNodeStyle(node: TreeNode, parentOpacity = 0): CSSProperties {
  const nodeType = node.nodeType || 'location';
  const hasChildren = node.children && node.children.length > 0;
  
  // 基本スタイル
  const baseStyle: CSSProperties = {
    position: 'relative',
    padding: '8px',
    margin: '4px 0',
    borderRadius: '4px',
    cursor: 'pointer',
  };
  
  if (nodeType === 'version') {
    // バージョンノード用スタイル
    return {
      ...baseStyle,
      background: node.isCurrentVersion ? 'rgba(0, 102, 204, 0.1)' : 'rgba(0, 0, 0, 0.05)',
      borderLeft: node.isCurrentVersion ? '3px solid #0066cc' : undefined,
    };
  } else {
    // LocationURIノード用スタイル
    // 現在の要素の透明度：親からの透明度 + 自分の透明度
    const currentOpacity = parentOpacity + 0.02;
    
    // 実際の背景色を計算
    const backgroundOpacity = Math.min(currentOpacity, 0.3); // 最大30%まで
    let backgroundColor = `rgba(0, 0, 0, ${backgroundOpacity})`;
    
    // 未完了の場合、薄赤色の背景色にする
    if (!hasChildren && node.isCompleted === false) {
      backgroundColor = `rgba(255, 200, 200, 0.3)`;
    }
    
    return {
      ...baseStyle,
      background: backgroundColor,
    };
  }
}

/**
 * ノードタイプに基づいたテキスト色を取得する
 */
export function getTextColors(node: TreeNode, backgroundOpacity = 0): {
  primary: string;
  secondary: string;
  tertiary: string;
} {
  const nodeType = node.nodeType || 'location';
  const hasChildren = node.children && node.children.length > 0;
  
  if (nodeType === 'version') {
    // バージョンノードのテキスト色
    return {
      primary: node.isCurrentVersion ? '#0066cc' : '#000000',
      secondary: '#666666',
      tertiary: '#888888',
    };
  } else {
    // LocationURIノードのテキスト色
    const isHighOpacity = backgroundOpacity > 0.15;
    const isIncomplete = !hasChildren && node.isCompleted === false;
    
    return {
      primary: (isHighOpacity || isIncomplete) ? 'white' : 'black',
      secondary: (isHighOpacity || isIncomplete) ? '#ccc' : '#666',
      tertiary: (isHighOpacity || isIncomplete) ? '#aaa' : '#888',
    };
  }
}
