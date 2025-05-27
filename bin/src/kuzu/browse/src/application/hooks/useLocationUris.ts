import { useState, useEffect } from 'react';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import { NodeData } from '../../domain/types';
import * as logger from '../../../../common/infrastructure/logger';
import { createVersionCompletionService } from '../services/VersionCompletionService';
import { createVersionProgressRepository } from '../../infrastructure/repository/VersionProgressRepository';

export const useLocationUris = (dbConnection: any | null, selectedVersionId: string) => {
  const [treeData, setTreeData] = useState<NodeData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 選択されたバージョンのツリーデータを取得
  useEffect(() => {
    const fetchTreeData = async () => {
      if (!dbConnection || !selectedVersionId) return;
      
      setLoading(true);
      
      try {
        // 指定バージョン以前の各URIの最新状態を取得
        const result = await executeDQLQuery(dbConnection, 'list_uris_cumulative', { 
          version_id: selectedVersionId 
        });
        
        const queryResult = await result.data.getAllObjects();
        
        // LocationURIデータをツリー構造に変換
        const locationUris = queryResult.map(row => ({
          uri_id: row.uri_id || row.id,
          scheme: row.scheme || '',
          authority: row.authority || '',
          path: row.path || '',
          fragment: row.fragment || '',
          query: row.query || '',
          from_version: row.from_version,
          version_description: row.version_description
        }));
        
        // 完了状態を取得
        const repository = createVersionProgressRepository();
        const versionService = createVersionCompletionService(repository);
        
        // 完了状態を取得（規約準拠版）
        const incompleteUrisResult = await getIncompleteUrisSafely(
          versionService, 
          dbConnection, 
          selectedVersionId
        );
        
        let locationUrisWithCompletion;
        if (incompleteUrisResult.status === "success") {
          const incompleteUriIds = new Set(incompleteUrisResult.data.map(uri => uri.uri_id));
          
          // LocationURIに完了状態を追加
          locationUrisWithCompletion = locationUris.map(uri => ({
            ...uri,
            isCompleted: !incompleteUriIds.has(uri.uri_id)
          }));
        } else {
          logger.debug('完了状態の取得に失敗:', incompleteUrisResult.message);
          // エラーが発生した場合は完了状態なしでツリーを構築
          locationUrisWithCompletion = locationUris;
        }
        
        // 階層構造変換（パスベース）
        const treeNodes: NodeData[] = buildTreeFromLocationUris(locationUrisWithCompletion, selectedVersionId);
        setTreeData(treeNodes);
        
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラー';
        setError(`ツリーデータ取得でエラーが発生しました: ${errorMessage}`);
        logger.error('ツリーデータ取得エラー:', err);
      }
      
      setLoading(false);
    };

    fetchTreeData();
  }, [dbConnection, selectedVersionId]);

  return {
    treeData,
    loading,
    error
  };
};

/**
 * 未完了URIを安全に取得する内部関数
 * 規約準拠: try-catch禁止、共用体型エラーハンドリング
 */
async function getIncompleteUrisSafely(
  versionService: any,
  dbConnection: any,
  selectedVersionId: string
): Promise<{ status: "success"; data: any[] } | { status: "error"; message: string }> {
  const incompleteUris = await versionService.getIncompleteLocationUris(dbConnection, selectedVersionId);
  
  if (!incompleteUris) {
    return {
      status: "error",
      message: "未完了URIの取得に失敗しました"
    };
  }
  
  return { status: "success", data: incompleteUris };
}

// LocationURIからツリー構造を構築する簡易実装
function buildTreeFromLocationUris(locationUris: any[], selectedVersionId?: string): NodeData[] {
  const tree: NodeData[] = [];
  
  // スキーム別にグループ化
  const schemeGroups = locationUris.reduce((acc, uri) => {
    const scheme = uri.scheme || parseSchemeFromUriId(uri.uri_id);
    if (!acc[scheme]) {
      acc[scheme] = [];
    }
    acc[scheme].push(uri);
    return acc;
  }, {});

  // 各スキームのルートノードを作成
  Object.entries(schemeGroups).forEach(([scheme, uris]: [string, any[]]) => {
    const rootNode: NodeData = {
      id: `${scheme}://`,
      name: `${scheme}://`,
      nodeType: 'location',  // nodeTypeを追加
      children: []
    };
    
    // ファイルシステムの場合は階層構造を構築
    if (scheme === 'file') {
      buildFileHierarchy(rootNode, uris, selectedVersionId);
    } else {
      // その他のスキームは単純にリスト表示
      uris.forEach(uri => {
        const leafNode: NodeData = {
          id: uri.uri_id,
          name: `${uri.path}${uri.fragment ? '#' + uri.fragment : ''}${uri.query ? '?' + uri.query : ''}`,
          nodeType: 'location',  // nodeTypeを追加
          children: [],
          from_version: uri.from_version,
          isCurrentVersion: uri.from_version === selectedVersionId,
          isCompleted: uri.isCompleted
        };
        rootNode.children.push(leafNode);
      });
    }
    
    tree.push(rootNode);
  });

  return tree;
}

// URI IDからスキームを解析
function parseSchemeFromUriId(uriId: string): string {
  const schemeMatch = uriId.match(/^([^:]+):/);
  return schemeMatch ? schemeMatch[1] : 'unknown';
}

// ファイル階層を構築する関数
function buildFileHierarchy(rootNode: NodeData, uris: any[], selectedVersionId?: string) {
  const pathMap = new Map<string, NodeData>();
  
  // ルートノードをマップに追加
  pathMap.set('/', rootNode);
  
  // パスをソートして親から順に処理
  const sortedUris = uris.sort((a, b) => {
    const pathA = a.path || parsePathFromUriId(a.uri_id);
    const pathB = b.path || parsePathFromUriId(b.uri_id);
    return pathA.localeCompare(pathB);
  });
  
  sortedUris.forEach(uri => {
    const path = uri.path || parsePathFromUriId(uri.uri_id);
    const pathParts = path.split('/').filter(part => part !== '');
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
          nodeType: 'location',  // nodeTypeを追加
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
        currentNode.isCompleted = uri.isCompleted;
      }
      
      parentNode = currentNode;
    }
  });
}

// URI IDからパスを解析
function parsePathFromUriId(uriId: string): string {
  try {
    if (uriId.includes('://')) {
      const url = new URL(uriId);
      return url.pathname;
    } else if (uriId.startsWith('file:')) {
      return uriId.replace('file:', '');
    }
    return uriId;
  } catch {
    return uriId;
  }
}
