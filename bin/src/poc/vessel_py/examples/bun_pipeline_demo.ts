#!/usr/bin/env bun
/**
 * Bun Vessel Pipeline Demo
 * Demonstrates the power of script | script | result pattern
 */

import { $ } from "bun";

console.log("=== Bun Vessel Pipeline Demo ===\n");

// 1. Simple JavaScript pipeline
console.log("1. JavaScript Pipeline:");
const result1 = await $`
  echo 'console.log(JSON.stringify({numbers: [1,2,3,4,5]}))' | bun vessel.ts | \
  bun vessel_data.ts 'const obj = JSON.parse(data); console.log(obj.numbers.reduce((a,b) => a+b, 0))'
`.text();
console.log(`   Sum of [1,2,3,4,5] = ${result1.trim()}\n`);

// 2. TypeScript pipeline with type safety
console.log("2. TypeScript Pipeline:");
const tsScript1 = `
interface Product {
  name: string;
  price: number;
}

const products: Product[] = [
  { name: "Apple", price: 1.5 },
  { name: "Banana", price: 0.8 },
  { name: "Orange", price: 2.0 }
];

console.log(JSON.stringify(products));
`;

const tsScript2 = `
interface Product {
  name: string;
  price: number;
}

const products: Product[] = JSON.parse(data);
const total = products.reduce((sum, p) => sum + p.price, 0);
console.log(\`Total: $\${total.toFixed(2)}\`);
`;

await Bun.write("temp_ts1.ts", tsScript1);
await Bun.write("vessel_data_ts.ts", `#!/usr/bin/env bun
import { tmpdir } from "os";
import { join } from "path";
import { unlink } from "fs/promises";

const script = process.argv[2];
if (!script) {
  console.error("Usage: bun vessel_data_ts.ts 'script'");
  process.exit(1);
}

const data = await Bun.stdin.text();
const tempFile = join(tmpdir(), \`vessel_data_\${Date.now()}.ts\`);

try {
  const fullScript = \`
    const data = \${JSON.stringify(data.trim())};
    \${script}
  \`;
  
  await Bun.write(tempFile, fullScript);
  await import(tempFile);
} catch (error) {
  console.error("Error:", error);
  process.exit(1);
} finally {
  try { await unlink(tempFile); } catch {}
}
`);

const result2 = await $`
  bun vessel_ts.ts < temp_ts1.ts | \
  bun vessel_data_ts.ts ${JSON.stringify(tsScript2)}
`.text();
console.log(`   ${result2.trim()}\n`);

// 3. Error handling demo
console.log("3. Error Handling:");
try {
  await $`echo 'throw new Error("Intentional error")' | bun vessel.ts`.text();
} catch (error: any) {
  console.log(`   ✓ Error caught successfully (exit code: ${error.exitCode})\n`);
}

// 4. Async operations
console.log("4. Async Operations:");
const asyncScript = `
const fetchData = async () => {
  // Simulate async operation
  await new Promise(resolve => setTimeout(resolve, 100));
  return { status: "success", timestamp: new Date().toISOString() };
};

const result = await fetchData();
console.log(JSON.stringify(result));
`;

const result4 = await $`echo ${asyncScript} | bun vessel.ts`.text();
const parsed = JSON.parse(result4);
console.log(`   Status: ${parsed.status}, Time: ${parsed.timestamp}\n`);

// Clean up
await $`rm -f temp_ts1.ts vessel_data_ts.ts`.quiet();

console.log("=== Demo Complete ===");
console.log("\nThe vessel system enables:");
console.log("- Dynamic script execution (JavaScript and TypeScript)");
console.log("- Type-safe pipelines");
console.log("- Error propagation");
console.log("- Async/await support");
console.log("- Natural command-line composition");