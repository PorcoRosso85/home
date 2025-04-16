// Node型の定義
export interface NodeType {
  id: string;
  name: string;
  type: string;
  description: string;
  schema?: {
    title: string;
    type: string;
    properties: Record<string, any>;
    required: string[];
  };
  metadata?: {
    implementation?: {
      status: string;
      progress: number;
      assignee: string;
      lastUpdated: string;
      notes?: string;
      issues?: string[];
      location?: {
        protocol: string;
        path: string;
      };
    };
    documentation?: Array<{
      type: string;
      url: string;
      title: string;
    }>;
    complexity?: string;
    dependencies?: string[];
  };
  tags?: string[];
}

// Edge型の定義
export interface EdgeType {
  id: string;
  source: string;
  target: string;
  name: string;
  description: string;
  type: string;
  properties?: Record<string, any>;
  metadata?: {
    implementation?: {
      status: string;
      progress: number;
      assignee: string;
      lastUpdated: string;
      issues?: string[];
      notes?: string;
      location?: {
        protocol: string;
        path: string;
      };
    };
    documentation?: Array<{
      type: string;
      url: string;
      title: string;
    }>;
    complexity?: string;
    dependencies?: string[];
  };
  d3?: {
    visual?: {
      strokeWidth?: number;
      style?: string;
      color?: string;
    };
  };
}

// サブグラフ型の定義
export interface SubgraphType {
  id: string;
  name: string;
  description: string;
  nodeIds: string[];
  metadata?: {
    implementation?: {
      status: string;
      progress: number;
    };
    documentation?: Array<{
      type: string;
      url: string;
      title: string;
    }>;
  };
  tags?: string[];
}

// メタデータ型の定義
export interface MetadataType {
  version: string;
  lastUpdated: string;
  author: string;
  description: string;
  stats: {
    nodeCount: number;
    edgeCount: number;
    subgraphCount: number;
  };
  statusSummary: Record<string, number>;
  tags: string[];
}

// フロントエンド用のノード型（表示用に拡張）
export interface FrontendNodeType {
  id: string;
  name: string;
  path: string;
  children?: FrontendNodeType[];
}

// ハイライトデータの型
export interface HighlightDataType {
  [key: string]: number;
  _minPosition: number;
  _maxPosition: number;
  _boxCount: number;
}

// ノードデータマップの型
export interface NodesMapType {
  [key: string]: NodeType;
}

// エッジ配列の型
export type EdgesArrayType = EdgeType[];

// ファイルノード型の定義（createNestedStructureで使用）
export interface FileNodeType {
  name: string;
  path: string;
}

// ストレージ情報型の定義
export interface StorageInfoType {
  used: number;
  total: number;
  percentage: number;
}

// ファイルロード結果型の定義
export interface FileLoadResultType {
  name: string;
  content: any;
}

// グラフデータ整合性チェック結果型の定義
export interface GraphValidationResultType {
  valid: boolean;
  errors: string[];
}

// 関数依存関係型の定義
export interface FunctionDependencyType {
  from: string;
  to: string;
}

// エクスポートファイル種類型の定義
export type ExportFileType = 'nodes' | 'edges' | 'subgraphs' | 'metadata';

// ノードサービスレスポンス型の定義
export interface NodeServiceResponseType<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// 関数ノード検索条件型の定義
export interface FunctionNodeSearchType {
  path?: string;
  name?: string;
  type?: string;
  status?: string;
  tag?: string;
}
