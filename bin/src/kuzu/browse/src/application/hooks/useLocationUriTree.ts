/**
 * 特定のバージョンに関連するLocationURIツリーを取得するためのカスタムフック
 */
import { useState, useEffect } from 'react';
import type { TreeNode, LocationURI } from '../../domain/types';
import { useDatabaseConnection } from '../../infrastructure/database/useDatabaseConnection';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';

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
    
    // パスの階層ごとにグループ化して子ノードを作成
    const pathGroups: Record<string, LocationURI[]> = {};
    
    uris.forEach(uri => {
      const pathParts = uri.path.split('/').filter(Boolean);
      if (pathParts.length > 1) {
        // ディレクトリパスがある場合
        const dirPath = pathParts.slice(0, -1).join('/');
        if (!pathGroups[dirPath]) {
          pathGroups[dirPath] = [];
        }
        pathGroups[dirPath].push(uri);
      } else {
        // ルートレベルのファイル
        const leafNode: TreeNode = {
          id: uri.uri_id,
          name: uri.path || '[空のパス]',
          nodeType: 'location',
          children: [],
          from_version: uri.from_version,
          isCompleted: uri.isCompleted
        };
        schemeNode.children.push(leafNode);
      }
    });
    
    // ディレクトリノードを追加
    Object.entries(pathGroups).forEach(([dirPath, dirUris]) => {
      const dirNode: TreeNode = {
        id: `dir-${scheme}-${dirPath}`,
        name: dirPath,
        nodeType: 'location',
        children: []
      };
      
      // ディレクトリ内のファイルを追加
      dirUris.forEach(uri => {
        const fileName = uri.path.split('/').pop() || '[不明]';
        const fileNode: TreeNode = {
          id: uri.uri_id,
          name: fileName,
          nodeType: 'location',
          children: [],
          from_version: uri.from_version,
          isCompleted: uri.isCompleted
        };
        dirNode.children.push(fileNode);
      });
      
      schemeNode.children.push(dirNode);
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
      
      try {
        // 指定バージョンに関連するLocationURIを取得
        const uriResult = await executeDQLQuery(dbConnection, 'locationuris_by_version', {
          version_id: versionId
        });
        
        if (!uriResult.success || !uriResult.data) {
          throw new Error(`LocationURIデータの取得に失敗しました: ${uriResult.error}`);
        }
        
        const uriData = await uriResult.data.getAllObjects();
        const locationUris: LocationURI[] = uriData.map((u: any) => ({
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
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラー';
        setError(`LocationURIツリーの構築中にエラーが発生しました: ${errorMessage}`);
        setLoading(false);
        console.error('Error building location URI tree:', err);
      }
    }
    
    fetchLocationUriData();
  }, [versionId, dbConnection, isConnected]);
  
  return { locationTree, loading, error };
}
