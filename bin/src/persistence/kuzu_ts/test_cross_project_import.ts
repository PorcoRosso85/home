#!/usr/bin/env -S deno run --allow-all --unstable-worker-options

/**
 * Test cross-project import issue
 * This simulates how sync/kuzu_ts would import the Worker implementation
 */

// This simulates an import from another project
console.log("=== Testing Cross-Project Import ===");
console.log("Current directory:", Deno.cwd());

// First, let's check if we can create a Worker with absolute path
const workerPath = new URL("./core/kuzu_worker.ts", import.meta.url).pathname;
console.log("Worker path:", workerPath);

try {
  // Test 1: Can we create the Worker?
  console.log("\n1. Creating Worker...");
  const worker = new Worker(workerPath, { type: "module" });
  
  // Test 2: Can the Worker resolve npm:kuzu?
  console.log("2. Testing Worker message passing...");
  
  const testMessage = {
    id: "test_1",
    type: "createDatabase",
    payload: { path: ":memory:" }
  };
  
  const responsePromise = new Promise((resolve, reject) => {
    worker.onmessage = (event) => {
      console.log("✅ Worker response received:", event.data);
      resolve(event.data);
    };
    
    worker.onerror = (error) => {
      console.error("❌ Worker error:", error);
      reject(error);
    };
  });
  
  worker.postMessage(testMessage);
  
  const response = await responsePromise;
  console.log("3. Test completed successfully!");
  
  worker.terminate();
  
} catch (error) {
  console.error("❌ Test failed:", error);
  console.error("\nThis demonstrates the cross-project import issue:");
  console.error("- Worker is created from the calling project's context");
  console.error("- npm:kuzu is not available in the calling project");
  console.error("- The Worker cannot resolve npm:kuzu imports");
}

console.log("\n=== Analysis ===");
console.log("The issue occurs because:");
console.log("1. Worker runs in the context of the calling project");
console.log("2. sync/kuzu_ts doesn't have npm:kuzu in its dependencies");
console.log("3. The Worker cannot access persistence/kuzu_ts's node_modules");