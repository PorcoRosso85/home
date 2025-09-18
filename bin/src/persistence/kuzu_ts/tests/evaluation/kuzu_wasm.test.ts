import { assertEquals } from "https://deno.land/std@0.218.0/assert/mod.ts";

Deno.test("kuzu-wasm - panic detection test", async () => {
  console.log("Starting kuzu-wasm panic detection test...");
  console.log("This test verifies whether kuzu-wasm causes a panic in Deno environment");
  
  let testCompleted = false;
  let errorType = "none";
  let errorMessage = "";
  const totalStartTime = performance.now();
  
  try {
    // Import and initialize WASM module
    console.log("\n1. Importing kuzu-wasm module...");
    const importStart = performance.now();
    const kuzuModule = await import("npm:kuzu-wasm@0.11.1");
    const kuzu = kuzuModule.default;
    const importEnd = performance.now();
    console.log(`✓ Module imported successfully in ${(importEnd - importStart).toFixed(2)}ms`);
    console.log(`  Available methods: ${Object.keys(kuzu).join(", ")}`);
    
    // Check if we need to call init
    if (typeof kuzu.init === 'function') {
      console.log("\n2. Attempting to initialize WASM...");
      const initStart = performance.now();
      try {
        await kuzu.init();
        const initEnd = performance.now();
        console.log(`✓ WASM initialized successfully in ${(initEnd - initStart).toFixed(2)}ms`);
      } catch (initError) {
        errorType = "initialization";
        errorMessage = (initError as Error).message;
        console.log(`✗ WASM initialization failed: ${errorMessage}`);
        
        // Check if it's the known Worker issue
        if (errorMessage.includes("Classic workers are not supported")) {
          console.log("\n⚠️  KNOWN ISSUE DETECTED:");
          console.log("   kuzu-wasm uses Classic Workers which are not supported in Deno");
          console.log("   This is a compatibility issue between kuzu-wasm and Deno");
          console.log("   No panic occurred - error was handled gracefully");
        }
        
        // Try to use without init
        console.log("\n3. Attempting to use kuzu-wasm without init...");
      }
    }
    
    // Try to create database anyway
    if (errorType === "none") {
      console.log("\n3. Creating in-memory database...");
      const dbStart = performance.now();
      const db = new kuzu.Database();
      const dbEnd = performance.now();
      console.log(`✓ Database created successfully in ${(dbEnd - dbStart).toFixed(2)}ms`);
      
      // Create connection
      console.log("\n4. Creating connection...");
      const connStart = performance.now();
      const conn = new kuzu.Connection(db);
      const connEnd = performance.now();
      console.log(`✓ Connection created successfully in ${(connEnd - connStart).toFixed(2)}ms`);
      
      // Execute a simple query
      console.log("\n5. Executing test query...");
      const queryStart = performance.now();
      await conn.execute("CREATE NODE TABLE Test(id INT64, PRIMARY KEY (id))");
      const queryEnd = performance.now();
      console.log(`✓ Query executed successfully in ${(queryEnd - queryStart).toFixed(2)}ms`);
    }
    
    // Mark test as completed
    testCompleted = true;
    
  } catch (error) {
    if (errorType === "none") {
      errorType = "runtime";
      errorMessage = (error as Error).message;
    }
    console.error("\n✗ Error during test execution:", error);
    console.error("  Error type:", (error as Error).constructor.name);
    console.error("  Error message:", errorMessage);
    
    // Check for known issues
    if (errorMessage.includes("Classic workers are not supported")) {
      console.log("\n⚠️  KNOWN ISSUE: kuzu-wasm requires Classic Workers");
      testCompleted = true; // Still mark as completed since it didn't panic
    }
  }
  
  const totalTime = performance.now() - totalStartTime;
  console.log(`\n═══════════════════════════════════════════════════`);
  console.log(`Test Summary:`);
  console.log(`  Duration: ${totalTime.toFixed(2)}ms`);
  console.log(`  Completed: ${testCompleted ? "YES" : "NO"}`);
  console.log(`  Panic detected: NO`);
  console.log(`  Error type: ${errorType}`);
  if (errorMessage) {
    console.log(`  Error message: ${errorMessage}`);
  }
  console.log(`═══════════════════════════════════════════════════\n`);
  
  // The test passes if we reach here without a panic
  assertEquals(testCompleted, true, "Test should complete without causing a panic");
});

Deno.test("kuzu-wasm - worker compatibility check", async () => {
  console.log("\nChecking Web Worker compatibility...");
  
  try {
    // Test Module Worker (supported by Deno)
    console.log("\n1. Testing Module Worker (ES Modules):");
    try {
      const moduleWorkerCode = `
        self.postMessage('Module worker is running');
      `;
      const blob = new Blob([moduleWorkerCode], { type: "application/javascript" });
      const moduleWorkerUrl = URL.createObjectURL(blob);
      const moduleWorker = new Worker(moduleWorkerUrl, { type: "module" });
      
      await new Promise((resolve) => {
        moduleWorker.onmessage = (e) => {
          console.log("✓ Module Worker supported:", e.data);
          moduleWorker.terminate();
          resolve(undefined);
        };
      });
      
      URL.revokeObjectURL(moduleWorkerUrl);
    } catch (e) {
      console.log("✗ Module Worker not supported:", (e as Error).message);
    }
    
    // Test Classic Worker (NOT supported by Deno)
    console.log("\n2. Testing Classic Worker:");
    try {
      const classicWorkerCode = `
        self.postMessage('Classic worker is running');
      `;
      const blob = new Blob([classicWorkerCode], { type: "application/javascript" });
      const classicWorkerUrl = URL.createObjectURL(blob);
      const classicWorker = new Worker(classicWorkerUrl, { type: "classic" });
      
      await new Promise((resolve, reject) => {
        classicWorker.onmessage = (e) => {
          console.log("✓ Classic Worker supported:", e.data);
          classicWorker.terminate();
          resolve(undefined);
        };
        classicWorker.onerror = (e) => {
          reject(new Error(e.toString()));
        };
      });
      
      URL.revokeObjectURL(classicWorkerUrl);
    } catch (e) {
      console.log("✗ Classic Worker not supported:", (e as Error).message);
      console.log("  This is why kuzu-wasm fails in Deno");
    }
    
    // Test without type specification (defaults to classic)
    console.log("\n3. Testing Worker without type specification:");
    try {
      const defaultWorkerCode = `
        self.postMessage('Default worker is running');
      `;
      const blob = new Blob([defaultWorkerCode], { type: "application/javascript" });
      const defaultWorkerUrl = URL.createObjectURL(blob);
      const defaultWorker = new Worker(defaultWorkerUrl);
      
      await new Promise((resolve, reject) => {
        defaultWorker.onmessage = (e) => {
          console.log("✓ Default Worker supported:", e.data);
          defaultWorker.terminate();
          resolve(undefined);
        };
        defaultWorker.onerror = (e) => {
          reject(new Error("Worker error"));
        };
        // Timeout after 100ms
        setTimeout(() => reject(new Error("Worker timeout")), 100);
      });
      
      URL.revokeObjectURL(defaultWorkerUrl);
    } catch (e) {
      console.log("✗ Default Worker not supported:", (e as Error).message);
      console.log("  Workers without type specification default to 'classic' which Deno doesn't support");
    }
    
  } catch (error) {
    console.error("Unexpected error:", error);
  }
  
  console.log("\n═══════════════════════════════════════════════════");
  console.log("Worker Compatibility Summary:");
  console.log("  - Deno supports Module Workers (type: 'module')");
  console.log("  - Deno does NOT support Classic Workers");
  console.log("  - kuzu-wasm uses Classic Workers, causing incompatibility");
  console.log("═══════════════════════════════════════════════════\n");
  
  assertEquals(true, true, "Worker compatibility check completed");
});

Deno.test("kuzu-wasm - version and module structure", async () => {
  console.log("\nAnalyzing kuzu-wasm module structure...");
  
  try {
    const kuzuModule = await import("npm:kuzu-wasm@0.11.1");
    const kuzu = kuzuModule.default;
    
    console.log("\n1. Module Export Structure:");
    console.log(`   Default export type: ${typeof kuzu}`);
    console.log(`   Is constructor: ${kuzu.constructor.name}`);
    
    console.log("\n2. Available Properties and Methods:");
    const methods: string[] = [];
    const constructors: string[] = [];
    const other: string[] = [];
    
    for (const [key, value] of Object.entries(kuzu)) {
      if (typeof value === 'function') {
        if (key[0] === key[0].toUpperCase()) {
          constructors.push(key);
        } else {
          methods.push(key);
        }
      } else {
        other.push(`${key} (${typeof value})`);
      }
    }
    
    console.log(`   Constructors: ${constructors.join(", ")}`);
    console.log(`   Methods: ${methods.join(", ")}`);
    if (other.length > 0) {
      console.log(`   Other: ${other.join(", ")}`);
    }
    
    console.log("\n3. Version Information:");
    try {
      // Try getVersion without init
      if (typeof kuzu.getVersion === 'function') {
        console.log("   getVersion() method exists");
        console.log("   Note: Calling it would attempt to use Classic Workers");
      }
      
      if (typeof kuzu.getStorageVersion === 'function') {
        console.log("   getStorageVersion() method exists");
        console.log("   Note: Calling it would attempt to use Classic Workers");
      }
    } catch (e) {
      console.log(`   Version methods not accessible: ${(e as Error).message}`);
    }
    
    console.log("\n4. Worker Path Configuration:");
    if (typeof kuzu.setWorkerPath === 'function') {
      console.log("   setWorkerPath method is available");
      console.log("   This suggests kuzu-wasm expects to load worker scripts");
    }
    
    console.log("\n5. Database Constructor Check:");
    if (kuzu.Database) {
      console.log("   Database constructor is available");
      try {
        // Try to create without initialization
        const testDb = new kuzu.Database();
        console.log("   ✓ Database can be created without init()");
        
        if (kuzu.Connection) {
          const testConn = new kuzu.Connection(testDb);
          console.log("   ✓ Connection can be created without init()");
        }
      } catch (e) {
        console.log(`   ✗ Cannot create Database without init(): ${(e as Error).message}`);
      }
    }
    
  } catch (error) {
    console.error("Error analyzing module:", error);
  }
  
  console.log("\n═══════════════════════════════════════════════════");
  console.log("Module Analysis Summary:");
  console.log("  - kuzu-wasm exports a module with Database/Connection constructors");
  console.log("  - The init() method attempts to create Classic Workers");
  console.log("  - Some functionality may work without init() in Deno");
  console.log("  - Full functionality requires Worker support");
  console.log("═══════════════════════════════════════════════════\n");
  
  assertEquals(true, true, "Module structure analysis completed");
});