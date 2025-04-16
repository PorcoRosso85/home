/**
 * graph.ts
 * 
 * グラフ構造のためのドメインエンティティ定義
 * 依存関係を表現するためのエッジリスト形式のグラフ構造を提供します
 */

/**
 * グラフのノードを表す型
 */
export type Node = {
  /** ノードの一意識別子 */
  id: string | number;
  /** ノードに関連付けられたラベル群 */
  labels: string[];
  /** ノードに関連付けられた任意のプロパティ */
  properties: Record<string, unknown>;
};

/**
 * グラフのエッジ（辺）を表す型
 */
export type Edge = {
  /** エッジの一意識別子 */
  id: string | number;
  /** 始点ノードのID */
  source: string | number;
  /** 終点ノードのID */
  target: string | number;
  /** エッジのラベル */
  label: string;
  /** エッジに関連付けられた任意のプロパティ */
  properties: Record<string, unknown>;
};

/**
 * エッジリスト形式のグラフ構造を表す型
 */
export type Graph = {
  /** グラフに含まれるノード群 */
  nodes: Node[];
  /** グラフに含まれるエッジ群 */
  edges: Edge[];
};

/**
 * ノードを作成する関数
 */
export function createNode(id: string | number, labels: string[] = [], properties: Record<string, unknown> = {}): Node {
  return {
    id,
    labels,
    properties
  };
}

/**
 * エッジを作成する関数
 */
export function createEdge(
  id: string | number,
  source: string | number,
  target: string | number,
  label: string,
  properties: Record<string, unknown> = {}
): Edge {
  return {
    id,
    source,
    target,
    label,
    properties
  };
}

/**
 * 空のグラフを作成する関数
 */
export function createGraph(): Graph {
  return {
    nodes: [],
    edges: []
  };
}

/**
 * グラフにノードを追加する関数
 * イミュータブルな操作として新しいグラフインスタンスを返します
 */
export function addNode(graph: Graph, node: Node): Graph {
  return {
    nodes: [...graph.nodes, node],
    edges: [...graph.edges]
  };
}

/**
 * グラフにエッジを追加する関数
 * イミュータブルな操作として新しいグラフインスタンスを返します
 */
export function addEdge(graph: Graph, edge: Edge): Graph {
  return {
    nodes: [...graph.nodes],
    edges: [...graph.edges, edge]
  };
}

/**
 * ノードIDからノードを検索する関数
 */
export function findNodeById(graph: Graph, nodeId: string | number): Node | undefined {
  return graph.nodes.find(node => node.id === nodeId);
}

/**
 * 指定したノードに接続する全てのエッジを取得する関数
 */
export function getConnectedEdges(graph: Graph, nodeId: string | number): Edge[] {
  return graph.edges.filter(edge => edge.source === nodeId || edge.target === nodeId);
}

/**
 * 指定したノードから出るエッジを取得する関数
 */
export function getOutgoingEdges(graph: Graph, nodeId: string | number): Edge[] {
  return graph.edges.filter(edge => edge.source === nodeId);
}

/**
 * 指定したノードに入るエッジを取得する関数
 */
export function getIncomingEdges(graph: Graph, nodeId: string | number): Edge[] {
  return graph.edges.filter(edge => edge.target === nodeId);
}
