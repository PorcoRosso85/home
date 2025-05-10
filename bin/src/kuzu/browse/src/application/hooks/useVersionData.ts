import { useState, useEffect } from 'react';
import { executeQuery } from '../../infrastructure/repository/queryExecutor';
import { VersionState, TreeNode } from '../../domain/types';
import * as logger from '../../../../common/infrastructure/logger';

export const useVersionData = (dbConnection: any | null, showLatestOnly: boolean = false) => {
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
        
        let result;
        if (showLatestOnly) {
          // 全期間での最新バージョンのみ表示
          result = await executeQuery(dbConnection, 'get_latest_locationuris', {});
        } else {
          // 指定バージョン以前の各URIの最新状態を取得
          result = await executeQuery(dbConnection, 'get_uris_up_to_version', { 
            version_id: selectedVersionId 
          });
        }
        
        if (result.success && result.data) {
          const queryResult = await result.data.getAllObjects();
          
          // LocationURIデータをツリー構造に変換
          const locationUris = queryResult.map(row => ({
            uri_id: row.uri_id,
            scheme: row.scheme,
            authority: row.authority || '',
            path: row.path,
            fragment: row.fragment || '',
            query: row.query || '',
            from_version: row.from_version || row.latest_version_id,
            version_description: row.version_description
          }));
          
          // 簡易的な階層構造変換（パスベース）
          const treeNodes: TreeNode[] = buildTreeFromLocationUris(locationUris, selectedVersionId);
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
  }, [dbConnection, selectedVersionId, showLatestOnly]);

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
function buildTreeFromLocationUris(locationUris: any[], selectedVersionId?: string): TreeNode[] {
  const tree: TreeNode[] = [];
  
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
    
    // ファイルシステムの場合は階層構造を構築
    if (scheme === 'file') {
      buildFileHierarchy(rootNode, uris, selectedVersionId);
    } else {
      // その他のスキームは単純にリスト表示
      uris.forEach(uri => {
        const leafNode: TreeNode = {
          id: uri.uri_id,
          name: `${uri.path}${uri.fragment ? '#' + uri.fragment : ''}${uri.query ? '?' + uri.query : ''}`,
          children: [],
          from_version: uri.from_version,
          isCurrentVersion: uri.from_version === selectedVersionId
        };
        rootNode.children.push(leafNode);
      });
    }
    
    tree.push(rootNode);
  });

  return tree;
}

// ファイル階層を構築する関数
function buildFileHierarchy(rootNode: TreeNode, uris: any[], selectedVersionId?: string) {
  const pathMap = new Map<string, TreeNode>();
  
  // ルートノードをマップに追加
  pathMap.set('/', rootNode);
  
  // パスをソートして親から順に処理
  const sortedUris = uris.sort((a, b) => a.path.localeCompare(b.path));
  
  sortedUris.forEach(uri => {
    const pathParts = uri.path.split('/').filter(part => part !== '');
    let currentPath = '';
    let parentNode = rootNode;
    
    // パスの各部分を処理
    for (let i = 0; i < pathParts.length; i++) {
      currentPath += '/' + pathParts[i];
      
      // 既存のノードを探す
      let currentNode = pathMap.get(currentPath);
      
      if (!currentNode) {
        // 新規ノードを作成
        currentNode = {
          id: currentPath,
          name: pathParts[i],
          children: [],
          from_version: uri.from_version,
          isCurrentVersion: uri.from_version === selectedVersionId
        };
        parentNode.children.push(currentNode);
        pathMap.set(currentPath, currentNode);
      }
      
      // 最後の部分（ファイル名）の場合は、フラグメントやクエリを追加
      if (i === pathParts.length - 1) {
        currentNode.name += uri.fragment ? '#' + uri.fragment : '';
        currentNode.name += uri.query ? '?' + uri.query : '';
        currentNode.id = uri.uri_id;
      }
      
      parentNode = currentNode;
    }
  });
}
