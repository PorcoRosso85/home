import type { LocationUri } from '../domain/uriTypes';

/**
 * Browse向けLocationUriデータエクスポート
 */
export async function exportLocationUris(connection: any): Promise<LocationUri[]> {
  try {
    // LocationURIノードを全て取得
    const query = `
      MATCH (uri:LocationURI)
      RETURN uri.uri_id as uri_id,
             uri.scheme as scheme,
             uri.authority as authority,
             uri.path as path,
             uri.fragment as fragment,
             uri.query as query
    `;
    
    const result = await connection.query(query);
    const data = await result.getAllObjects();
    
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
  } catch (error) {
    console.error('Failed to export LocationUris:', error);
    throw error;
  }
}

/**
 * 特定のスキームのLocationUriをエクスポート
 */
export async function exportLocationUrisByScheme(connection: any, scheme: string): Promise<LocationUri[]> {
  try {
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
    
    const result = await connection.query(query, { scheme });
    const data = await result.getAllObjects();
    
    return data.map((row: any) => ({
      uri_id: row.uri_id || '',
      scheme: row.scheme || '',
      authority: row.authority || '',
      path: row.path || '',
      fragment: row.fragment || '',
      query: row.query || ''
    }));
  } catch (error) {
    console.error(`Failed to export LocationUris for scheme '${scheme}':`, error);
    throw error;
  }
}

/**
 * LocationURIと関連エンティティの関係をエクスポート
 */
export async function exportLocationUriRelations(connection: any): Promise<{
  locationUris: LocationUri[];
  relations: Array<{ fromUri: string; toEntity: string; relationType: string }>;
}> {
  try {
    // LocationURIと他のエンティティの関係を取得
    const relationsQuery = `
      MATCH (uri:LocationURI)-[r]->(e)
      RETURN uri.uri_id as fromUri,
             e as toEntity,
             type(r) as relationType
    `;
    
    const [urisResult, relationsResult] = await Promise.all([
      exportLocationUris(connection),
      connection.query(relationsQuery)
    ]);
    
    const relationsData = await relationsResult.getAllObjects();
    
    return {
      locationUris: urisResult,
      relations: relationsData.map((row: any) => ({
        fromUri: row.fromUri,
        toEntity: row.toEntity,
        relationType: row.relationType
      }))
    };
  } catch (error) {
    console.error('Failed to export LocationUri relations:', error);
    throw error;
  }
}
