/**
 * UI関連型定義 - React Hook State Types
 */
import type { VersionState, NodeData, NodeClickEvent } from './coreTypes';

// React Hook State Types
export type VersionStatesState = {
  versions: VersionState[];
  loading: boolean;
  error: string | null;
};

export type LocationUrisState = {
  treeData: NodeData[];
  loading: boolean;
  error: string | null;
};

export type DatabaseConnectionState = {
  dbConnection: any | null;
  isConnected: boolean;
  error: string | null;
};

export type SimpleClaudeAnalysisState = {
  loading: boolean;
  result: string | null;
  error: string | null;
};

export type PageState = {
  selectedVersionId: string;
};

export type ContextMenuState = {
  show: boolean;
  x: number;
  y: number;
  node: NodeData | null;
};

export type VersionStatesReactState = {
  expandedVersions: Set<string>;
  contextMenu: ContextMenuState;
};

// Tree・Node UI Types
export type TreeInput = {
  treeData: NodeData[];
  onNodeClick?: (clickEvent: NodeClickEvent) => void;
};

export type TreeOutput = {
  hasData: boolean;
  emptyMessage: string;
  renderableNodes: NodeData[];
};

export type NodeInput = {
  node: NodeData;
  onNodeClick?: (clickEvent: NodeClickEvent) => void;
  parentOpacity: number;
};

export type NodeStyleOutput = {
  backgroundColor: string;
  textColor: string;
  secondaryTextColor: string;
  tertiaryTextColor: string;
  nodeTextColor: string;
  currentOpacity: number;
};

export type NodeOutput = {
  hasChildren: boolean;
  styles: NodeStyleOutput;
  handleClick: (e: React.MouseEvent) => void;
  handleContextMenu: (e: React.MouseEvent) => void;
};

// Re-export for convenience
export type { VersionState, NodeData, NodeClickEvent };
