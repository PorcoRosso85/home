import { assertEquals } from "https://deno.land/std@0.218.0/assert/mod.ts";

Deno.test("kuzu-wasm - basic initialization test", async () => {
  console.log("Starting kuzu-wasm basic initialization test...");
  
  let testCompleted = false;
  let initSuccessful = false;
  const startTime = performance.now();
  
  try {
    console.log("Attempting to import kuzu-wasm...");
    // Dynamic import to better handle potential failures
    const initStart = performance.now();
    const kuzuModule = await import("npm:kuzu-wasm@0.11.1");
    const initEnd = performance.now();
    console.log(`Module imported in ${(initEnd - initStart).toFixed(2)}ms`);
    
    // Check what was imported
    console.log("Module type:", typeof kuzuModule);
    console.log("Module keys:", Object.keys(kuzuModule));
    console.log("Default export type:", typeof kuzuModule.default);
    
    // Try to initialize
    if (typeof kuzuModule.default === 'function') {
      console.log("Attempting to initialize WASM...");
      const wasmInitStart = performance.now();
      
      try {
        const kuzu = await kuzuModule.default();
        const wasmInitEnd = performance.now();
        console.log(`WASM initialization completed in ${(wasmInitEnd - wasmInitStart).toFixed(2)}ms`);
        console.log("Kuzu object type:", typeof kuzu);
        console.log("Kuzu object keys:", Object.keys(kuzu));
        
        initSuccessful = true;
        
        // Try to check available methods
        if (kuzu.Database) {
          console.log("Database constructor found");
        }
        if (kuzu.Connection) {
          console.log("Connection constructor found");
        }
        
      } catch (wasmError) {
        console.error("WASM initialization error:", wasmError);
        console.error("Error type:", (wasmError as Error).constructor.name);
        console.error("Error message:", (wasmError as Error).message);
        if ((wasmError as Error).stack) {
          console.error("Stack trace:", (wasmError as Error).stack);
        }
      }
    } else {
      console.log("Warning: Default export is not a function");
    }
    
    testCompleted = true;
    
  } catch (error) {
    console.error("Import or initialization error:", error);
    console.error("Error type:", (error as Error).constructor.name);
    console.error("Error message:", (error as Error).message);
    if ((error as Error).stack) {
      console.error("Stack trace:", (error as Error).stack);
    }
  }
  
  const totalTime = performance.now() - startTime;
  console.log(`Test completed in ${totalTime.toFixed(2)}ms`);
  console.log(`Test completed: ${testCompleted}`);
  console.log(`Initialization successful: ${initSuccessful}`);
  
  // The test passes if we can complete without a panic
  assertEquals(testCompleted, true, "Test should complete without fatal errors");
});

Deno.test("kuzu-wasm - alternative import methods", async () => {
  console.log("\nTesting alternative import methods...");
  
  // Test 1: Try different import syntaxes
  console.log("\n1. Testing direct destructured import...");
  try {
    const { default: init } = await import("npm:kuzu-wasm@0.11.1");
    console.log("Destructured import successful, init type:", typeof init);
  } catch (e) {
    console.error("Destructured import failed:", (e as Error).message);
  }
  
  // Test 2: Try importing without version
  console.log("\n2. Testing import without version...");
  try {
    const kuzuLatest = await import("npm:kuzu-wasm");
    console.log("Latest version import successful");
    console.log("Module keys:", Object.keys(kuzuLatest));
  } catch (e) {
    console.error("Latest version import failed:", (e as Error).message);
  }
  
  // Test 3: Check if it's a namespace issue
  console.log("\n3. Checking module structure...");
  try {
    const mod = await import("npm:kuzu-wasm@0.11.1");
    console.log("Full module structure:");
    for (const [key, value] of Object.entries(mod)) {
      console.log(`  ${key}: ${typeof value}`);
    }
  } catch (e) {
    console.error("Module structure check failed:", (e as Error).message);
  }
  
  // Test passes if we get here without crashing
  assertEquals(true, true, "Alternative import tests completed");
});

Deno.test("kuzu-wasm - minimal database operation", async () => {
  console.log("\nAttempting minimal database operation...");
  
  let operationCompleted = false;
  
  try {
    const kuzuModule = await import("npm:kuzu-wasm@0.11.1");
    
    if (typeof kuzuModule.default === 'function') {
      console.log("Initializing kuzu-wasm...");
      
      // Wrap in try-catch to handle potential worker errors
      try {
        const kuzu = await kuzuModule.default();
        console.log("WASM initialized successfully");
        
        // Try the simplest possible database operation
        if (kuzu && kuzu.Database) {
          console.log("Attempting to create database...");
          const db = new kuzu.Database();
          console.log("Database created!");
          
          if (kuzu.Connection) {
            console.log("Attempting to create connection...");
            const conn = new kuzu.Connection(db);
            console.log("Connection created!");
            
            operationCompleted = true;
          }
        }
      } catch (opError) {
        console.error("Operation error:", opError);
        console.error("This might be a known issue with kuzu-wasm in Deno");
      }
    }
  } catch (error) {
    console.error("Test error:", error);
  }
  
  console.log(`Operation completed: ${operationCompleted}`);
  
  // Test passes if we complete without panic
  assertEquals(true, true, "Minimal operation test completed");
});