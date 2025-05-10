/**
 * KuzuDB Parquet Viewer の基本型定義
 */

/**
 * データベース操作結果
 */
export interface DatabaseResult {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * ステータスメッセージ
 */
export interface StatusMessage {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
}

/**
 * VersionState型定義
 */
export interface VersionState {
  id: string;           // バージョンID (例: 'v1.0.0')
  timestamp: string;    // タイムスタンプ (ISO 8601形式)
  description: string;  // バージョンの説明
}

/**
 * LocationURI型定義
 */
export interface LocationURI {
  uri_id: string;      // URI識別子
  scheme: string;      // スキーム (file, http, etc.)
  authority: string;   // 権限 (ホスト名など)
  path: string;        // パス
  fragment: string;    // フラグメント
  query: string;       // クエリ文字列
}

/**
 * バージョンとLocationURIの関係データ
 */
export interface VersionedLocationData {
  version_id: string;
  location_uris: LocationURI[];
  previous_version_id?: string;
}

/**
 * LOCATED_WITH関係のエンティティ情報
 */
export interface LocatedWithEntity {
  type: 'code' | 'requirement' | 'reference';
  id: string;
  entity_type: string;
}

/**
 * LocationURI階層情報
 */
export interface LocationHierarchy {
  parent_uri: string;
  child_uri: string;
  relation_type: 'file_hierarchy' | 'requirement_hierarchy';
}
