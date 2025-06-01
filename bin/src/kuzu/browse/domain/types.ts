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

export type NodeData = {
  id: string;
  name: string;
  nodeType?: 'version' | 'location';
  children: NodeData[];
  from_version?: string;
  isCurrentVersion?: boolean;
  isCompleted?: boolean;
  isExpanded?: boolean;
  isLoading?: boolean;
  description?: string;
  change_reason?: string;
  timestamp?: string;
};

export type NodeClickEvent = {
  node: NodeData;
  eventType: 'left' | 'right';
  event: MouseEvent;
  // Claude解析用のコンテキストデータ
  contextData?: {
    queryResult?: any;
    renderingData?: any;
  };
};

// Claude解析関連の型定義
export type ClaudeAnalysisRequest = {
  versionId: string;
  prompt: string;
  nodeData: NodeData;
};

export type ClaudeAnalysisResult = 
  | { status: "success"; data: string }
  | { status: "error"; message: string };

// =============================================================================
// Core Functions Input/Output Types (Phase 1追加)
// =============================================================================

// VersionStates Core Types
export type VersionStatesInput = {
  dbConnection: any;
};

export type VersionStatesError = {
  type: 'DATABASE_ERROR' | 'QUERY_ERROR' | 'TRANSFORM_ERROR' | 'UNKNOWN_ERROR';
  message: string;
  originalError?: unknown;
};

export type VersionStatesOutput = 
  | { success: true; data: VersionState[] }
  | { success: false; error: VersionStatesError };

// React Hook State Types
export type VersionStatesState = {
  versions: VersionState[];
  loading: boolean;
  error: string | null;
};

// LocationUris Core Types (Phase 2追加)
export type LocationUrisInput = {
  dbConnection: any;
  selectedVersionId: string;
};

export type LocationUrisError = {
  type: 'DATABASE_ERROR' | 'QUERY_ERROR' | 'TRANSFORM_ERROR' | 'SERVICE_ERROR' | 'UNKNOWN_ERROR';
  message: string;
  originalError?: unknown;
};

export type LocationUrisOutput = 
  | { success: true; data: NodeData[] }
  | { success: false; error: LocationUrisError };

// React Hook State Types
export type LocationUrisState = {
  treeData: NodeData[];
  loading: boolean;
  error: string | null;
};

// DatabaseConnection Core Types (Phase 3追加)
export type DatabaseConnectionInput = {
  // 現在は特に入力パラメータは不要だが、将来的な拡張のため定義
};

export type DatabaseConnectionError = {
  type: 'CONNECTION_ERROR' | 'INITIALIZATION_ERROR' | 'EVENT_ERROR' | 'UNKNOWN_ERROR';
  message: string;
  originalError?: unknown;
};

export type DatabaseConnectionOutput = 
  | { success: true; data: { dbConnection: any; isConnected: boolean } }
  | { success: false; error: DatabaseConnectionError };

// React Hook State Types
export type DatabaseConnectionState = {
  dbConnection: any | null;
  isConnected: boolean;
  error: string | null;
};
