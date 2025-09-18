#!/usr/bin/env -S deno run --allow-read --allow-write --allow-env --allow-ffi --unstable-ffi

interface QueryResult {
  [key: string]: any;
}

function displayMinimal(results: QueryResult[]) {
  if (results.length === 0) return;
  
  const columns = Object.keys(results[0]);
  
  // Header
  console.log(columns.join("\t"));
  
  // Data
  results.forEach(row => {
    const values = columns.map(col => String(row[col] ?? ""));
    console.log(values.join("\t"));
  });
}

async function main() {
  // Sample data
  const personData: QueryResult[] = [
    { "name": "Alice", "age": 30, "city": "Tokyo" },
    { "name": "Bob", "age": 25, "city": "Osaka" },
    { "name": "Charlie", "age": 35, "city": "Kyoto" }
  ];
  
  displayMinimal(personData);
  
  console.log("");
  
  const graphData: QueryResult[] = [
    { "from": "Alice", "relation": "KNOWS", "to": "Bob" },
    { "from": "Bob", "relation": "WORKS_WITH", "to": "Charlie" },
    { "from": "Alice", "relation": "MANAGES", "to": "Charlie" }
  ];
  
  displayMinimal(graphData);
}

if (import.meta.main) {
  await main();
}