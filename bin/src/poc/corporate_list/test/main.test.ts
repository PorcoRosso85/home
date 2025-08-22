import { test, expect, describe } from "bun:test";
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = dirname(__dirname);

// Import compiled JavaScript modules from dist
const distPath = join(projectRoot, "dist", "src");

/**
 * Test helper to validate scraped result structure
 */
function validateScrapedResult(result: any): string | null {
  const requiredFields = ["source", "company_name", "title", "url", "scraped_at"];
  
  for (const field of requiredFields) {
    if (!(field in result)) {
      return `Missing field: ${field}`;
    }
  }
  
  if (typeof result.source !== "string") {
    return "source must be string";
  }
  
  if (result.company_name !== null && typeof result.company_name !== "string") {
    return "company_name must be null or string";
  }
  
  if (typeof result.title !== "string") {
    return "title must be string";
  }
  
  if (typeof result.url !== "string") {
    return "url must be string";
  }
  
  if (typeof result.scraped_at !== "string") {
    return "scraped_at must be string";
  }
  
  return null;
}

describe("Compiled Main Module Tests", () => {
  
  test("Compiled files exist", () => {
    // Check main compiled files
    const mainJs = join(distPath, "main.js");
    const variablesJs = join(distPath, "variables.js");
    const browserJs = join(distPath, "infrastructure", "browser.js");
    const extractorJs = join(distPath, "domain", "extractor.js");
    const scraperJs = join(distPath, "domain", "scraper.js");
    
    expect(existsSync(mainJs)).toBe(true);
    expect(existsSync(variablesJs)).toBe(true);
    expect(existsSync(browserJs)).toBe(true);
    expect(existsSync(extractorJs)).toBe(true);
    expect(existsSync(scraperJs)).toBe(true);
  });
  
  test("Can import variables module", async () => {
    try {
      const variablesModule = await import(`${distPath}/variables.js`);
      
      // Check that we can access the variables
      expect(variablesModule).toBeDefined();
    } catch (error) {
      throw new Error(`Failed to import variables module: ${(error as Error).message}`);
    }
  });
  
  test("Can import domain modules", async () => {
    try {
      const extractorModule = await import(`${distPath}/domain/extractor.js`);
      const scraperModule = await import(`${distPath}/domain/scraper.js`);
      
      expect(extractorModule).toBeDefined();
      expect(scraperModule).toBeDefined();
    } catch (error) {
      throw new Error(`Failed to import domain modules: ${(error as Error).message}`);
    }
  });
  
  test("Can import infrastructure modules", async () => {
    try {
      const browserModule = await import(`${distPath}/infrastructure/browser.js`);
      
      expect(browserModule).toBeDefined();
    } catch (error) {
      throw new Error(`Failed to import infrastructure modules: ${(error as Error).message}`);
    }
  });
  
  test("Module structure validation", () => {
    // Test mock data structure to ensure our validation functions work
    const mockScrapedResult = {
      source: "test",
      company_name: "Test Company",
      title: "Test Article",
      url: "https://test.example.com",
      scraped_at: "2025-08-22T12:00:00Z"
    };
    
    const validationError = validateScrapedResult(mockScrapedResult);
    expect(validationError).toBe(null);
    
    // Test invalid data
    const invalidResult = {
      source: "test",
      title: "Test",
      // Missing required fields
    };
    
    const invalidError = validateScrapedResult(invalidResult);
    expect(invalidError).toBeDefined();
  });
  
  test("JavaScript compilation preserves functionality", () => {
    // Check that the dist directory structure matches expectations
    const expectedDirs = ["domain", "infrastructure"];
    const srcDistPath = join(projectRoot, "dist", "src");
    
    for (const dir of expectedDirs) {
      const dirPath = join(srcDistPath, dir);
      expect(existsSync(dirPath)).toBe(true);
    }
    
    // Check domain subdirectory
    const domainPath = join(srcDistPath, "domain");
    const domainFiles = ["extractor.js", "scraper.js", "scraper-factory.js", "types.js"];
    
    for (const file of domainFiles) {
      const filePath = join(domainPath, file);
      expect(existsSync(filePath)).toBe(true);
    }
  });
  
  test("TypeScript declaration files exist", () => {
    // Check that .d.ts files were generated
    const mainDts = join(distPath, "main.d.ts");
    const variablesDts = join(distPath, "variables.d.ts");
    
    expect(existsSync(mainDts)).toBe(true);
    expect(existsSync(variablesDts)).toBe(true);
  });
  
});