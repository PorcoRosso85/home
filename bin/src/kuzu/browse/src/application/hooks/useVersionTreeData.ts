/**
 * バージョンツリーデータを取得・管理するためのカスタムフック
 */
import { useState, useEffect } from 'react';
import type { TreeNode, VersionState } from '../../domain/types';
import { buildVersionTree } from '../../domain/service/versionTreeBuilder';
import { useDatabaseConnection } from '../../infrastructure/database/useDatabaseConnection';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';

/**
 * バージョンとFOLLOWS関係を取得するためのクエリ
 */
interface VersionRelations {
  from: string;
  to: string;
}

/**
 * バージョンツリーデータを取得・管理するフック
 */
export function useVersionTreeData() {
  const [versionTree, setVersionTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { dbConnection, isConnected } = useDatabaseConnection();

  useEffect(() => {
    async function fetchVersionData() {
      // データベース接続がない場合は何もしない
      if (!dbConnection || !isConnected) {
        return;
      }

      try {
        // バージョンデータを取得
        const versionsResult = await executeDQLQuery(dbConnection, 'get_all_versions', {});

        if (!versionsResult.success || !versionsResult.data) {
          throw new Error(`バージョンデータの取得に失敗しました: ${versionsResult.error}`);
        }

        const versionsData = await versionsResult.data.getAllObjects();
        const versions: VersionState[] = versionsData.map((v: any) => ({
          id: v.version_id,
          timestamp: v.timestamp,
          description: v.description,
          change_reason: v.change_reason || ''
        }));

        // バージョン間のFOLLOWS関係を取得
        const followsResult = await executeDQLQuery(dbConnection, 'get_uris_up_to_version', {});

        if (!followsResult.success || !followsResult.data) {
          throw new Error(`FOLLOWS関係の取得に失敗しました: ${followsResult.error}`);
        }

        const followsData = await followsResult.data.getAllObjects();
        const follows: VersionRelations[] = followsData
          .filter((rel: any) => rel.from_version_id && rel.to_version_id)
          .map((rel: any) => ({
            from: rel.from_version_id,
            to: rel.to_version_id
          }));

        // バージョンツリーを構築
        const treeData = buildVersionTree(versions, follows);
        setVersionTree(treeData);
        setLoading(false);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラー';
        setError(`バージョンツリーの構築中にエラーが発生しました: ${errorMessage}`);
        setLoading(false);
        console.error('Error building version tree:', err);
      }
    }

    fetchVersionData();
  }, [dbConnection, isConnected]);

  return { versionTree, loading, error };
}
