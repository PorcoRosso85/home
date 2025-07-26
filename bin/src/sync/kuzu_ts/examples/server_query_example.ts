#!/usr/bin/env -S deno run --allow-net

/**
 * Server Query Example
 * サーバー側KuzuDBクエリ機能のデモンストレーション
 * 
 * このサンプルは以下を実演します:
 * 1. サーバーの起動確認
 * 2. テストデータの作成
 * 3. 様々なクエリの実行
 * 4. CLIツールの使用例
 */

// Query helper function
async function queryServer(cypher: string, params?: Record<string, any>) {
  const response = await fetch("http://localhost:8080/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cypher, params })
  });
  
  const result = await response.json();
  if (!result.success) {
    throw new Error(result.error);
  }
  
  return result.data;
}

// Check server status
async function checkServerStatus() {
  try {
    const response = await fetch("http://localhost:8080/state");
    const state = await response.json();
    console.log("Server Status:", state);
    return true;
  } catch (error) {
    console.error("Server not available:", error.message);
    return false;
  }
}

async function main() {
  console.log("=== Server Query Example ===\n");
  
  // Check if server is running
  if (!await checkServerStatus()) {
    console.log("\nPlease start the server first:");
    console.log("  deno run --allow-net --allow-read serve.ts");
    Deno.exit(1);
  }
  
  console.log("\n1. Count all nodes:");
  try {
    const countResult = await queryServer("MATCH (n) RETURN count(n) as count");
    console.log(`   Total nodes: ${countResult[0]?.count || 0}`);
  } catch (error) {
    console.log("   No nodes found (empty database)");
  }
  
  console.log("\n2. Query all users:");
  try {
    const users = await queryServer("MATCH (u:User) RETURN u.id as id, u.name as name, u.email as email");
    if (users.length > 0) {
      console.log("   Users found:");
      users.forEach(user => {
        console.log(`   - ${user.id}: ${user.name} (${user.email})`);
      });
    } else {
      console.log("   No users found");
    }
  } catch (error) {
    console.log("   Error:", error.message);
  }
  
  console.log("\n3. Query with parameters:");
  try {
    const result = await queryServer(
      "MATCH (u:User {id: $userId}) RETURN u.name as name",
      { userId: "user1" }
    );
    if (result.length > 0) {
      console.log(`   Found user: ${result[0].name}`);
    } else {
      console.log("   User not found");
    }
  } catch (error) {
    console.log("   Error:", error.message);
  }
  
  console.log("\n4. Complex query - Find followers:");
  try {
    const followers = await queryServer(`
      MATCH (follower:User)-[:FOLLOWS]->(target:User)
      RETURN follower.name as followerName, target.name as targetName
    `);
    if (followers.length > 0) {
      console.log("   Relationships found:");
      followers.forEach(rel => {
        console.log(`   - ${rel.followerName} follows ${rel.targetName}`);
      });
    } else {
      console.log("   No follow relationships found");
    }
  } catch (error) {
    console.log("   Error:", error.message);
  }
  
  console.log("\n5. Aggregation query:");
  try {
    const stats = await queryServer(`
      MATCH (u:User)
      OPTIONAL MATCH (u)-[:FOLLOWS]->(other:User)
      RETURN u.name as user, count(other) as followingCount
      ORDER BY followingCount DESC
    `);
    if (stats.length > 0) {
      console.log("   User follow statistics:");
      stats.forEach(stat => {
        console.log(`   - ${stat.user}: following ${stat.followingCount} users`);
      });
    } else {
      console.log("   No statistics available");
    }
  } catch (error) {
    console.log("   Error:", error.message);
  }
  
  console.log("\n=== CLI Tool Examples ===");
  console.log("\nYou can also use the CLI tool directly:");
  console.log('  ./cli/query.ts "MATCH (u:User) RETURN u"');
  console.log('  ./cli/query.ts "MATCH (u:User {id: $id}) RETURN u" -p \'{"id": "user1"}\'');
  console.log('  ./cli/query.ts -j "MATCH (n) RETURN count(n) as count"');
  console.log('  ./cli/query.ts --help');
}

// Run the example
if (import.meta.main) {
  await main();
}