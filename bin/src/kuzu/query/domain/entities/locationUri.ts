/**
 * LocationURIエンティティ - 究極の最小化版
 * 
 * REFACTORED: 冗長なプロパティを削除（7プロパティ → 1プロパティ）
 * scheme, authority, path, fragment, query, completed は id から派生可能
 */

/**
 * LocationURIの最小構造
 */
export type LocationUriEntity = {
  id: string;              // 完全なURI情報（例: 'file:///src/auth.js#L10-L25'）
};

/**
 * LocationURIエンティティを作成する
 */
export function createLocationUri(
  id: string
): LocationUriEntity {
  return { id };
}

// UriUtils削除: 解析ロジックはCypher側に移行

/**
 * LocationURIエンティティをクエリパラメータに変換する
 */
export function toQueryParams(locationUri: LocationUriEntity): Record<string, string> {
  return {
    id: locationUri.id
  };
}

// バリデーション削除: Cypher側に完全移行
