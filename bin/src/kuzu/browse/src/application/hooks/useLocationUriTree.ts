/**
 * 特定のバージョンに関連するLocationURIツリーを取得するためのカスタムフック
 */
import { useState, useEffect } from 'react';
import type { TreeNode, LocationURI } from '../../domain/types';
import { useDatabaseConnection } from '../../infrastructure/database/useDatabaseConnection';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';

/**
 * URLのパスをセグメントに分割する
 */
function splitPath(path: string): string[] {
  return path.split('/').filter(Boolean);
}

/**
 * LocationURIツリーを構築する補助関数
 */
function buildLocationUriTree(locationUris: LocationURI[]): TreeNode[] {
  // スキームごとにLocationURIをグループ化
  const schemeGroups: Record<string, LocationURI[]> = {};
  
  locationUris.forEach(uri => {
    const scheme = uri.scheme || 'unknown';
    if (!schemeGroups[scheme]) {
      schemeGroups[scheme] = [];
    }
    schemeGroups[scheme].push(uri);
  });
  
  // スキームツリーの構築
  const tree: TreeNode[] = [];
  
  Object.entries(schemeGroups).forEach(([scheme, uris]) => {
    // スキームノード
    const schemeNode: TreeNode = {
      id: `scheme-${scheme}`,
      name: `${scheme}://`,
      nodeType: 'location',
      children: []
    };
    
    // ディレクトリ構造を構築
    const directoryTree: Record<string, TreeNode> = {};
    
    uris.forEach(uri => {
      const pathSegments = splitPath(uri.path);
      
      if (pathSegments.length === 0) {
        // パスがない場合は直接スキームノードに追加
        const leafNode: TreeNode = {
          id: uri.uri_id,
          name: '[空のパス]',
          nodeType: 'location',
          children: [],
          from_version: uri.from_version,
          isCompleted: uri.isCompleted
        };
        schemeNode.children.push(leafNode);
        return;
      }
      
      if (pathSegments.length === 1) {
        // ルートレベルのファイル
        const leafNode: TreeNode = {
          id: uri.uri_id,
          name: pathSegments[0],
          nodeType: 'location',
          children: [],
          from_version: uri.from_version,
          isCompleted: uri.isCompleted
        };
        schemeNode.children.push(leafNode);
        return;
      }
      
      // 複数セグメントあるパスの処理
      let currentPath = '';
      let parentNode = schemeNode;
      
      // パスの最後のセグメント（ファイル名）を除く部分でディレクトリツリーを構築
      for (let i = 0; i < pathSegments.length - 1; i++) {
        const segment = pathSegments[i];
        currentPath = currentPath ? `${currentPath}/${segment}` : segment;
        
        // このパスのディレクトリノードがまだない場合は作成
        if (!directoryTree[currentPath]) {
          const dirNode: TreeNode = {
            id: `dir-${scheme}-${currentPath}`,
            name: segment,
            nodeType: 'location',
            children: []
          };
          directoryTree[currentPath] = dirNode;
          
          // 親ディレクトリがある場合はその子として追加
          if (i > 0) {
            const parentPath = splitPath(currentPath).slice(0, -1).join('/');
            if (directoryTree[parentPath]) {
              directoryTree[parentPath].children.push(dirNode);
            }
          } else {
            // トップレベルのディレクトリはスキームノードの子として追加
            schemeNode.children.push(dirNode);
          }
        }
      }
      
      // ファイルノードの作成と追加
      const fileName = pathSegments[pathSegments.length - 1];
      const parentPath = splitPath(uri.path).slice(0, -1).join('/');
      const fileNode: TreeNode = {
        id: uri.uri_id,
        name: fileName,
        nodeType: 'location',
        children: [],
        from_version: uri.from_version,
        isCompleted: uri.isCompleted
      };
      
      if (directoryTree[parentPath]) {
        directoryTree[parentPath].children.push(fileNode);
      } else {
        // 親ディレクトリがない場合（通常はエラー状態）
        schemeNode.children.push(fileNode);
      }
    });
    
    tree.push(schemeNode);
  });
  
  return tree;
}

/**
 * 特定のバージョンに関連するLocationURIツリーを取得するカスタムフック
 */
export function useLocationUriTree(versionId: string) {
  const [locationTree, setLocationTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { dbConnection, isConnected } = useDatabaseConnection();
  
  useEffect(() => {
    async function fetchLocationUriData() {
      if (!versionId || !dbConnection || !isConnected) {
        setLocationTree([]);
        setLoading(false);
        return;
      }
      
      // 指定バージョンに関連するLocationURIを取得（規約準拠版）
      const uriResult = await executeDQLQuery(dbConnection, 'locationuris_by_version', {
        version_id: versionId
      });
      
      if (!uriResult.success || !uriResult.data) {
        setError(`LocationURIデータの取得に失敗しました: ${uriResult.error}`);
        setLoading(false);
        return;
      }
      
      const uriDataResult = await getUriDataSafely(uriResult.data);
      if (uriDataResult.status === "error") {
        setError(uriDataResult.message);
        setLoading(false);
        return;
      }
      
      const locationUris: LocationURI[] = uriDataResult.data.map((u: any) => ({
        uri_id: u.uri_id,
        scheme: u.scheme,
        authority: u.authority || '',
        path: u.path || '',
        fragment: u.fragment || '',
        query: u.query || '',
        from_version: versionId,
        isCompleted: !!u.is_completed
      }));
      
      const treeData = buildLocationUriTree(locationUris);
      setLocationTree(treeData);
      setLoading(false);
      setError(null);
    }
    
    fetchLocationUriData();
  }, [versionId, dbConnection, isConnected]);
  
  return { locationTree, loading, error };
}
