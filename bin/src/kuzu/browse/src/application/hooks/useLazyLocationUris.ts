/**
 * 最小構成でLocationURIの遅延ロードを管理するフック
 */

import { useState, useCallback, useRef } from 'react';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import { LocationURI, TreeNode } from '../../domain/types';
import * as logger from '../../../../common/infrastructure/logger';

export function useLazyLocationUris(dbConnection: any) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locationUris, setLocationUris] = useState<LocationURI[]>([]);
  const [locationTreeNodes, setLocationTreeNodes] = useState<TreeNode[]>([]);
  
  // キャッシュ
  const cacheRef = useRef<Record<string, LocationURI[]>>({});
  
  // スキーム別にグループ化
  const groupByScheme = useCallback((uris: LocationURI[]): Record<string, LocationURI[]> => {
    return uris.reduce((acc, uri) => {
      if (!acc[uri.scheme]) {
        acc[uri.scheme] = [];
      }
      acc[uri.scheme].push(uri);
      return acc;
    }, {} as Record<string, LocationURI[]>);
  }, []);
  
  // LocationURIをツリー構造に変換
  const buildLocationTree = useCallback((uris: LocationURI[], versionId: string): TreeNode[] => {
    // スキーム別にグループ化
    const schemeGroups = groupByScheme(uris);
    const rootNodes: TreeNode[] = [];
    
    // 各スキームグループをツリーノードに変換
    Object.entries(schemeGroups).forEach(([scheme, schemeUris]) => {
      const schemeNode: TreeNode = {
        id: `scheme-${scheme}`,
        name: `${scheme}://`,
        nodeType: 'location',
        children: [],
        isExpanded: true
      };
      
      // ファイルシステムパスの階層を構築
      if (scheme === 'file') {
        const pathMap = new Map<string, TreeNode>();
        pathMap.set('/', schemeNode);
        
        // パスをソート
        const sortedUris = [...schemeUris].sort((a, b) => a.path.localeCompare(b.path));
        
        sortedUris.forEach(uri => {
          const pathParts = uri.path.split('/').filter(part => part !== '');
          let currentPath = '';
          let parentNode = schemeNode;
          
          // パスの各部分を処理
          for (let i = 0; i < pathParts.length; i++) {
            const part = pathParts[i];
            currentPath += '/' + part;
            
            if (!pathMap.has(currentPath)) {
              // 新しいノードを作成
              const isLeaf = i === pathParts.length - 1;
              const newNode: TreeNode = {
                id: isLeaf ? uri.uri_id : `path-${currentPath}`,
                name: part,
                nodeType: 'location',
                children: [],
                isExpanded: true,
                from_version: isLeaf ? uri.from_version : undefined,
                isCurrentVersion: isLeaf ? uri.from_version === versionId : undefined,
                isCompleted: isLeaf ? uri.isCompleted : undefined
              };
              
              parentNode.children.push(newNode);
              pathMap.set(currentPath, newNode);
            }
            
            parentNode = pathMap.get(currentPath) as TreeNode;
          }
        });
      } else {
        // 他のスキームは単純にリスト
        schemeUris.forEach(uri => {
          const uriNode: TreeNode = {
            id: uri.uri_id,
            name: `${uri.path}${uri.fragment ? '#' + uri.fragment : ''}${uri.query ? '?' + uri.query : ''}`,
            nodeType: 'location',
            children: [],
            from_version: uri.from_version,
            isCurrentVersion: uri.from_version === versionId,
            isCompleted: uri.isCompleted
          };
          
          schemeNode.children.push(uriNode);
        });
      }
      
      rootNodes.push(schemeNode);
    });
    
    return rootNodes;
  }, [groupByScheme]);
  
  // LocationURIをロード
  const loadLocationUris = useCallback(async (versionId: string): Promise<LocationURI[]> => {
    // キャッシュをチェック
    if (cacheRef.current[versionId]) {
      const cachedUris = cacheRef.current[versionId];
      setLocationUris(cachedUris);
      setLocationTreeNodes(buildLocationTree(cachedUris, versionId));
      return cachedUris;
    }
    
    if (!dbConnection) {
      setError('データベース接続がありません');
      return [];
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // 指定バージョン以前の各URIの最新状態を取得
      const result = await executeDQLQuery(dbConnection, 'get_uris_up_to_version', { 
        version_id: versionId 
      });
      
      if (!result.success || !result.data) {
        throw new Error(result.error || 'クエリ実行に失敗しました');
      }
      
      const queryResult = await result.data.getAllObjects();
      
      // LocationURIデータを整形
      const uris: LocationURI[] = queryResult.map(row => ({
        uri_id: row.uri_id,
        scheme: row.scheme,
        authority: row.authority || '',
        path: row.path,
        fragment: row.fragment || '',
        query: row.query || '',
        from_version: row.from_version,
        version_description: row.version_description,
        isCompleted: row.is_completed !== false
      }));
      
      // キャッシュと状態を更新
      cacheRef.current[versionId] = uris;
      setLocationUris(uris);
      setLocationTreeNodes(buildLocationTree(uris, versionId));
      
      return uris;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '不明なエラーが発生しました';
      logger.error(`LocationURI取得エラー: ${errorMsg}`);
      setError(errorMsg);
      return [];
    } finally {
      setLoading(false);
    }
  }, [dbConnection, buildLocationTree]);
  
  return {
    loading,
    error,
    locationUris,
    loadLocationUris,
    locationTreeNodes
  };
}
