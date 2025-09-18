#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --no-check

/**
 * test-function-graph.ts
 * 
 * Function.meta.jsonを使用したグラフ構築テスト
 * 実際のFunction.meta.jsonファイルを読み込み、依存関係グラフを構築してテストします
 */

import { buildDependencyGraph } from "../domain/service/graphBuilder.ts";
import { serializeToJson, convertToMermaid } from "../application/serializers/graphSerializer.ts";

async function main() {
  console.log("Function.meta.jsonからの依存関係グラフ構築テスト");
  
  try {
    // Function.meta.jsonファイルを読み込む
    const functionSchemaText = await Deno.readTextFile("./Function.meta.json");
    const functionSchema = JSON.parse(functionSchemaText);
    
    console.log(`Function.meta.jsonを読み込みました: ${functionSchema.title}`);
    
    // グラフを構築
    console.log("依存関係グラフを構築中...");
    const graph = buildDependencyGraph(functionSchema, "Function");
    
    // 結果を出力
    console.log(`グラフ構築完了: ノード数=${graph.nodes.length}, エッジ数=${graph.edges.length}`);
    
    // ノードタイプの集計
    const referenceNodes = graph.nodes.filter(n => n.labels.includes("reference"));
    console.log(`参照ノード数: ${referenceNodes.length}`);
    
    // 循環参照の検出
    const circularEdges = graph.edges.filter(e => (e.properties as any).isCircular === true);
    console.log(`循環参照エッジ数: ${circularEdges.length}`);
    
    // Mermaid形式での出力
    console.log("\n=== Mermaid形式のグラフ ===");
    console.log(convertToMermaid(graph));
    
    // 結果をファイルに保存
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    await Deno.writeTextFile(`function-graph-${timestamp}.json`, serializeToJson(graph));
    await Deno.writeTextFile(`function-graph-${timestamp}.md`, 
      "# Function.meta.json Dependency Graph\n\n" +
      "```mermaid\n" + 
      convertToMermaid(graph) + 
      "\n```"
    );
    
    console.log(`\n結果をファイルに保存しました:`);
    console.log(`- function-graph-${timestamp}.json`);
    console.log(`- function-graph-${timestamp}.md`);
    
  } catch (error) {
    console.error("エラーが発生しました:", error.message);
  }
}

// スクリプトが直接実行された場合のみmain関数を実行
if (import.meta.main) {
  main();
}
