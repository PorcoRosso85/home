import { useState, useEffect } from 'react';
import { executeQuery } from '../../infrastructure/repository/queryExecutor';
import { VersionState, TreeNode } from '../../domain/types';
import * as logger from '../../../../common/infrastructure/logger';

export const useVersionData = (dbConnection: any | null) => {
  const [versions, setVersions] = useState<VersionState[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 全バージョンを取得
  useEffect(() => {
    const fetchVersions = async () => {
      if (!dbConnection) {
        logger.debug('dbConnectionがnullのため、バージョン取得をスキップ');
        return;
      }

      try {
        setLoading(true);
        logger.debug('バージョン一覧の取得を開始');
        const result = await executeQuery(dbConnection, 'get_all_versions', {});
        logger.debug('クエリ実行結果:', result);
        
        if (result.success && result.data) {
          const queryResult = await result.data.getAllObjects();
          logger.debug('getAllObjects結果:', queryResult);
          
          const versionList: VersionState[] = queryResult.map(row => ({
            id: row.version_id,
            timestamp: row.timestamp,
            description: row.description
          }));
          
          logger.debug('変換後のバージョンリスト:', versionList);
          setVersions(versionList);
          
          // 最新バージョンを自動選択
          if (versionList.length > 0) {
            const defaultVersion = versionList[versionList.length - 1].id;
            logger.debug('デフォルトバージョンを設定:', defaultVersion);
            setSelectedVersionId(defaultVersion);
          } else {
            logger.debug('バージョンが見つかりません');
          }
        } else {
          logger.error('クエリ実行失敗:', result.error);
          setError(`バージョン取得失敗: ${result.error || '不明なエラー'}`);
        }
      } catch (err) {
        logger.error('バージョン一覧取得エラー:', err);
        setError('バージョンの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchVersions();
  }, [dbConnection]);

  // 選択されたバージョンのツリーデータを取得
  useEffect(() => {
    const fetchTreeData = async () => {
      if (!dbConnection || !selectedVersionId) return;

      try {
        setLoading(true);
        const result = await executeQuery(dbConnection, 'locationuris_by_version', { 
          version_id: selectedVersionId 
        });
        
        if (result.success && result.data) {
          const queryResult = await result.data.getAllObjects();
          
          // LocationURIデータをツリー構造に変換
          const locationUris = queryResult.map(row => ({
            uri_id: row.uri_id,
            scheme: row.scheme,
            authority: row.authority || '',
            path: row.path,
            fragment: row.fragment || '',
            query: row.query || ''
          }));
          
          // 簡易的な階層構造変換（パスベース）
          const treeNodes: TreeNode[] = buildTreeFromLocationUris(locationUris);
          setTreeData(treeNodes);
        }
      } catch (err) {
        logger.error('ツリーデータ取得エラー:', err);
        setError('ツリーデータの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchTreeData();
  }, [dbConnection, selectedVersionId]);

  return {
    versions,
    selectedVersionId,
    setSelectedVersionId,
    treeData,
    loading,
    error
  };
};

// LocationURIからツリー構造を構築する簡易実装
function buildTreeFromLocationUris(locationUris: any[]): TreeNode[] {
  const tree: TreeNode[] = [];
  const nodeMap = new Map<string, TreeNode>();

  // スキーム別にグループ化
  const schemeGroups = locationUris.reduce((acc, uri) => {
    if (!acc[uri.scheme]) {
      acc[uri.scheme] = [];
    }
    acc[uri.scheme].push(uri);
    return acc;
  }, {});

  // 各スキームのルートノードを作成
  Object.entries(schemeGroups).forEach(([scheme, uris]: [string, any[]]) => {
    const rootNode: TreeNode = {
      id: `${scheme}://`,
      name: `${scheme}://`,
      children: []
    };
    
    // 各URIをツリーに追加
    uris.forEach(uri => {
      const leafNode: TreeNode = {
        id: uri.uri_id,
        name: `${uri.path}${uri.fragment ? '#' + uri.fragment : ''}${uri.query ? '?' + uri.query : ''}`,
        children: []
      };
      rootNode.children.push(leafNode);
    });
    
    tree.push(rootNode);
  });

  return tree;
}
