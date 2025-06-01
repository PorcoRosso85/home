import type { TreeInput, TreeOutput } from '../../domain/types';

/**
 * ツリー表示ロジックのCore関数（Pure Logic）
 * React依存なし、テスト可能な純粋関数
 */
export const computeTreeStateCore = (input: TreeInput): TreeOutput => {
  // Core層：データ存在チェック
  const hasData = input.treeData && input.treeData.length > 0;
  
  // Core層：空メッセージの決定
  const emptyMessage = "No data available";
  
  // Core層：レンダリング可能なノードリストの準備
  const renderableNodes = hasData ? input.treeData : [];
  
  return {
    hasData,
    emptyMessage,
    renderableNodes
  };
};

/**
 * ツリー項目キー生成のCore関数
 */
export const generateTreeNodeKeyCore = (nodeId: string | undefined, index: number): string => {
  return `root-${nodeId || index}`;
};
