/**
 * データ取得・状態管理のカスタムフック
 */
import { useState, useEffect, useCallback } from 'react';
import type { TreeNodeData } from '../../domain/entity/locationUri';
import { buildLocationTree } from '../usecase/buildLocationTree';
import { onDatabaseReady } from '../../infrastructure/database/databaseEvent';
import * as logger from '../../../../common/infrastructure/logger';

type TreeDataState = {
  treeData: TreeNodeData[];
  selectedNode: TreeNodeData | null;
  isLoading: boolean;
  error: string | null;
  handleNodeClick: (node: TreeNodeData) => void;
}

export function useTreeData(): TreeDataState {
  const [treeData, setTreeData] = useState<TreeNodeData[]>([]);
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleNodeClick = useCallback((node: TreeNodeData) => {
    setSelectedNode(node);
    logger.debug(`Selected node: ${node.id}`);
  }, []);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    logger.debug('データ取得を開始します...');
    
    // データ取得を安全に実行（規約準拠版）
    const result = await buildLocationTreeSafely();
    
    if (result.status === "success") {
      logger.info(`データ取得成功: ${result.data.length}件`);
      setTreeData(result.data);
    } else {
      logger.error('データ取得エラー:', result.message);
      setError(result.message);
    }
    
    setIsLoading(false);
    logger.debug('データ取得処理完了');
  }, []);

/**
 * LocationTreeを安全に構築する内部関数
 * 規約準拠: try-catch禁止、共用体型エラーハンドリング
 */
async function buildLocationTreeSafely(): Promise<
  { status: "success"; data: TreeNodeData[] } | 
  { status: "error"; message: string }
> {
  const data = await buildLocationTree();
  
  if (!data || !Array.isArray(data)) {
    return {
      status: "error",
      message: "データの構築に失敗しました"
    };
  }
  
  return { status: "success", data };
}

  useEffect(() => {
    // database-readyイベントを待ち、データを取得
    const cleanup = onDatabaseReady(fetchData);
    return cleanup;
  }, [fetchData]);

  return {
    treeData,
    selectedNode,
    isLoading,
    error,
    handleNodeClick,
  };
}
