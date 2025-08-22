#!/usr/bin/env node
/**
 * Variables Configuration Test
 * 
 * Tests the configuration loading functionality from variables.ts
 * including environment variable support and default value fallbacks.
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { getConfig, SEARCH_KEYWORDS, TARGET_SITES, BROWSER_CONFIG, EXTRACTION_CONFIG, type ScraperConfig } from '../src/variables.js'

// Save original environment variables to restore later
const originalEnv = { ...process.env }

/**
 * Restore original environment variables
 */
function restoreEnv(): void {
  // Clear any test environment variables
  delete process.env.SCRAPER_KEYWORDS
  delete process.env.SCRAPER_TIMEOUT
  delete process.env.SCRAPER_WAIT_TIME
  delete process.env.SCRAPER_MAX_TITLE_LENGTH
  delete process.env.SCRAPER_USER_AGENT
  delete process.env.SCRAPER_PRTIMES_URL

  // Restore original environment
  Object.assign(process.env, originalEnv)
}

test('Configuration constants are properly exported', async () => {
  // Test that default constants exist and have expected structure
  assert.ok(Array.isArray(SEARCH_KEYWORDS), 'SEARCH_KEYWORDS should be an array')
  assert.ok(SEARCH_KEYWORDS.length > 0, 'SEARCH_KEYWORDS should not be empty')
  
  assert.ok(typeof TARGET_SITES === 'object', 'TARGET_SITES should be an object')
  assert.ok(typeof TARGET_SITES.PR_TIMES === 'string', 'TARGET_SITES.PR_TIMES should be a string')
  assert.ok(TARGET_SITES.PR_TIMES.includes('prtimes.jp'), 'PR_TIMES URL should contain prtimes.jp')
  
  assert.ok(typeof BROWSER_CONFIG === 'object', 'BROWSER_CONFIG should be an object')
  assert.ok(typeof BROWSER_CONFIG.userAgent === 'string', 'userAgent should be a string')
  assert.ok(typeof BROWSER_CONFIG.timeout === 'number', 'timeout should be a number')
  assert.ok(typeof BROWSER_CONFIG.waitTime === 'number', 'waitTime should be a number')
  assert.ok(Array.isArray(BROWSER_CONFIG.launchArgs), 'launchArgs should be an array')
  
  assert.ok(typeof EXTRACTION_CONFIG === 'object', 'EXTRACTION_CONFIG should be an object')
  assert.ok(typeof EXTRACTION_CONFIG.maxTitleLength === 'number', 'maxTitleLength should be a number')
  assert.ok(Array.isArray(EXTRACTION_CONFIG.companyPatterns), 'companyPatterns should be an array')
  
  console.log('✅ All configuration constants are properly structured')
})

test('getConfig() returns default configuration without environment variables', async () => {
  // Ensure no test environment variables are set
  restoreEnv()
  
  const config = getConfig()
  
  // Verify structure
  assert.ok(typeof config === 'object', 'Config should be an object')
  assert.ok(Array.isArray(config.searchKeywords), 'searchKeywords should be an array')
  assert.ok(typeof config.targetSites === 'object', 'targetSites should be an object')
  assert.ok(typeof config.browser === 'object', 'browser config should be an object')
  assert.ok(typeof config.extraction === 'object', 'extraction config should be an object')
  
  // Verify default values
  assert.deepStrictEqual(config.searchKeywords, SEARCH_KEYWORDS, 'Should use default search keywords')
  assert.strictEqual(config.targetSites.PR_TIMES, TARGET_SITES.PR_TIMES, 'Should use default PR_TIMES URL')
  assert.strictEqual(config.browser.userAgent, BROWSER_CONFIG.userAgent, 'Should use default user agent')
  assert.strictEqual(config.browser.timeout, BROWSER_CONFIG.timeout, 'Should use default timeout')
  assert.strictEqual(config.browser.waitTime, BROWSER_CONFIG.waitTime, 'Should use default wait time')
  assert.deepStrictEqual(config.browser.launchArgs, BROWSER_CONFIG.launchArgs, 'Should use default launch args')
  assert.strictEqual(config.extraction.maxTitleLength, EXTRACTION_CONFIG.maxTitleLength, 'Should use default max title length')
  assert.deepStrictEqual(config.extraction.companyPatterns, EXTRACTION_CONFIG.companyPatterns, 'Should use default company patterns')
  
  console.log('✅ getConfig() returns correct default configuration')
})

test('getConfig() respects environment variable overrides', async () => {
  // Set test environment variables
  process.env.SCRAPER_KEYWORDS = 'テスト1,テスト2,テスト3'
  process.env.SCRAPER_TIMEOUT = '45000'
  process.env.SCRAPER_WAIT_TIME = '5000'
  process.env.SCRAPER_MAX_TITLE_LENGTH = '150'
  process.env.SCRAPER_USER_AGENT = 'Test User Agent'
  process.env.SCRAPER_PRTIMES_URL = 'https://test.example.com/search?q='
  
  const config = getConfig()
  
  // Verify environment variable overrides
  assert.deepStrictEqual(config.searchKeywords, ['テスト1', 'テスト2', 'テスト3'], 'Should parse keywords from environment')
  assert.strictEqual(config.browser.timeout, 45000, 'Should use environment timeout')
  assert.strictEqual(config.browser.waitTime, 5000, 'Should use environment wait time')
  assert.strictEqual(config.extraction.maxTitleLength, 150, 'Should use environment max title length')
  assert.strictEqual(config.browser.userAgent, 'Test User Agent', 'Should use environment user agent')
  assert.strictEqual(config.targetSites.PR_TIMES, 'https://test.example.com/search?q=', 'Should use environment PR_TIMES URL')
  
  // Verify unchanged defaults
  assert.deepStrictEqual(config.browser.launchArgs, BROWSER_CONFIG.launchArgs, 'Should keep default launch args')
  assert.deepStrictEqual(config.extraction.companyPatterns, EXTRACTION_CONFIG.companyPatterns, 'Should keep default company patterns')
  
  console.log('✅ getConfig() correctly applies environment variable overrides')
  
  // Clean up
  restoreEnv()
})

test('getConfig() handles malformed environment variables gracefully', async () => {
  // Set malformed environment variables
  process.env.SCRAPER_KEYWORDS = '' // Empty string
  process.env.SCRAPER_TIMEOUT = 'not-a-number' // Invalid number
  process.env.SCRAPER_WAIT_TIME = '-1000' // Negative number (but valid integer)
  process.env.SCRAPER_MAX_TITLE_LENGTH = 'invalid'
  
  const config = getConfig()
  
  // Should fall back to defaults for invalid values
  assert.deepStrictEqual(config.searchKeywords, SEARCH_KEYWORDS, 'Should fall back to default keywords for empty string')
  assert.strictEqual(config.browser.timeout, BROWSER_CONFIG.timeout, 'Should fall back to default timeout for invalid number')
  assert.strictEqual(config.browser.waitTime, -1000, 'Should accept negative wait time (valid integer)')
  assert.strictEqual(config.extraction.maxTitleLength, EXTRACTION_CONFIG.maxTitleLength, 'Should fall back to default max title length for invalid value')
  
  console.log('✅ getConfig() handles malformed environment variables gracefully')
  
  // Clean up
  restoreEnv()
})

test('getConfig() properly parses comma-separated keywords', async () => {
  // Test various keyword formats
  const testCases = [
    {
      input: 'keyword1,keyword2,keyword3',
      expected: ['keyword1', 'keyword2', 'keyword3']
    },
    {
      input: ' keyword1 , keyword2 , keyword3 ', // With spaces
      expected: ['keyword1', 'keyword2', 'keyword3']
    },
    {
      input: 'keyword1,,keyword2,', // With empty segments
      expected: ['keyword1', 'keyword2']
    },
    {
      input: 'single-keyword',
      expected: ['single-keyword']
    }
  ]
  
  for (const testCase of testCases) {
    process.env.SCRAPER_KEYWORDS = testCase.input
    const config = getConfig()
    
    assert.deepStrictEqual(
      config.searchKeywords, 
      testCase.expected, 
      `Failed for input: "${testCase.input}"`
    )
  }
  
  console.log('✅ getConfig() correctly parses comma-separated keywords')
  
  // Clean up
  restoreEnv()
})

test('Configuration maintains type safety', async () => {
  const config = getConfig()
  
  // Verify all types match expected ScraperConfig interface
  assert.ok(Array.isArray(config.searchKeywords) && config.searchKeywords.every(k => typeof k === 'string'), 'searchKeywords should be string array')
  assert.ok(typeof config.targetSites === 'object' && typeof config.targetSites.PR_TIMES === 'string', 'targetSites should have proper structure')
  assert.ok(typeof config.browser === 'object', 'browser should be an object')
  assert.ok(typeof config.browser.userAgent === 'string', 'userAgent should be string')
  assert.ok(typeof config.browser.timeout === 'number', 'timeout should be number')
  assert.ok(typeof config.browser.waitTime === 'number', 'waitTime should be number')
  assert.ok(Array.isArray(config.browser.launchArgs) && config.browser.launchArgs.every(a => typeof a === 'string'), 'launchArgs should be string array')
  assert.ok(typeof config.extraction === 'object', 'extraction should be an object')
  assert.ok(typeof config.extraction.maxTitleLength === 'number', 'maxTitleLength should be number')
  assert.ok(Array.isArray(config.extraction.companyPatterns) && config.extraction.companyPatterns.every(p => p instanceof RegExp), 'companyPatterns should be RegExp array')
  
  console.log('✅ Configuration maintains proper type safety')
})

// Test Summary
console.log('\n📋 Variables Configuration Test Summary:')
console.log('🎯 Test purpose: Verify configuration loading and environment variable support')
console.log('📊 Coverage: Default values, environment overrides, error handling, type safety')
console.log('✅ All configuration functionality should work correctly')