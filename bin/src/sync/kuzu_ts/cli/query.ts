#!/usr/bin/env -S deno run --allow-net

/**
 * KuzuDB Server Query CLI
 * サーバー側KuzuDBインスタンスにクエリを実行するCLIツール
 * 
 * Usage:
 *   deno run --allow-net cli/query.ts "MATCH (u:User) RETURN u"
 *   deno run --allow-net cli/query.ts "MATCH (u:User {id: \$id}) RETURN u" --params '{"id": "user1"}'
 *   deno run --allow-net cli/query.ts --server http://localhost:8080 "MATCH (u:User) RETURN u"
 */

import { parseArgs } from "https://deno.land/std@0.224.0/cli/parse_args.ts";

interface QueryResult {
  success: boolean;
  data?: any;
  error?: string;
}

async function queryServer(
  serverUrl: string, 
  cypher: string, 
  params?: Record<string, any>
): Promise<QueryResult> {
  try {
    const response = await fetch(`${serverUrl}/query`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ cypher, params })
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    return {
      success: false,
      error: `Failed to connect to server: ${error.message}`
    };
  }
}

function formatResult(data: any): string {
  if (!data || data.length === 0) {
    return "No results found";
  }
  
  // If data is an array of objects, format as table
  if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
    // Get all unique keys
    const keys = [...new Set(data.flatMap(obj => Object.keys(obj)))];
    
    // Calculate column widths
    const widths: Record<string, number> = {};
    for (const key of keys) {
      widths[key] = Math.max(
        key.length,
        ...data.map(obj => String(obj[key] || "").length)
      );
    }
    
    // Build header
    const header = keys.map(key => key.padEnd(widths[key])).join(" | ");
    const separator = keys.map(key => "-".repeat(widths[key])).join("-+-");
    
    // Build rows
    const rows = data.map(obj => 
      keys.map(key => String(obj[key] || "").padEnd(widths[key])).join(" | ")
    );
    
    return [header, separator, ...rows].join("\n");
  }
  
  // Otherwise, return JSON
  return JSON.stringify(data, null, 2);
}

async function main() {
  const args = parseArgs(Deno.args, {
    string: ["server", "params", "format"],
    boolean: ["help", "json"],
    default: {
      server: "http://localhost:8080",
      format: "table"
    },
    alias: {
      s: "server",
      p: "params",
      f: "format",
      h: "help",
      j: "json"
    }
  });

  if (args.help || args._.length === 0) {
    console.log(`KuzuDB Server Query CLI

Usage:
  query.ts [options] <cypher_query>

Options:
  -s, --server <url>    Server URL (default: http://localhost:8080)
  -p, --params <json>   Query parameters as JSON string
  -f, --format <type>   Output format: table, json (default: table)
  -j, --json            Shorthand for --format json
  -h, --help            Show this help message

Examples:
  # Simple query
  query.ts "MATCH (u:User) RETURN u"
  
  # Query with parameters
  query.ts "MATCH (u:User {id: \$id}) RETURN u" -p '{"id": "user1"}'
  
  # Query to different server
  query.ts -s http://remote:8080 "MATCH (n) RETURN count(n) as count"
  
  # Output as JSON
  query.ts -j "MATCH (u:User) RETURN u"
`);
    Deno.exit(0);
  }

  const cypher = args._[0] as string;
  const serverUrl = args.server;
  const format = args.json ? "json" : args.format;
  
  let params: Record<string, any> | undefined;
  if (args.params) {
    try {
      params = JSON.parse(args.params);
    } catch (error) {
      console.error(`Invalid JSON in params: ${error.message}`);
      Deno.exit(1);
    }
  }

  // Execute query
  console.error(`Querying ${serverUrl}...`);
  const result = await queryServer(serverUrl, cypher, params);
  
  if (!result.success) {
    console.error(`Error: ${result.error}`);
    Deno.exit(1);
  }
  
  // Format and output result
  if (format === "json") {
    console.log(JSON.stringify(result.data, null, 2));
  } else {
    console.log(formatResult(result.data));
  }
}

// Run the CLI
if (import.meta.main) {
  await main();
}