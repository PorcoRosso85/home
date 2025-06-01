import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import type { 
  NodeData,
  LocationUrisInput,
  LocationUrisOutput,
  LocationUrisError
} from '../../domain/types';
import type { Result } from '../../common/types';
import { createError, createSuccess, classifyError } from '../../common/errorHandler';
import { isErrorResult } from '../../common/typeGuards';
import * as logger from '../../../common/infrastructure/logger';
import { createVersionCompletionService } from '../services/VersionCompletionService';
import { createVersionProgressRepository } from '../../infrastructure/repository/VersionProgressRepository';

/**
 * LocationURI取得とツリー構築のCore関数（Pure Logic）
 */
export const fetchLocationUrisCore = async (input: LocationUrisInput): Promise<Result<NodeData[]>> => {
  if (!input.dbConnection) {
    return createError('DATABASE_ERROR', 'データベース接続が確立されていません');
  }

  if (!input.selectedVersionId) {
    return createSuccess([]);
  }

  // Core層：LocationURIデータの取得（try/catch除去）
  const locationUris = await fetchLocationUrisData(input.dbConnection, input.selectedVersionId);
  
  // Core層：完了状態の取得
  const locationUrisWithCompletion = await attachCompletionStatus(
    locationUris, 
    input.dbConnection, 
    input.selectedVersionId
  );
  
  // Core層：ツリー構造への変換
  const treeNodes = buildTreeFromLocationUris(locationUrisWithCompletion, input.selectedVersionId);
  
  return createSuccess(treeNodes);
};

// LocationURIデータの取得
async function fetchLocationUrisData(dbConnection: any, selectedVersionId: string) {
  const result = await executeDQLQuery(dbConnection, 'list_uris_cumulative', { 
    version_id: selectedVersionId 
  });
  
  const queryResult = await result.data.getAllObjects();
  
  return queryResult.map(row => ({
    uri_id: row.uri_id || row.id,
    scheme: row.scheme || '',
    authority: row.authority || '',
    path: row.path || '',
    fragment: row.fragment || '',
    query: row.query || '',
    from_version: row.from_version,
    version_description: row.version_description
  }));
}

// 完了状態の取得
async function attachCompletionStatus(locationUris: any[], dbConnection: any, selectedVersionId: string) {
  try {
    const repository = createVersionProgressRepository();
    const versionService = createVersionCompletionService(repository);
    
    const incompleteUrisResult = await getIncompleteUrisSafely(
      versionService, 
      dbConnection, 
      selectedVersionId
    );
    
    if (incompleteUrisResult.status === "success") {
      const incompleteUriIds = new Set(incompleteUrisResult.data.map(uri => uri.uri_id));
      
      return locationUris.map(uri => ({
        ...uri,
        isCompleted: !incompleteUriIds.has(uri.uri_id)
      }));
    } else {
      logger.debug('完了状態の取得に失敗:', incompleteUrisResult.message);
      return locationUris;
    }
  } catch (error) {
    logger.debug('完了状態取得でエラー:', error);
    return locationUris;
  }
}

async function getIncompleteUrisSafely(versionService: any, dbConnection: any, selectedVersionId: string) {
  const incompleteUris = await versionService.getIncompleteLocationUris(dbConnection, selectedVersionId);
  
  if (!incompleteUris) {
    return { status: "error", message: "未完了URIの取得に失敗しました" };
  }
  
  return { status: "success", data: incompleteUris };
}

// ツリー構造の構築
function buildTreeFromLocationUris(locationUris: any[], selectedVersionId?: string): NodeData[] {
  const tree: NodeData[] = [];
  
  const schemeGroups = locationUris.reduce((acc, uri) => {
    const scheme = uri.scheme || parseSchemeFromUriId(uri.uri_id);
    if (!acc[scheme]) acc[scheme] = [];
    acc[scheme].push(uri);
    return acc;
  }, {});

  Object.entries(schemeGroups).forEach(([scheme, uris]: [string, any[]]) => {
    const rootNode: NodeData = {
      id: `${scheme}://`,
      name: `${scheme}://`,
      nodeType: 'location',
      children: []
    };
    
    if (scheme === 'file') {
      buildFileHierarchy(rootNode, uris, selectedVersionId);
    } else {
      uris.forEach(uri => {
        const leafNode: NodeData = {
          id: uri.uri_id,
          name: `${uri.path}${uri.fragment ? '#' + uri.fragment : ''}${uri.query ? '?' + uri.query : ''}`,
          nodeType: 'location',
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

function parseSchemeFromUriId(uriId: string): string {
  const schemeMatch = uriId.match(/^([^:]+):/);
  return schemeMatch ? schemeMatch[1] : 'unknown';
}

// ファイル階層構築
function buildFileHierarchy(rootNode: NodeData, uris: any[], selectedVersionId?: string) {
  const pathMap = new Map<string, NodeData>();
  pathMap.set('/', rootNode);
  
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
    
    for (let i = 0; i < pathParts.length; i++) {
      currentPath += '/' + pathParts[i];
      
      let currentNode = pathMap.get(currentPath);
      
      if (!currentNode) {
        currentNode = {
          id: currentPath,
          name: pathParts[i],
          nodeType: 'location',
          children: [],
          from_version: uri.from_version,
          isCurrentVersion: uri.from_version === selectedVersionId
        };
        parentNode.children.push(currentNode);
        pathMap.set(currentPath, currentNode);
      }
      
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
