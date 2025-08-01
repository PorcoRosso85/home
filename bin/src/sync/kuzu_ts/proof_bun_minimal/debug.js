// Debug script to check environment
const fs = require("fs");
const path = require("path");

console.log("🔍 Debug Information:");
console.log("CWD:", process.cwd());
console.log("Script location:", __filename);

// Check node_modules
const nodeModulesPath = path.join(process.cwd(), "node_modules");
console.log("\nnode_modules exists?", fs.existsSync(nodeModulesPath));

if (fs.existsSync(nodeModulesPath)) {
  console.log("node_modules contents:", fs.readdirSync(nodeModulesPath));
  
  const kuzuPath = path.join(nodeModulesPath, "kuzu");
  console.log("\nkuzu exists?", fs.existsSync(kuzuPath));
  
  if (fs.existsSync(kuzuPath)) {
    console.log("kuzu is symlink?", fs.lstatSync(kuzuPath).isSymbolicLink());
    if (fs.lstatSync(kuzuPath).isSymbolicLink()) {
      console.log("kuzu symlink target:", fs.readlinkSync(kuzuPath));
    }
  }
}

// Try different require approaches
console.log("\n🧪 Testing require approaches:");
try {
  const kuzu1 = require("kuzu");
  console.log("✅ require('kuzu') worked!");
} catch (e) {
  console.log("❌ require('kuzu') failed:", e.message);
}

try {
  const kuzu2 = require("./node_modules/kuzu");
  console.log("✅ require('./node_modules/kuzu') worked!");
} catch (e) {
  console.log("❌ require('./node_modules/kuzu') failed:", e.message);
}