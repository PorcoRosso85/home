import type { LocationUri } from '../../../query/domain/uriTypes';
import type { TreeNodeData } from '../interface/components/TreeNode';

/**
 * LocationUriからセグメント抽出
 */
export function parseLocationUri(locationUri: LocationUri): {
  segments: string[];
  name: string;
  type: 'entity' | 'value';
} {
  // スキーム別の解析
  const segments: string[] = [];
  
  if (locationUri.scheme === 'file') {
    // file://→ ファイルパス解析
    const pathParts = locationUri.path.split('/').filter(p => p);
    segments.push('files', ...pathParts);
    
    // ファイル名を抽出
    const fileName = pathParts[pathParts.length - 1] || locationUri.path;
    return {
      segments,
      name: fileName,
      type: 'value'
    };
  } else if (locationUri.scheme === 'path') {
    // パス形式→既存のダミーデータ形式
    segments.push(...locationUri.path.split('/').filter(p => p));
    
    // セグメントから名前と型を推測
    const lastSegment = segments[segments.length - 1];
    const isRelation = segments.some(s => 
      ['knows', 'lives_in', 'works_at', 'friend_of', 'owns', 'located_in'].includes(s)
    );
    
    return {
      segments,
      name: lastSegment,
      type: isRelation ? 'value' : 'entity'
    };
  } else {
    // その他のスキーム→汎用解析
    segments.push(locationUri.scheme);
    if (locationUri.authority) segments.push(locationUri.authority);
    segments.push(...locationUri.path.split('/').filter(p => p));
    if (locationUri.query) segments.push('?', locationUri.query);
    if (locationUri.fragment) segments.push('#', locationUri.fragment);
    
    return {
      segments,
      name: segments[segments.length - 1] || locationUri.uri_id,
      type: 'entity'
    };
  }
}

/**
 * 階層関係を推測
 */
export function inferTreeStructure(locationUris: LocationUri[]): TreeNodeData[] {
  const treeMap: Record<string, TreeNodeData> = {};
  const rootNodes: TreeNodeData[] = [];
  
  locationUris.forEach((locationUri, index) => {
    const { segments, name, type } = parseLocationUri(locationUri);
    
    let currentPath = '';
    let parentNode: TreeNodeData | null = null;
    
    segments.forEach((segment, i) => {
      const isLeaf = i === segments.length - 1;
      const segmentPath = currentPath + '/' + segment;
      currentPath = segmentPath;
      
      if (!treeMap[segmentPath]) {
        // 新しいノードを作成
        const newNode: TreeNodeData = {
          id: `node-${index}-${i}`,
          type: isLeaf ? type : 'entity',
          name: segment,
          uri: segmentPath,
          properties: {
            path: segmentPath,
            isLeaf,
            locationUri: isLeaf ? locationUri : undefined
          },
          children: []
        };
        
        treeMap[segmentPath] = newNode;
        
        if (parentNode) {
          parentNode.children?.push(newNode);
        } else if (i === 0) {
          rootNodes.push(newNode);
        }
      }
      
      parentNode = treeMap[segmentPath];
    });
  });
  
  return rootNodes;
}

/**
 * スキーム別にLocationUriをグループ化
 */
export function groupByScheme(locationUris: LocationUri[]): Record<string, LocationUri[]> {
  return locationUris.reduce((groups, uri) => {
    if (!groups[uri.scheme]) {
      groups[uri.scheme] = [];
    }
    groups[uri.scheme].push(uri);
    return groups;
  }, {} as Record<string, LocationUri[]>);
}

/**
 * 任意のLocationUri配列から階層構築
 */
export function buildDynamicTree(locationUris: LocationUri[]): TreeNodeData[] {
  // 空配列対策
  if (!locationUris || locationUris.length === 0) {
    return [];
  }
  
  // スキーム別にグループ化
  const schemeGroups = groupByScheme(locationUris);
  const rootNodes: TreeNodeData[] = [];
  
  // 各スキームグループを処理
  Object.entries(schemeGroups).forEach(([scheme, uris]) => {
    const schemeNode: TreeNodeData = {
      id: `scheme-${scheme}`,
      type: 'entity',
      name: scheme,
      uri: `/${scheme}`,
      properties: {
        path: `/${scheme}`,
        isLeaf: false,
        scheme
      },
      children: inferTreeStructure(uris)
    };
    
    rootNodes.push(schemeNode);
  });
  
  return rootNodes;
}
