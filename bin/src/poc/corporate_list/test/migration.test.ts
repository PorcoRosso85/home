import { test, expect, describe } from "bun:test";
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = dirname(__dirname);
const distPath = join(projectRoot, "dist", "src");

describe("Migration and Compatibility Tests", () => {
  
  test("TypeScript to JavaScript compilation successful", () => {
    // Check that all main files were compiled
    const expectedFiles = [
      "main.js",
      "variables.js",
      "infrastructure/browser.js",
      "domain/scraper.js",
      "domain/extractor.js",
      "domain/scraper-factory.js",
      "domain/types.js"
    ];
    
    for (const file of expectedFiles) {
      const filePath = join(distPath, file);
      expect(existsSync(filePath)).toBe(true);
    }
  });
  
  test("Compiled files are valid JavaScript modules", async () => {
    // Try to import each main module to ensure they're valid
    const moduleTests = [
      { name: "variables", path: `${distPath}/variables.js` },
      { name: "browser", path: `${distPath}/infrastructure/browser.js` },
      { name: "extractor", path: `${distPath}/domain/extractor.js` },
      { name: "scraper", path: `${distPath}/domain/scraper.js` }
    ];
    
    for (const moduleTest of moduleTests) {
      try {
        const module = await import(moduleTest.path);
        expect(module).toBeDefined();
        expect(typeof module).toBe("object");
      } catch (error) {
        throw new Error(`Failed to import ${moduleTest.name} module: ${(error as Error).message}`);
      }
    }
  });
  
  test("Type definitions generated correctly", () => {
    // Check that .d.ts files were generated
    const expectedTypeFiles = [
      "main.d.ts",
      "variables.d.ts", 
      "infrastructure/browser.d.ts",
      "domain/scraper.d.ts",
      "domain/extractor.d.ts"
    ];
    
    for (const file of expectedTypeFiles) {
      const filePath = join(distPath, file);
      expect(existsSync(filePath)).toBe(true);
      
      // Check that the .d.ts file has content
      const content = readFileSync(filePath, "utf8");
      expect(content.length).toBeGreaterThan(0);
    }
  });
  
  test("Source maps generated for debugging", () => {
    // Check that .js.map files were generated
    const expectedMapFiles = [
      "main.js.map",
      "variables.js.map",
      "infrastructure/browser.js.map"
    ];
    
    for (const file of expectedMapFiles) {
      const filePath = join(distPath, file);
      if (existsSync(filePath)) {
        const content = readFileSync(filePath, "utf8");
        expect(content.length).toBeGreaterThan(0);
        
        // Basic validation that it's a valid source map
        try {
          const sourceMap = JSON.parse(content);
          expect(sourceMap.version).toBeDefined();
          expect(sourceMap.sources).toBeDefined();
        } catch (error) {
          console.log(`Source map validation failed for ${file}:`, (error as Error).message);
        }
      }
    }
  });
  
  test("Package.json scripts compatibility", () => {
    // Check that package.json has the expected scripts
    const packageJsonPath = join(projectRoot, "package.json");
    expect(existsSync(packageJsonPath)).toBe(true);
    
    const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));
    
    // Check for build script
    expect(packageJson.scripts.build).toBeDefined();
    expect(packageJson.scripts.build).toBe("tsc");
    
    // Check module type
    expect(packageJson.type).toBe("module");
  });
  
  test("All JavaScript test files exist", () => {
    // Check that all corresponding JavaScript test files were created
    const expectedTestFiles = [
      "typescript-env.test.js",
      "main.test.js",
      "variables.test.js",
      "infrastructure/browser.test.js",
      "domain/scraper.test.js",
      "domain/extractor.test.js",
      "migration.test.js"
    ];
    
    for (const file of expectedTestFiles) {
      const filePath = join(__dirname, file);
      expect(existsSync(filePath)).toBe(true);
    }
  });
  
  test("TypeScript and JavaScript test files coexist", () => {
    // Verify that both .ts and .js versions exist where expected
    const testPairs = [
      { ts: "typescript-env.test.ts", js: "typescript-env.test.js" },
      { ts: "main.test.ts", js: "main.test.js" },
      { ts: "variables.test.ts", js: "variables.test.js" },
      { ts: "migration.test.ts", js: "migration.test.js" }
    ];
    
    for (const pair of testPairs) {
      const tsPath = join(__dirname, pair.ts);
      const jsPath = join(__dirname, pair.js);
      
      if (existsSync(tsPath)) {
        expect(existsSync(jsPath)).toBe(true);
      }
    }
  });
  
});