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
    try {
      setIsLoading(true);
      setError(null);
      logger.debug('データ取得を開始します...');
      const data = await buildLocationTree();
      logger.info(`データ取得成功: ${data.length}件`);
      setTreeData(data);
    } catch (err) {
      logger.error('データ取得エラー:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load data';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      logger.debug('データ取得処理完了');
    }
  }, []);

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
