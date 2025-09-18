#!/usr/bin/env deno run

console.log("🔐 Environment Variable Access Demo");
console.log("==================================");

function tryGetEnv(varName: string) {
  try {
    const value = Deno.env.get(varName);
    if (value) {
      console.log(`✅ Successfully read ${varName}:`);
      console.log(`   Value: ${value.substring(0, 20)}${value.length > 20 ? '...' : ''}`);
    } else {
      console.log(`⚠️  ${varName} is not set`);
    }
  } catch (error) {
    console.log(`❌ Failed to read ${varName}:`);
    console.log(`   Error: ${error.message}`);
  }
}

function trySetEnv(varName: string, value: string) {
  try {
    Deno.env.set(varName, value);
    console.log(`✅ Successfully set ${varName}`);
  } catch (error) {
    console.log(`❌ Failed to set ${varName}:`);
    console.log(`   Error: ${error.message}`);
  }
}

console.log("\n1. Attempting to read HOME:");
tryGetEnv("HOME");

console.log("\n2. Attempting to read PATH:");
tryGetEnv("PATH");

console.log("\n3. Attempting to read API_KEY:");
tryGetEnv("API_KEY");

console.log("\n4. Attempting to set TEST_VAR:");
trySetEnv("TEST_VAR", "test_value");

console.log("\n5. Attempting to read all environment variables:");
try {
  const allEnv = Deno.env.toObject();
  console.log(`✅ Successfully read all env vars: ${Object.keys(allEnv).length} variables found`);
} catch (error) {
  console.log(`❌ Failed to read all env vars:`);
  console.log(`   Error: ${error.message}`);
}

console.log("\n");
console.log("💡 Try running with different permissions:");
console.log("   deno run --allow-env=HOME,PATH src/env_access.ts");
console.log("   deno run --allow-env src/env_access.ts");