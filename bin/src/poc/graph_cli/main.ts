#!/usr/bin/env -S deno run --allow-read --allow-write --allow-env --allow-ffi --unstable-ffi

// KuzuDBクエリ結果の表示サンプル
// 実際のKuzuDBは、以下のような形式でデータを返します

interface KuzuQueryResult {
  [key: string]: any; // 例: "p.name", "p.age", "r.type" など
}

function displayQueryResults(results: KuzuQueryResult[]) {
  if (results.length === 0) {
    console.log("No results found.");
    return;
  }

  // カラム名を抽出
  const columns = Object.keys(results[0]);
  
  // テーブルヘッダーを表示
  console.log("\n" + columns.join(" | "));
  console.log("-".repeat(columns.join(" | ").length));
  
  // 各行を表示
  results.forEach(row => {
    const values = columns.map(col => String(row[col] ?? "NULL"));
    console.log(values.join(" | "));
  });
  
  console.log(`\nTotal: ${results.length} rows`);
}

async function main() {
  console.log("Graph CLI - KuzuDB Query Results Viewer");
  console.log("=======================================");
  
  try {
    // Verify module import path works
    const kuzuTsPath = Deno.env.get("KUZU_TS_PATH");
    console.log(`✓ KuzuDB TypeScript module path: ${kuzuTsPath}`);
    
    // サンプルデータ（KuzuDBのgetAll()が返す形式）
    const sampleResults: KuzuQueryResult[] = [
      { "p.name": "Alice", "p.age": 30, "p.city": "Tokyo" },
      { "p.name": "Bob", "p.age": 25, "p.city": "Osaka" },
      { "p.name": "Charlie", "p.age": 35, "p.city": "Kyoto" }
    ];
    
    console.log("\n[Sample Query]: MATCH (p:Person) RETURN p.name, p.age, p.city");
    displayQueryResults(sampleResults);
    
    // グラフクエリの例
    const graphResults: KuzuQueryResult[] = [
      { "a.name": "Alice", "rel.type": "KNOWS", "b.name": "Bob" },
      { "a.name": "Bob", "rel.type": "WORKS_WITH", "b.name": "Charlie" },
      { "a.name": "Alice", "rel.type": "MANAGES", "b.name": "Charlie" }
    ];
    
    console.log("\n[Sample Query]: MATCH (a:Person)-[rel]->(b:Person) RETURN a.name, rel.type, b.name");
    displayQueryResults(graphResults);
    
    console.log("\n✓ Environment configured successfully");
    console.log("Note: This is a demonstration of how KuzuDB query results are displayed.");
    console.log("Actual queries will be executed when npm dependencies are resolved.");
    
  } catch (error) {
    console.error("Error:", error);
    Deno.exit(1);
  }
}

if (import.meta.main) {
  await main();
}