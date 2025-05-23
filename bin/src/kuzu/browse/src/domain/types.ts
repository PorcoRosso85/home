/**
 * KuzuDB Parquet Viewer の基本型定義
 * 規約準拠: type定義優先
 */

export type DatabaseResult = {
  success: boolean;
  data?: any;
  error?: string;
};

export type StatusMessage = {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
};

export type VersionState = {
  id: string;
  timestamp: string;
  description: string;
  change_reason: string;
};

export type LocationURI = {
  uri_id: string;
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
  from_version?: string;
  version_description?: string;
  isCompleted?: boolean;
};

export type TreeNode = {
  id: string;
  name: string;
  nodeType?: 'version' | 'location';
  children: TreeNode[];
  from_version?: string;
  isCurrentVersion?: boolean;
  isCompleted?: boolean;
  isExpanded?: boolean;
  isLoading?: boolean;
  description?: string;
  change_reason?: string;
  timestamp?: string;
};
