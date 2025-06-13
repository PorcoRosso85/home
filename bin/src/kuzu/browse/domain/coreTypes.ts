/**
 * 基盤型定義 - 汎用的な基本型
 * CONVENTION.yaml準拠: type定義優先
 */

export type ChangeType = 'CREATE' | 'UPDATE' | 'DELETE';

export type LocationChange = {
  uri_id: string;
  change_type: ChangeType;
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
  contextData?: {
    queryResult?: any;
    renderingData?: any;
  };
};
