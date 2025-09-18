import { describe, test, expect } from "bun:test";
import { $ } from "bun";

describe("Bun Vessel Tests", () => {
  test("basic script execution", async () => {
    const result = await $`echo 'console.log("Hello from Bun vessel!")' | bun vessel.ts`.text();
    expect(result.trim()).toBe("Hello from Bun vessel!");
  });

  test("TypeScript execution", async () => {
    const script = `
      const greeting: string = "TypeScript works!";
      console.log(greeting);
    `;
    const result = await $`echo ${script} | bun vessel.ts`.text();
    expect(result.trim()).toBe("TypeScript works!");
  });

  test("async/await support", async () => {
    const script = `
      const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      await delay(10);
      console.log("Async completed");
    `;
    const result = await $`echo ${script} | bun vessel.ts`.text();
    expect(result.trim()).toBe("Async completed");
  });

  test("Bun-specific features", async () => {
    const script = `
      // Use Bun's $ for shell commands
      const files = await $\`ls -la | head -1\`.text();
      console.log("Shell output received");
    `;
    const result = await $`echo ${script} | bun vessel.ts`.text();
    expect(result.trim()).toContain("Shell output received");
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

describe("Bun Vessel Pipeline Tests", () => {
  test("simple pipeline", async () => {
    // Generate data → Transform → Result
    const pipeline = await $`
      echo 'console.log(5)' | bun vessel.ts | \
      bun vessel_data.ts 'console.log(parseInt(data) * 2)'
    `.text();
    
    expect(pipeline.trim()).toBe("10");
  });

  test("TypeScript pipeline", async () => {
    const step1 = `
      interface User { name: string; age: number; }
      const users: User[] = [
        { name: "Alice", age: 25 },
        { name: "Bob", age: 30 }
      ];
      console.log(JSON.stringify(users));
    `;
    
    const step2 = `
      interface User { name: string; age: number; }
      const users: User[] = JSON.parse(data);
      const avgAge = users.reduce((sum, u) => sum + u.age, 0) / users.length;
      console.log(avgAge);
    `;
    
    const result = await $`
      echo ${step1} | bun vessel.ts | \
      bun vessel_data.ts ${step2}
    `.text();
    
    expect(result.trim()).toBe("27.5");
  });
});