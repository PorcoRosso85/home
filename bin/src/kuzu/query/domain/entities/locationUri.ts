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

/**
 * URI派生関数 - 必要時にidから各部分を取得
 */
export const UriUtils = {
  /**
   * スキーム取得: 'file', 'requirement', 'test'等
   */
  getScheme(id: string): string {
    return id.split(':')[0] || '';
  },

  /**
   * パス取得: '/src/auth/login.js'等
   */
  getPath(id: string): string {
    try {
      return new URL(id).pathname;
    } catch {
      return id.startsWith('/') ? id : '';
    }
  },

  /**
   * フラグメント取得: 'L10-L25', 'REQ-001-2'等  
   */
  getFragment(id: string): string {
    const parts = id.split('#');
    return parts.length > 1 ? parts[1] : '';
  },

  /**
   * オーソリティ取得: 'github.com', 'local'等
   */
  getAuthority(id: string): string {
    try {
      return new URL(id).hostname;
    } catch {
      return '';
    }
  },

  /**
   * クエリ取得: URLパラメータ部分
   */
  getQuery(id: string): string {
    try {
      return new URL(id).search.replace('?', '');
    } catch {
      return '';
    }
  }
};

/**
 * LocationURIエンティティをクエリパラメータに変換する
 */
export function toQueryParams(locationUri: LocationUriEntity): Record<string, string | boolean> {
  return {
    id: locationUri.id,
    completed: locationUri.completed,
  };
}

/**
 * バリデーション関数（Cypher側に委譲）
 * NOTE: 実際のバリデーションは /dql/validation/validate_location_uri.cypher で実行
 */
export function validateLocationUri(id: string): { isValid: boolean; error?: string } {
  // 基本的なnullチェックのみ、詳細はCypher側で処理
  if (!id || typeof id !== 'string') {
    return {
      isValid: false,
      error: 'ID must be a non-empty string'
    };
  }

  return { isValid: true }; // Cypher側でのバリデーションに委譲
}
