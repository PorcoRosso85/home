import type { LocationUri } from '../domain/uriTypes';

/**
 * Browse向けLocationUriデータエクスポート
 */
export async function exportLocationUris(connection: any): Promise<LocationUri[] | {code: string; message: string}> {
  const query = `
    MATCH (uri:LocationURI)
    RETURN uri.uri_id as uri_id,
           uri.scheme as scheme,
           uri.authority as authority,
           uri.path as path,
           uri.fragment as fragment,
           uri.query as query
  `;
  
  const result = await connection.query(query).catch((error: any) => {
    console.error('Failed to export LocationUris:', error);
    return null;
  });
  
  if (!result) {
    return {code: "QUERY_ERROR", message: "Failed to execute LocationURI export query"};
  }
  
  const data = await result.getAllObjects().catch(() => []);
  
  // KuzuDBの結果をLocationUri型に変換
  const locationUris: LocationUri[] = data.map((row: any) => ({
    uri_id: row.uri_id || '',
    scheme: row.scheme || '',
    authority: row.authority || '',
    path: row.path || '',
    fragment: row.fragment || '',
    query: row.query || ''
  }));
  
  return locationUris;
}

/**
 * 特定のスキームのLocationUriをエクスポート
 */
export async function exportLocationUrisByScheme(connection: any, scheme: string): Promise<LocationUri[] | {code: string; message: string}> {
  const query = `
    MATCH (uri:LocationURI)
    WHERE uri.scheme = $scheme
    RETURN uri.uri_id as uri_id,
           uri.scheme as scheme,
           uri.authority as authority,
           uri.path as path,
           uri.fragment as fragment,
           uri.query as query
  `;
  
  const result = await connection.query(query, { scheme }).catch((error: any) => {
    console.error(`Failed to export LocationUris for scheme '${scheme}':`, error);
    return null;
  });
  
  if (!result) {
    return {code: "QUERY_ERROR", message: `Failed to execute LocationURI export query for scheme '${scheme}'`};
  }
  
  const data = await result.getAllObjects().catch(() => []);
  
  return data.map((row: any) => ({
    uri_id: row.uri_id || '',
    scheme: row.scheme || '',
    authority: row.authority || '',
    path: row.path || '',
    fragment: row.fragment || '',
    query: row.query || ''
  }));
}

/**
 * LocationURIと関連エンティティの関係をエクスポート
 */
export async function exportLocationUriRelations(connection: any): Promise<{
  locationUris: LocationUri[];
  relations: Array<{ fromUri: string; toEntity: string; relationType: string }>;
} | {code: string; message: string}> {
  // LocationURIと他のエンティティの関係を取得
  const relationsQuery = `
    MATCH (uri:LocationURI)-[r]->(e)
    RETURN uri.uri_id as fromUri,
           e as toEntity,
           type(r) as relationType
  `;
  
  const urisResult = await exportLocationUris(connection);
  if ('code' in urisResult) {
    return urisResult; // エラーを伝播
  }
  
  const relationsResult = await connection.query(relationsQuery).catch((error: any) => {
    console.error('Failed to export LocationUri relations:', error);
    return null;
  });
  
  if (!relationsResult) {
    return {code: "RELATIONS_QUERY_ERROR", message: "Failed to execute relations query"};
  }
  
  const relationsData = await relationsResult.getAllObjects().catch(() => []);
  
  return {
    locationUris: urisResult,
    relations: relationsData.map((row: any) => ({
      fromUri: row.fromUri,
      toEntity: row.toEntity,
      relationType: row.relationType
    }))
  };
}
