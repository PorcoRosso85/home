/**
 * LocationURIエンティティ
 * 
 * KuzuDBのLocationURIノードを表現する型定義と関連関数
 */

/**
 * LocationURIの基本構造
 */
export type LocationUriEntity = {
  uri_id: string;      // URI識別子（主キー）
  scheme: string;      // URIスキーム（例: http, file）
  authority: string;   // URIオーソリティ部分
  path: string;        // URIパス部分
  fragment: string;    // URIフラグメント部分
  query: string;       // URIクエリ部分
  completed: boolean;  // 完了フラグ
};

/**
 * LocationURIエンティティを作成する
 */
export function createLocationUri(
  uriId: string,
  scheme: string,
  path: string,
  authority?: string,
  fragment?: string,
  query?: string,
  completed: boolean = false
): LocationUriEntity {
  return {
    uri_id: uriId,
    scheme,
    authority: authority || '',
    path,
    fragment: fragment || '',
    query: query || '',
    completed
  };
}

/**
 * LocationURIエンティティの複製を作成する
 */
export function cloneLocationUri(locationUri: LocationUriEntity): LocationUriEntity {
  return {
    uri_id: locationUri.uri_id,
    scheme: locationUri.scheme,
    authority: locationUri.authority,
    path: locationUri.path,
    fragment: locationUri.fragment,
    query: locationUri.query,
    completed: locationUri.completed,
  };
}

/**
 * LocationURIエンティティの部分更新
 */
export function updateLocationUri(
  locationUri: LocationUriEntity,
  updates: Partial<Omit<LocationUriEntity, 'uri_id'>>
): LocationUriEntity {
  return {
    ...locationUri,
    ...updates,
  };
}

/**
 * LocationURIエンティティを文字列URIに変換する
 */
export function toUriString(locationUri: LocationUriEntity): string {
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
 * 文字列URIからLocationURIエンティティを生成する
 */
export function fromUriString(uri: string): LocationUriEntity {
  try {
    const urlObject = new URL(uri);
    
    return createLocationUri(
      uri,
      urlObject.protocol.replace(':', ''),
      urlObject.pathname,
      urlObject.hostname + (urlObject.port ? ':' + urlObject.port : ''),
      urlObject.hash.replace('#', ''),
      urlObject.search.replace('?', '')
    );
  } catch (error) {
    // URLコンストラクタエラーの場合、単純なパス形式として処理
    if (uri.startsWith('/')) {
      return createLocationUri(uri, 'path', uri);
    }
    
    throw new Error(`Invalid URI format: ${uri}`);
  }
}

/**
 * LocationURIエンティティの等価性チェック
 */
export function equalsLocationUri(uri1: LocationUriEntity, uri2: LocationUriEntity): boolean {
  return (
    uri1.uri_id === uri2.uri_id &&
    uri1.scheme === uri2.scheme &&
    uri1.authority === uri2.authority &&
    uri1.path === uri2.path &&
    uri1.fragment === uri2.fragment &&
    uri1.query === uri2.query &&
    uri1.completed === uri2.completed
  );
}

/**
 * LocationURIエンティティをクエリパラメータに変換する
 */
export function toQueryParams(locationUri: LocationUriEntity): Record<string, string | boolean> {
  return {
    uri_id: locationUri.uri_id,
    scheme: locationUri.scheme,
    authority: locationUri.authority,
    path: locationUri.path,
    fragment: locationUri.fragment,
    query: locationUri.query,
    completed: locationUri.completed,
  };
}
