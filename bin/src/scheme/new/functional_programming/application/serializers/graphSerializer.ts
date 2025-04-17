/**
 * graphSerializer.ts
 * 
 * グラフ構造を様々な形式にシリアライズするための関数群
 * クリーンアーキテクチャのアプリケーション層に位置する
 */

import { Graph, Node, Edge } from "../../domain/entities/graph.ts";

/**
 * グラフをJSON形式にシリアライズする
 * 
 * @param graph グラフ構造
 * @returns JSON文字列
 */
export function serializeToJson(graph: Graph): string {
  return JSON.stringify(graph, null, 2);
}

/**
 * グラフをGraphViz DOT形式に変換する
 * 
 * @param graph グラフ構造
 * @param directed 有向グラフとして出力するか（デフォルト: true）
 * @returns DOT形式の文字列
 */
export function convertToDot(graph: Graph, directed: boolean = true): string {
  const graphType = directed ? "digraph" : "graph";
  const arrow = directed ? " -> " : " -- ";
  
  let dotString = `${graphType} DependencyGraph {\n`;
  dotString += "  // ノード定義\n";
  
  // ノード定義
  for (const node of graph.nodes) {
    const labels = node.labels.length > 0 ? node.labels.join(", ") : "";
    const label = `${node.id}${labels ? "\\n" + labels : ""}`;
    dotString += `  "${node.id}" [label="${label}"];\n`;
  }
  
  dotString += "\n  // エッジ定義\n";
  
  // エッジ定義
  for (const edge of graph.edges) {
    dotString += `  "${edge.source}"${arrow}"${edge.target}" [label="${edge.label}"];\n`;
  }
  
  dotString += "}\n";
  return dotString;
}

/**
 * グラフをMermaid形式に変換する
 * 
 * @param graph グラフ構造
 * @param flowchart フローチャートの方向（デフォルト: "TD"（上から下））
 * @returns Mermaid形式の文字列
 */
export function convertToMermaid(graph: Graph, flowchart: "TB" | "TD" | "BT" | "RL" | "LR" = "TD"): string {
  let mermaidString = `graph ${flowchart}\n`;
  
  // ノード定義
  for (const node of graph.nodes) {
    const labels = node.labels.length > 0 ? node.labels.join(", ") : "";
    const label = `${node.id}${labels ? "<br>" + labels : ""}`;
    mermaidString += `  ${node.id}["${label}"]\n`;
  }
  
  // エッジ定義
  for (const edge of graph.edges) {
    mermaidString += `  ${edge.source} -->|${edge.label}| ${edge.target}\n`;
  }
  
  return mermaidString;
}

/**
 * グラフをCSV形式（ノードとエッジの2つのファイル）に変換する
 * 
 * @param graph グラフ構造
 * @returns [ノードCSV, エッジCSV]のタプル
 */
export function convertToCsv(graph: Graph): [string, string] {
  // ノードCSV
  let nodesCSV = "id,labels,properties\n";
  for (const node of graph.nodes) {
    const labels = node.labels.join(";");
    const properties = JSON.stringify(node.properties).replace(/"/g, '""');
    nodesCSV += `"${node.id}","${labels}","${properties}"\n`;
  }
  
  // エッジCSV
  let edgesCSV = "id,source,target,label,properties\n";
  for (const edge of graph.edges) {
    const properties = JSON.stringify(edge.properties).replace(/"/g, '""');
    edgesCSV += `"${edge.id}","${edge.source}","${edge.target}","${edge.label}","${properties}"\n`;
  }
  
  return [nodesCSV, edgesCSV];
}

/**
 * グラフをテキスト形式（インデント付き）で表示する
 * 
 * @param graph グラフ構造
 * @returns インデント付きのテキスト表現
 */
export function convertToText(graph: Graph): string {
  // ノードをマップに変換して高速アクセスできるようにする
  const nodeMap = new Map<string | number, Node>();
  for (const node of graph.nodes) {
    nodeMap.set(node.id, node);
  }
  
  // エッジをソースノードごとにグループ化
  const outgoingEdges = new Map<string | number, Edge[]>();
  for (const edge of graph.edges) {
    if (!outgoingEdges.has(edge.source)) {
      outgoingEdges.set(edge.source, []);
    }
    outgoingEdges.get(edge.source)!.push(edge);
  }
  
  // ルートノードを探す（エッジの到達先だが始点ではないノード）
  const targetNodes = new Set<string | number>(graph.edges.map(e => e.target));
  const sourceNodes = new Set<string | number>(graph.edges.map(e => e.source));
  const rootNodeIds = [...nodeMap.keys()].filter(id => !targetNodes.has(id) || sourceNodes.has(id) && !graph.edges.some(e => e.target === id));
  
  let result = "依存関係グラフ:\n";
  
  // ルートノードが見つからない場合は任意のノードから開始
  if (rootNodeIds.length === 0 && graph.nodes.length > 0) {
    rootNodeIds.push(graph.nodes[0].id);
  }
  
  // 各ルートノードから再帰的に依存関係を構築
  const visited = new Set<string | number>();
  for (const rootId of rootNodeIds) {
    result += buildTextRepresentation(rootId, nodeMap, outgoingEdges, visited, 0);
  }
  
  // 孤立したノード（どのエッジにも関与していないノード）を追加
  const isolatedNodes = graph.nodes.filter(node => 
    !graph.edges.some(edge => edge.source === node.id || edge.target === node.id)
  );
  
  if (isolatedNodes.length > 0) {
    result += "\n孤立したノード:\n";
    for (const node of isolatedNodes) {
      result += `  - ${node.id} [${node.labels.join(", ")}]\n`;
    }
  }
  
  return result;
}

/**
 * 再帰的にテキスト表現を構築する内部関数
 */
function buildTextRepresentation(
  nodeId: string | number,
  nodeMap: Map<string | number, Node>,
  outgoingEdges: Map<string | number, Edge[]>,
  visited: Set<string | number>,
  depth: number
): string {
  // 循環参照を防ぐ
  if (visited.has(nodeId)) {
    return `${"  ".repeat(depth)}${nodeId} (循環参照)\n`;
  }
  
  visited.add(nodeId);
  const node = nodeMap.get(nodeId);
  if (!node) {
    return `${"  ".repeat(depth)}${nodeId} (不明なノード)\n`;
  }
  
  let result = `${"  ".repeat(depth)}${node.id} [${node.labels.join(", ")}]\n`;
  
  // 外向きエッジを処理
  const edges = outgoingEdges.get(nodeId) || [];
  for (const edge of edges) {
    result += `${"  ".repeat(depth + 1)}|-- ${edge.label} --> ${edge.target}\n`;
    // 対象ノードを再帰的に処理
    result += buildTextRepresentation(edge.target, nodeMap, outgoingEdges, new Set(visited), depth + 2);
  }
  
  return result;
}
