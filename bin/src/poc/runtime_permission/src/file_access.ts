#!/usr/bin/env deno run

console.log("🗂️  File Access Demo");
console.log("==================");

async function tryReadFile(path: string) {
  try {
    const content = await Deno.readTextFile(path);
    console.log(`✅ Successfully read ${path}:`);
    console.log(`   Content: ${content.substring(0, 50)}...`);
  } catch (error) {
    console.log(`❌ Failed to read ${path}:`);
    console.log(`   Error: ${error.message}`);
  }
}

async function tryWriteFile(path: string, content: string) {
  try {
    await Deno.writeTextFile(path, content);
    console.log(`✅ Successfully wrote to ${path}`);
  } catch (error) {
    console.log(`❌ Failed to write to ${path}:`);
    console.log(`   Error: ${error.message}`);
  }
}

console.log("\n1. Attempting to read /etc/passwd (system file):");
await tryReadFile("/etc/passwd");

console.log("\n2. Attempting to read current file:");
await tryReadFile("./src/file_access.ts");

console.log("\n3. Attempting to write to ./data/test.txt:");
await tryWriteFile("./data/test.txt", "Hello from Deno!");

console.log("\n4. Attempting to write to /tmp/test.txt:");
await tryWriteFile("/tmp/test.txt", "Hello from Deno!");

console.log("\n");
console.log("💡 Try running with different permissions:");
console.log("   deno run --allow-read=./src src/file_access.ts");
console.log("   deno run --allow-read --allow-write=./data src/file_access.ts");
console.log("   deno run --allow-all src/file_access.ts");