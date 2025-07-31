#!/usr/bin/env bun

// Test if Bun can load the native kuzu module
console.log("Testing native kuzu module loading in Bun...\n");

try {
  // Try to require the native module directly
  console.log("1. Attempting to load kuzu module...");
  const path = require('path');
  const modulePath = path.join(__dirname, '..', 'node_modules', 'kuzu');
  console.log("   Module path:", modulePath);
  
  const kuzu = require(modulePath);
  console.log("✓ Module loaded successfully");
  console.log("   Available exports:", Object.keys(kuzu));
  
  // Try to create a database
  console.log("\n2. Testing database creation...");
  const db = new kuzu.Database(":memory:");
  console.log("✓ Database created");
  
  console.log("\n✅ Bun CAN load and use the native kuzu module!");
} catch (error) {
  console.error("\n❌ Failed to load native module:");
  console.error("   Error:", error.message);
  
  // Check if it's a native module issue
  if (error.message.includes("dlopen") || error.message.includes(".node")) {
    console.error("\n⚠️  This appears to be a native module compatibility issue.");
    console.error("   Bun may not be compatible with the prebuilt kuzu binaries.");
  }
}