/**
 * LocationURIエンティティ（browse版）
 * 
 * 位置情報と完了状態を管理
 */

export interface LocationURI {
  uri_id: string;
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
  completed: boolean;
}

/**
 * LocationURIの表示用フォーマット
 */
export function formatLocationUri(locationUri: LocationURI): string {
  let uri = `${locationUri.scheme}:`;
  
  if (locationUri.authority) {
    uri += `//${locationUri.authority}`;
  }
  
  uri += locationUri.path;
  
  if (locationUri.query) {
    uri += `?${locationUri.query}`;
  }
  
  if (locationUri.fragment) {
    uri += `#${locationUri.fragment}`;
  }
  
  return uri;
}

/**
 * LocationURIのバリデーション
 */
export function validateLocationUri(locationUri: LocationURI): { isValid: boolean; error?: string } {
  if (!locationUri.uri_id || locationUri.uri_id.trim() === '') {
    return { isValid: false, error: 'URI ID is required' };
  }
  
  if (!locationUri.scheme || locationUri.scheme.trim() === '') {
    return { isValid: false, error: 'Scheme is required' };
  }
  
  if (!locationUri.path) {
    return { isValid: false, error: 'Path is required' };
  }
  
  if (typeof locationUri.completed !== 'boolean') {
    return { isValid: false, error: 'Completed must be a boolean' };
  }
  
  return { isValid: true };
}

/**
 * LocationURIリストの統計情報
 */
export function calculateLocationUriStatistics(locationUris: LocationURI[]): {
  total: number;
  completed: number;
  incomplete: number;
  completionPercentage: number;
} {
  const total = locationUris.length;
  const completed = locationUris.filter(uri => uri.completed).length;
  const incomplete = total - completed;
  const completionPercentage = total > 0 ? completed / total : 0;
  
  return {
    total,
    completed,
    incomplete,
    completionPercentage,
  };
}

/**
 * LocationURIのグループ化
 */
export function groupLocationUrisByScheme(locationUris: LocationURI[]): Record<string, LocationURI[]> {
  return locationUris.reduce((groups, uri) => {
    const scheme = uri.scheme || 'unknown';
    if (!groups[scheme]) {
      groups[scheme] = [];
    }
    groups[scheme].push(uri);
    return groups;
  }, {} as Record<string, LocationURI[]>);
}

/**
 * LocationURIのフィルタリング
 */
export function filterLocationUris(
  locationUris: LocationURI[], 
  filters: {
    completed?: boolean;
    scheme?: string;
    pathPattern?: string;
  }
): LocationURI[] {
  return locationUris.filter(uri => {
    if (filters.completed !== undefined && uri.completed !== filters.completed) {
      return false;
    }
    
    if (filters.scheme && uri.scheme !== filters.scheme) {
      return false;
    }
    
    if (filters.pathPattern && !uri.path.includes(filters.pathPattern)) {
      return false;
    }
    
    return true;
  });
}

/**
 * LocationURIの一括更新準備
 */
export function prepareBatchUpdate(
  locationUris: LocationURI[], 
  completed: boolean
): Array<{ uriId: string; completed: boolean }> {
  return locationUris.map(uri => ({
    uriId: uri.uri_id,
    completed,
  }));
}

/**
 * LocationURIの並び順調整
 */
export function sortLocationUris(
  locationUris: LocationURI[], 
  sortBy: 'path' | 'scheme' | 'completed' | 'uri_id' = 'path',
  order: 'asc' | 'desc' = 'asc'
): LocationURI[] {
  return [...locationUris].sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'path':
        comparison = a.path.localeCompare(b.path);
        break;
      case 'scheme':
        comparison = a.scheme.localeCompare(b.scheme);
        break;
      case 'completed':
        comparison = Number(a.completed) - Number(b.completed);
        break;
      case 'uri_id':
        comparison = a.uri_id.localeCompare(b.uri_id);
        break;
    }
    
    return order === 'asc' ? comparison : -comparison;
  });
}
