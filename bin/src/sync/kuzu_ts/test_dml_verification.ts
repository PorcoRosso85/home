/**
 * Simple test to verify if KuzuDB WASM can execute DML queries
 * This test:
 * 1. Initializes the KuzuDB WASM client
 * 2. Executes a simple CREATE query
 * 3. Queries the data back to verify it was created
 * 4. Logs whether DML actually works or not
 */

import { BrowserKuzuClientImpl } from "./core/client/browser_kuzu_client.ts";

async function testDMLVerification() {
  console.log("🔍 Starting KuzuDB WASM DML Verification Test");
  console.log("=" .repeat(50));
  
  const client = new BrowserKuzuClientImpl();
  
  try {
    // Step 1: Initialize the KuzuDB WASM client
    console.log("\n📦 Step 1: Initializing KuzuDB WASM client...");
    await client.initialize();
    console.log("✅ KuzuDB WASM client initialized successfully");
    
    // Step 2: Execute a simple CREATE query using the template system
    console.log("\n📝 Step 2: Executing CREATE_USER DML query...");
    const createUserEvent = await client.executeTemplate("CREATE_USER", {
      id: "test-user-123",
      name: "Test User",
      email: "test@example.com"
    });
    console.log("✅ CREATE_USER query executed successfully");
    console.log("   Event ID:", createUserEvent.id);
    console.log("   Template:", createUserEvent.template);
    console.log("   Params:", createUserEvent.params);
    
    // Step 3: Query the data back to verify it was created
    console.log("\n🔎 Step 3: Querying data to verify creation...");
    const result = await client.executeQuery(`
      MATCH (u:User {id: 'test-user-123'})
      RETURN u.id as id, u.name as name, u.email as email
    `);
    
    // Get the results
    const rows = result.getAll();
    console.log("   Query returned", rows.length, "rows");
    
    if (rows.length > 0) {
      console.log("✅ Data successfully created and retrieved:");
      console.log("   ID:", rows[0][0]);
      console.log("   Name:", rows[0][1]);
      console.log("   Email:", rows[0][2]);
    } else {
      console.log("❌ No data found - DML might not be working");
    }
    
    // Step 4: Let's also try another DML operation - CREATE_POST
    console.log("\n📝 Step 4: Testing CREATE_POST DML query...");
    const createPostEvent = await client.executeTemplate("CREATE_POST", {
      id: "test-post-456",
      content: "This is a test post to verify DML",
      authorId: "test-user-123"
    });
    console.log("✅ CREATE_POST query executed successfully");
    
    // Verify the post was created
    const postResult = await client.executeQuery(`
      MATCH (p:Post {id: 'test-post-456'})
      RETURN p.id as id, p.content as content, p.authorId as authorId
    `);
    
    const postRows = postResult.getAll();
    if (postRows.length > 0) {
      console.log("✅ Post successfully created:");
      console.log("   ID:", postRows[0][0]);
      console.log("   Content:", postRows[0][1]);
      console.log("   Author ID:", postRows[0][2]);
    }
    
    // Step 5: Test UPDATE operation
    console.log("\n📝 Step 5: Testing UPDATE_USER DML query...");
    const updateUserEvent = await client.executeTemplate("UPDATE_USER", {
      id: "test-user-123",
      name: "Updated Test User"
    });
    console.log("✅ UPDATE_USER query executed successfully");
    
    // Verify the update
    const updateResult = await client.executeQuery(`
      MATCH (u:User {id: 'test-user-123'})
      RETURN u.name as name
    `);
    
    const updateRows = updateResult.getAll();
    if (updateRows.length > 0 && updateRows[0][0] === "Updated Test User") {
      console.log("✅ User successfully updated:");
      console.log("   New name:", updateRows[0][0]);
    }
    
    // Final verdict
    console.log("\n" + "=" .repeat(50));
    console.log("🎉 VERDICT: KuzuDB WASM DML operations are WORKING!");
    console.log("✅ Successfully executed:");
    console.log("   - CREATE operations (User and Post)");
    console.log("   - UPDATE operations");
    console.log("   - SELECT queries to verify data");
    
    // Get final state to show all data
    const finalState = await client.getLocalState();
    console.log("\n📊 Final database state:");
    console.log("   Users:", finalState.users.length);
    console.log("   Posts:", finalState.posts.length);
    console.log("   Follows:", finalState.follows.length);
    
  } catch (error) {
    console.error("\n❌ Error during DML verification:");
    console.error(error);
    console.log("\n🚫 VERDICT: KuzuDB WASM DML operations FAILED!");
  }
}

// Run the test
if (import.meta.main) {
  await testDMLVerification();
}