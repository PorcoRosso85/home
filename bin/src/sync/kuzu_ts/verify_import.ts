// Verify that KuzuTsClient can import persistence/kuzu_ts correctly
import { KuzuTsClientImpl } from "./core/client/kuzu_ts_client.ts";

console.log("=== Import Resolution Verification ===\n");

const client = new KuzuTsClientImpl();
console.log("✅ KuzuTsClientImpl instantiated");

try {
  await client.initialize();
  console.log("✅ Successfully initialized with persistence/kuzu_ts");
  
  // Test basic functionality
  const version = client.getSchemaVersion();
  console.log(`✅ Schema version: ${version}`);
  
  // Create a user
  const event = await client.executeTemplate("CREATE_USER", {
    id: "test-user-1",
    name: "Test User",
    email: "test@example.com"
  });
  
  console.log("✅ Created user event:", event.id);
  
  // Get local state
  const state = await client.getLocalState();
  console.log("✅ Local state has", state.users.length, "users");
  
  console.log("\n🎉 SUCCESS: KuzuTsClient is working with correct import resolution!");
  
} catch (error) {
  console.error("❌ Error:", error.message);
  console.error("\nThis may be due to:");
  console.error("1. persistence/kuzu_ts module issues");
  console.error("2. V8 isolate lifecycle problems");
  console.error("3. Missing native KuzuDB bindings");
}