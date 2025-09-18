import { test, expect } from "bun:test";
import { getConfig, SEARCH_KEYWORDS, TARGET_SITES, BROWSER_CONFIG, EXTRACTION_CONFIG } from "../src/variables";

// Save original environment variables to restore later
const originalEnv = { ...process.env };

/**
 * Restore original environment variables
 */
function restoreEnv() {
  // Clear any test environment variables
  delete process.env.SCRAPER_KEYWORDS;
  delete process.env.SCRAPER_TIMEOUT;
  delete process.env.SCRAPER_WAIT_TIME;
  delete process.env.SCRAPER_MAX_TITLE_LENGTH;
  delete process.env.SCRAPER_USER_AGENT;
  delete process.env.SCRAPER_PRTIMES_URL;

  // Restore original environment
  Object.assign(process.env, originalEnv);
}

test("Configuration constants are properly exported", () => {
  // Test that default constants exist and have expected structure
  expect(Array.isArray(SEARCH_KEYWORDS)).toBe(true);
  expect(SEARCH_KEYWORDS.length).toBeGreaterThan(0);
  
  expect(typeof TARGET_SITES).toBe("object");
  expect(typeof TARGET_SITES.PR_TIMES).toBe("string");
  expect(TARGET_SITES.PR_TIMES).toContain("prtimes.jp");
  
  expect(typeof BROWSER_CONFIG).toBe("object");
  expect(typeof BROWSER_CONFIG.userAgent).toBe("string");
  expect(typeof BROWSER_CONFIG.timeout).toBe("number");
  expect(typeof BROWSER_CONFIG.waitTime).toBe("number");
  expect(Array.isArray(BROWSER_CONFIG.launchArgs)).toBe(true);
  
  expect(typeof EXTRACTION_CONFIG).toBe("object");
  expect(typeof EXTRACTION_CONFIG.maxTitleLength).toBe("number");
  expect(Array.isArray(EXTRACTION_CONFIG.companyPatterns)).toBe(true);
});

test("getConfig() returns default configuration without environment variables", () => {
  // Ensure no test environment variables are set
  restoreEnv();
  
  const config = getConfig();
  
  // Verify structure
  expect(typeof config).toBe("object");
  expect(Array.isArray(config.searchKeywords)).toBe(true);
  expect(typeof config.targetSites).toBe("object");
  expect(typeof config.browser).toBe("object");
  expect(typeof config.extraction).toBe("object");
  
  // Verify default values
  expect(config.searchKeywords).toEqual(SEARCH_KEYWORDS);
  expect(config.targetSites.PR_TIMES).toBe(TARGET_SITES.PR_TIMES);
  expect(config.browser.userAgent).toBe(BROWSER_CONFIG.userAgent);
  expect(config.browser.timeout).toBe(BROWSER_CONFIG.timeout);
  expect(config.browser.waitTime).toBe(BROWSER_CONFIG.waitTime);
  expect(config.browser.launchArgs).toEqual(BROWSER_CONFIG.launchArgs);
  expect(config.extraction.maxTitleLength).toBe(EXTRACTION_CONFIG.maxTitleLength);
  expect(config.extraction.companyPatterns).toEqual(EXTRACTION_CONFIG.companyPatterns);
});

test("getConfig() respects environment variable overrides", () => {
  // Set test environment variables
  process.env.SCRAPER_KEYWORDS = "テスト1,テスト2,テスト3";
  process.env.SCRAPER_TIMEOUT = "45000";
  process.env.SCRAPER_WAIT_TIME = "5000";
  process.env.SCRAPER_MAX_TITLE_LENGTH = "150";
  process.env.SCRAPER_USER_AGENT = "Test User Agent";
  process.env.SCRAPER_PRTIMES_URL = "https://test.example.com/search?q=";
  
  const config = getConfig();
  
  // Verify environment variable overrides
  expect(config.searchKeywords).toEqual(["テスト1", "テスト2", "テスト3"]);
  expect(config.browser.timeout).toBe(45000);
  expect(config.browser.waitTime).toBe(5000);
  expect(config.extraction.maxTitleLength).toBe(150);
  expect(config.browser.userAgent).toBe("Test User Agent");
  expect(config.targetSites.PR_TIMES).toBe("https://test.example.com/search?q=");
  
  // Verify unchanged defaults
  expect(config.browser.launchArgs).toEqual(BROWSER_CONFIG.launchArgs);
  expect(config.extraction.companyPatterns).toEqual(EXTRACTION_CONFIG.companyPatterns);
  
  // Clean up
  restoreEnv();
});

test("getConfig() handles malformed environment variables gracefully", () => {
  // Set malformed environment variables
  process.env.SCRAPER_KEYWORDS = ""; // Empty string
  process.env.SCRAPER_TIMEOUT = "not-a-number"; // Invalid number
  process.env.SCRAPER_WAIT_TIME = "-1000"; // Negative number (but valid integer)
  process.env.SCRAPER_MAX_TITLE_LENGTH = "invalid";
  
  const config = getConfig();
  
  // Should fall back to defaults for invalid values
  expect(config.searchKeywords).toEqual(SEARCH_KEYWORDS);
  expect(config.browser.timeout).toBe(BROWSER_CONFIG.timeout);
  expect(config.browser.waitTime).toBe(-1000);
  expect(config.extraction.maxTitleLength).toBe(EXTRACTION_CONFIG.maxTitleLength);
  
  // Clean up
  restoreEnv();
});

test("getConfig() properly parses comma-separated keywords", () => {
  // Test various keyword formats
  const testCases = [
    {
      input: "keyword1,keyword2,keyword3",
      expected: ["keyword1", "keyword2", "keyword3"]
    },
    {
      input: " keyword1 , keyword2 , keyword3 ", // With spaces
      expected: ["keyword1", "keyword2", "keyword3"]
    },
    {
      input: "keyword1,,keyword2,", // With empty segments
      expected: ["keyword1", "keyword2"]
    },
    {
      input: "single-keyword",
      expected: ["single-keyword"]
    }
  ];
  
  for (const testCase of testCases) {
    process.env.SCRAPER_KEYWORDS = testCase.input;
    const config = getConfig();
    
    expect(config.searchKeywords).toEqual(testCase.expected);
  }
  
  // Clean up
  restoreEnv();
});

test("Configuration maintains type safety", () => {
  const config = getConfig();
  
  // Verify all types are correct
  expect(Array.isArray(config.searchKeywords) && config.searchKeywords.every(k => typeof k === "string")).toBe(true);
  expect(typeof config.targetSites === "object" && typeof config.targetSites.PR_TIMES === "string").toBe(true);
  expect(typeof config.browser).toBe("object");
  expect(typeof config.browser.userAgent).toBe("string");
  expect(typeof config.browser.timeout).toBe("number");
  expect(typeof config.browser.waitTime).toBe("number");
  expect(Array.isArray(config.browser.launchArgs) && config.browser.launchArgs.every(a => typeof a === "string")).toBe(true);
  expect(typeof config.extraction).toBe("object");
  expect(typeof config.extraction.maxTitleLength).toBe("number");
  expect(Array.isArray(config.extraction.companyPatterns) && config.extraction.companyPatterns.every(p => p instanceof RegExp)).toBe(true);
});

test("Module import works correctly", () => {
  // Test that we can import the module and access its exports
  expect(typeof getConfig).toBe("function");
  expect(SEARCH_KEYWORDS).toBeDefined();
  expect(TARGET_SITES).toBeDefined();
  expect(BROWSER_CONFIG).toBeDefined();
  expect(EXTRACTION_CONFIG).toBeDefined();
});