import type { LocationUri, TreeNodeData } from '../entity/locationUri';

export function parseLocationUri(locationUri: LocationUri): {
  segments: string[];
  name: string;
  type: 'entity' | 'value';
} {
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
