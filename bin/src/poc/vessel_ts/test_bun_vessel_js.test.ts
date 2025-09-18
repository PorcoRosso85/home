import { describe, test, expect } from "bun:test";
import { $ } from "bun";

describe("Bun Vessel JavaScript Tests", () => {
  test("basic script execution", async () => {
    const result = await $`echo 'console.log("Hello from Bun vessel!")' | bun vessel.ts`.text();
    expect(result.trim()).toBe("Hello from Bun vessel!");
  });

  test("async/await support", async () => {
    const script = `
      const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
      await delay(10);
      console.log("Async completed");
    `;
    const result = await $`echo ${script} | bun vessel.ts`.text();
    expect(result.trim()).toBe("Async completed");
  });

  test("error handling", async () => {
    const script = `throw new Error("Test error");`;
    
    try {
      await $`echo ${script} | bun vessel.ts`.text();
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.exitCode).toBe(1);
      expect(error.stderr.toString()).toContain("Error executing script");
    }
  });

  test("JSON processing", async () => {
    const script = `
      const data = { message: "Hello", count: 42 };
      console.log(JSON.stringify(data));
    `;
    const result = await $`echo ${script} | bun vessel.ts`.text();
    const parsed = JSON.parse(result.trim());
    expect(parsed.message).toBe("Hello");
    expect(parsed.count).toBe(42);
  });
});

describe("Bun TypeScript Vessel Tests", () => {
  test("TypeScript execution", async () => {
    const script = `
      const greeting: string = "TypeScript works!";
      console.log(greeting);
    `;
    const result = await $`echo ${script} | bun vessel_ts.ts`.text();
    expect(result.trim()).toBe("TypeScript works!");
  });

  test("interface usage", async () => {
    const script = `
      interface User {
        name: string;
        age: number;
      }
      
      const user: User = { name: "Alice", age: 25 };
      console.log(JSON.stringify(user));
    `;
    const result = await $`echo ${script} | bun vessel_ts.ts`.text();
    const parsed = JSON.parse(result.trim());
    expect(parsed.name).toBe("Alice");
    expect(parsed.age).toBe(25);
  });
});

describe("Bun Vessel Pipeline Tests", () => {
  test("JavaScript pipeline", async () => {
    // Generate data → Transform → Result
    const pipeline = await $`
      echo 'console.log(5)' | bun vessel.ts | \
      bun vessel_data.ts 'console.log(parseInt(data) * 2)'
    `.text();
    
    expect(pipeline.trim()).toBe("10");
  });

  test("mixed JS/TS pipeline", async () => {
    // JS generates data → TS processes it
    const step1 = `console.log(JSON.stringify([1, 2, 3, 4, 5]))`;
    
    const step2 = `
      const numbers: number[] = JSON.parse(data);
      const sum: number = numbers.reduce((a, b) => a + b, 0);
      console.log(sum);
    `;
    
    // Create TypeScript version of vessel_data
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
  console.error("Error executing script:", error);
  process.exit(1);
} finally {
  try { await unlink(tempFile); } catch {}
}
`);
    
    const result = await $`
      echo ${step1} | bun vessel.ts | \
      bun vessel_data_ts.ts ${step2}
    `.text();
    
    expect(result.trim()).toBe("15");
  });
});