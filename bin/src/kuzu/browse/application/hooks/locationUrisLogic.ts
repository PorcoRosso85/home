import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import type { NodeData } from '../../domain/coreTypes';
import type { 
  LocationUrisInput,
  LocationUrisResult
} from '../types/locationUriTypes';
import { createError, createLocationUrisSuccess } from '../../common/errorHandler';
import { isErrorResult } from '../../common/typeGuards';
import * as logger from '../../../common/infrastructure/logger';

/**
 * LocationURI取得とツリー構築のCore関数（Pure Logic）
 * Duck APIからロードされたシンプルなデータ構造に対応
 */
export const fetchLocationUrisCore = async (input: LocationUrisInput): Promise<LocationUrisResult> => {
  if (!input.dbConnection) {
    return createError('DATABASE_ERROR', 'データベース接続が確立されていません');
  }

  if (!input.selectedVersionId) {
    return createLocationUrisSuccess([]);
  }

  // LocationURIデータの取得
  const locationUrisResult = await fetchLocationUrisDataSafely(input.dbConnection, input.selectedVersionId);
  
  if (isErrorResult(locationUrisResult)) {
    return locationUrisResult;
  }
  
  // ツリー構造への変換
  const treeNodes = buildTreeFromLocationUris(locationUrisResult.data, input.selectedVersionId);
  
  return createLocationUrisSuccess(treeNodes);
};

// LocationURIデータの取得（安全版）
async function fetchLocationUrisDataSafely(dbConnection: any, selectedVersionId: string) {
  const result = await executeDQLQuery(dbConnection, 'list_uris_cumulative', { 
    version_id: selectedVersionId 
  });
  
  if (isErrorResult(result)) {
    return result;
  }
  
  const queryResult = await result.data.getAllObjects();
  
  // idからURI情報を解析
  const locationUris = queryResult.map(row => {
    const uriId = row.id || row.uri_id;
    const parsedUri = parseUriFromId(uriId);
    
    return {
      uri_id: uriId,
      scheme: parsedUri.scheme,
      authority: parsedUri.authority,
      path: parsedUri.path,
      fragment: parsedUri.fragment,
      query: parsedUri.query,
      from_version: row.from_version || selectedVersionId,
      isCompleted: true // DuckLakeでは常に完了扱い
    };
  });
  
  return createLocationUrisSuccess(locationUris);
}

// URI IDからURI構成要素を解析
function parseUriFromId(uriId: string): {
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
} {
  try {
    // URL標準を使ってパース（file:// などの標準的なURIをサポート）
    const url = new URL(uriId);
    
    return {
      scheme: url.protocol.replace(':', ''), // "file:" -> "file"
      authority: url.hostname || '',
      path: url.pathname || '/',
      fragment: url.hash.replace('#', '') || '',
      query: url.search.replace('?', '') || ''
    };
  } catch (e) {
    // URL標準でパースできない場合は手動で解析
    logger.debug(`Manual parsing for non-standard URI: ${uriId}`);
    
    const schemeMatch = uriId.match(/^([^:]+):/);
    const scheme = schemeMatch ? schemeMatch[1] : 'unknown';
    
    // スキーム以降の部分を取得
    const afterScheme = uriId.substring(scheme.length + 1);
    
    // authorityとpathを分離（//で始まる場合はauthorityあり）
    let authority = '';
    let pathAndRest = afterScheme;
    
    if (afterScheme.startsWith('//')) {
      const authorityEnd = afterScheme.indexOf('/', 2);
      if (authorityEnd > -1) {
        authority = afterScheme.substring(2, authorityEnd);
        pathAndRest = afterScheme.substring(authorityEnd);
      } else {
        authority = afterScheme.substring(2);
        pathAndRest = '';
      }
    }
    
    // fragment と query を分離
    let path = pathAndRest;
    let fragment = '';
    let query = '';
    
    const fragmentIndex = path.indexOf('#');
    if (fragmentIndex > -1) {
      fragment = path.substring(fragmentIndex + 1);
      path = path.substring(0, fragmentIndex);
    }
    
    const queryIndex = path.indexOf('?');
    if (queryIndex > -1) {
      query = path.substring(queryIndex + 1);
      path = path.substring(0, queryIndex);
    }
    
    return { scheme, authority, path, fragment, query };
  }
}

// ツリー構造の構築
function buildTreeFromLocationUris(locationUris: any[], selectedVersionId?: string): NodeData[] {
  const tree: NodeData[] = [];
  
  const schemeGroups = locationUris.reduce((acc, uri) => {
    const scheme = uri.scheme;
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

// ファイル階層構築
function buildFileHierarchy(rootNode: NodeData, uris: any[], selectedVersionId?: string) {
  const pathMap = new Map<string, NodeData>();
  pathMap.set('/', rootNode);
  
  const sortedUris = uris.sort((a, b) => {
    const pathA = a.path;
    const pathB = b.path;
    return pathA.localeCompare(pathB);
  });
  
  sortedUris.forEach(uri => {
    const path = uri.path;
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
