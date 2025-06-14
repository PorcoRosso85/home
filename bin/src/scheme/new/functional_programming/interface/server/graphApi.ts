/**
 * グラフAPI
 * 
 * 依存関係グラフデータを提供するAPIエンドポイント
 */

import { Graph } from "../../domain/entities/graph.ts";

/**
 * グラフデータAPIエンドポイント
 * @param req HTTPリクエスト
 * @returns HTTPレスポンス
 */
export async function handleGraphApi(req: Request): Promise<Response> {
  try {
    // 実際の実装では、domain/service/graphBuilder.tsなどを使ってグラフを構築する
    // 例: const buildDependencyGraph = await import("../../domain/service/graphBuilder.ts").then(m => m.buildDependencyGraph);
    // const graph = buildDependencyGraph(schema, "root");
    
    // TODO: 実際のFunction.meta.jsonからグラフを構築
    const data: Graph = {
      nodes: [
        {
          id: "domain/service/functionDependencyAnalyzer.ts:::getFunctionDependency",
          labels: ["Function"],
          properties: {
            description: "関数の依存関係を取得",
            returnType: "FunctionDependency"
          }
        },
        {
          id: "domain/service/functionDependencyAnalyzer.ts:::dependencyToString",
          labels: ["Function"],
          properties: {
            description: "依存関係を文字列に変換"
          }
        },
        {
          id: "domain/service/graphBuilder.ts:::buildDependencyGraph",
          labels: ["Function"],
          properties: {
            description: "スキーマから依存関係グラフを構築"
          }
        },
        {
          id: "domain/entities/graph.ts:::createNode",
          labels: ["Function"],
          properties: {
            description: "ノードを作成"
          }
        },
        {
          id: "domain/entities/graph.ts:::createEdge",
          labels: ["Function"],
          properties: {
            description: "エッジを作成"
          }
        }
      ],
      edges: [
        {
          id: "edge1",
          source: "domain/service/functionDependencyAnalyzer.ts:::getFunctionDependency",
          target: "domain/service/functionDependencyAnalyzer.ts:::dependencyToString",
          label: "calls",
          properties: { order: 1 }
        },
        {
          id: "edge2",
          source: "domain/service/graphBuilder.ts:::buildDependencyGraph",
          target: "domain/entities/graph.ts:::createNode",
          label: "calls",
          properties: { order: 1 }
        },
        {
          id: "edge3",
          source: "domain/service/graphBuilder.ts:::buildDependencyGraph",
          target: "domain/entities/graph.ts:::createEdge",
          label: "calls",
          properties: { order: 2 }
        }
      ]
    };
    
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    console.error("グラフAPI処理エラー:", error);
    return new Response(
      JSON.stringify({ error: "グラフデータの取得中にエラーが発生しました" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
