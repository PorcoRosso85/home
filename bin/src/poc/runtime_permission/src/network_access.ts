#!/usr/bin/env deno run

console.log("🌐 Network Access Demo");
console.log("=====================");

async function tryFetch(url: string) {
  try {
    const response = await fetch(url);
    console.log(`✅ Successfully fetched ${url}:`);
    console.log(`   Status: ${response.status} ${response.statusText}`);
  } catch (error) {
    console.log(`❌ Failed to fetch ${url}:`);
    console.log(`   Error: ${error.message}`);
  }
}

console.log("\n1. Attempting to fetch https://api.github.com:");
await tryFetch("https://api.github.com");

console.log("\n2. Attempting to fetch https://jsonplaceholder.typicode.com/posts/1:");
await tryFetch("https://jsonplaceholder.typicode.com/posts/1");

console.log("\n3. Attempting to fetch http://localhost:8000:");
await tryFetch("http://localhost:8000");

console.log("\n");
console.log("💡 Try running with different permissions:");
console.log("   deno run --allow-net=api.github.com src/network_access.ts");
console.log("   deno run --allow-net=localhost:8000 src/network_access.ts");
console.log("   deno run --allow-net src/network_access.ts");