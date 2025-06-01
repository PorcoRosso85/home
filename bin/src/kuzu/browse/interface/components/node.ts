import type { NodeInput, NodeOutput, NodeStyleOutput } from '../../domain/types';
import * as logger from '../../../common/infrastructure/logger';

export const computeNodeStateCore = (input: NodeInput): NodeOutput => {
  const hasChildren = input.node.children && input.node.children.length > 0;
  const styles = computeNodeStylesCore(input);
  
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (input.onNodeClick) {
      logger.info('Node clicked', {
        nodeId: input.node.id,
        nodeType: input.node.nodeType,
        eventType: 'left'
      });
      input.onNodeClick({
        node: input.node,
        eventType: 'left',
        event: e.nativeEvent
      });
    }
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (input.onNodeClick) {
      logger.info('Node right-clicked', {
        nodeId: input.node.id,
        nodeType: input.node.nodeType,
        eventType: 'right'
      });
      input.onNodeClick({
        node: input.node,
        eventType: 'right',
        event: e.nativeEvent
      });
    }
  };

  return { hasChildren, styles, handleClick, handleContextMenu };
};

export const computeNodeStylesCore = (input: NodeInput): NodeStyleOutput => {
  const parentOpacity = input.parentOpacity || 0;
  const hasChildren = input.node.children && input.node.children.length > 0;
  
  const currentOpacity = parentOpacity + 0.02;
  const backgroundOpacity = Math.min(currentOpacity, 0.3);
  
  // Core層：背景色計算
  let backgroundColor = `rgba(0, 0, 0, ${backgroundOpacity})`;
  
  if (!hasChildren && input.node.isCompleted === false) {
    backgroundColor = `rgba(255, 200, 200, 0.3)`;
  }
  
  if (input.node.nodeType === 'version') {
    backgroundColor = `rgba(230, 240, 255, ${backgroundOpacity + 0.2})`;
  }
  
  // Core層：テキスト色計算
  const shouldUseLightText = backgroundOpacity > 0.15 || (!hasChildren && input.node.isCompleted === false);
  const textColor = shouldUseLightText ? 'white' : 'black';
  const secondaryTextColor = shouldUseLightText ? '#ccc' : '#666';
  const tertiaryTextColor = shouldUseLightText ? '#aaa' : '#888';
  const nodeTextColor = input.node.isCurrentVersion ? '#0066cc' : textColor;
  
  return {
    backgroundColor,
    textColor,
    secondaryTextColor,
    tertiaryTextColor,
    nodeTextColor,
    currentOpacity
  };
};

export const generateNodeKeyCore = (nodeId: string | undefined, index: number): string => {
  return `${nodeId || index}-${index}`;
};
