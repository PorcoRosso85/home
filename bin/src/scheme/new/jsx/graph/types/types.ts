// types.ts - 型定義

// 共通のURI情報
export interface Uri {
  protocol: string;
  path: string;
  parameters?: {
    branch?: string;
    version?: string;
    template?: string;
    port?: number;
    host?: string;
    query?: string;
    fragment?: string;
    username?: string;
    password?: string;
    [key: string]: any;
  };
}

// 実装情報
export interface Implementation {
  status: string;
  progress: number;
  assignee?: string;
  lastUpdated?: string;
  notes?: string;
  issues?: string[];
  location?: Uri;
}

// ドキュメント参照
export interface DocumentationReference {
  type: string;
  url: string;
  title: string;
  description?: string;
}

// 共通メタデータ
export interface Metadata {
  implementation?: Implementation;
  documentation?: DocumentationReference[];
  complexity?: string;
  dependencies?: string[];
  [key: string]: any;
}

// D3.js表示用のノード設定
export interface NodeD3Config {
  coords?: {
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
    vx?: number;
    vy?: number;
  };
  visual?: {
    radius?: number;
    color?: string;
  };
}

// D3.js表示用のエッジ設定
export interface EdgeD3Config {
  visual?: {
    strokeWidth?: number;
    style?: string;
    color?: string;
    curvature?: number;
    label?: boolean;
  };
}

// データスキーマ
export interface DataSchema {
  title: string;
  type: string;
  description?: string;
  properties?: Record<string, any>;
  required?: string[];
  additionalProperties?: boolean;
}

// リトライポリシー
export interface RetryPolicy {
  maxRetries: number;
  backoffFactor?: number;
  statusCodes?: number[];
}

// ノード
export interface Node {
  id: string;
  name: string;
  type: string;
  description: string;
  schema: DataSchema;
  tags: string[];
  validationRules?: string[];
  metadata?: Metadata;
  d3?: NodeD3Config;
}

// エッジ
export interface Edge {
  id: string;
  source: string;
  target: string;
  name: string;
  description: string;
  type?: string;
  properties?: {
    async?: boolean;
    timeout?: number;
    retry?: RetryPolicy;
    [key: string]: any;
  };
  metadata?: Metadata;
  d3?: EdgeD3Config;
}

// サブグラフ
export interface Subgraph {
  id: string;
  name: string;
  description: string;
  nodeIds: string[];
  metadata?: Metadata;
}

// グラフメタデータ
export interface GraphMetadata {
  version: string;
  lastUpdated: string;
  author: string;
  description: string;
  stats: {
    nodeCount: number;
    edgeCount: number;
    subgraphCount: number;
    implementationStats?: {
      completed: number;
      inProgress: number;
      planned: number;
    };
  };
  statusSummary: Record<string, number>;
  tags: string[];
}

// グラフデータ全体
export interface GraphData {
  nodes: Record<string, Node>;
  edges: Edge[];
  subgraphs: Subgraph[];
  metadata: GraphMetadata;
}
