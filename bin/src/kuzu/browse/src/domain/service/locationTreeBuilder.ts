import type { LocationUri, TreeNodeData } from '../entity/locationUri';
import { parseLocationUri } from './locationUriParser';
import { groupByScheme } from './locationUriGrouper';

export function buildTreeStructure(locationUris: LocationUri[]): TreeNodeData[] {
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

export function buildTree(locationUris: LocationUri[]): TreeNodeData[] {
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
      children: buildTreeStructure(uris)
    };
    
    rootNodes.push(schemeNode);
  });
  
  return rootNodes;
}
