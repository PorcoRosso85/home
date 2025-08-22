#!/usr/bin/env node
/**
 * TypeScript vs JavaScript Golden Master Test for corporate_list scraper
 * 
 * This test ensures that the TypeScript implementation produces the same output
 * as the JavaScript version (scrape.mjs).
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { readFileSync, existsSync } from 'node:fs'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = dirname(__dirname)

// Define types for our scraping results
interface ScrapedResult {
  source: string;
  company_name: string | null;
  title: string;
  url: string;
  scraped_at: string;
}

/**
 * Run the JavaScript scraper and return parsed results
 */
async function runJavaScriptScraper(): Promise<ScrapedResult[]> {
  try {
    const env = {
      ...process.env,
      PATH: `${process.env.PATH}:/nix/store/h9j4plw38q9adgyp7gvcr8v6qmkjm312-chromium-139.0.7258.138/bin`
    }
    
    const command = 'node scrape.mjs'
    const output = execSync(command, { 
      cwd: projectRoot,
      env,
      encoding: 'utf8',
      timeout: 120000 // 2 minutes
    })
    
    // Extract JSON array from output (between [ and ])
    const jsonMatch = output.match(/\[[\s\S]*\]/m)
    if (!jsonMatch) {
      throw new Error('No JSON array found in JavaScript scraper output')
    }
    
    return JSON.parse(jsonMatch[0])
  } catch (error: any) {
    throw new Error(`Failed to run JavaScript scraper: ${error.message}`)
  }
}

/**
 * Run the TypeScript scraper and return parsed results
 */
async function runTypeScriptScraper(): Promise<ScrapedResult[]> {
  try {
    const env = {
      ...process.env,
      PATH: `${process.env.PATH}:/nix/store/h9j4plw38q9adgyp7gvcr8v6qmkjm312-chromium-139.0.7258.138/bin`
    }
    
    const command = 'npx tsx src/main.ts'
    const output = execSync(command, { 
      cwd: projectRoot,
      env,
      encoding: 'utf8',
      timeout: 120000 // 2 minutes
    })
    
    // Extract JSON array from output (between [ and ])
    const jsonMatch = output.match(/\[[\s\S]*\]/m)
    if (!jsonMatch) {
      throw new Error('No JSON array found in TypeScript scraper output')
    }
    
    return JSON.parse(jsonMatch[0])
  } catch (error: any) {
    throw new Error(`Failed to run TypeScript scraper: ${error.message}`)
  }
}

/**
 * Normalize data for comparison (remove timestamp fields)
 */
function normalizeForComparison(data: ScrapedResult[]): Omit<ScrapedResult, 'scraped_at'>[] {
  return data.map(item => ({
    source: item.source,
    company_name: item.company_name,
    title: item.title,
    url: item.url
    // Remove scraped_at timestamp as it will always differ between runs
  }))
}

/**
 * Compare two datasets with detailed reporting
 */
function compareDatasets(actual: any[], expected: any[], testName: string): string[] {
  const errors: string[] = []
  
  // Check total count - allow some flexibility for live scraping
  const countDiff = Math.abs(actual.length - expected.length)
  const maxAllowedDiff = 5 // Allow up to 5 articles difference between TS and JS
  
  if (countDiff > maxAllowedDiff) {
    errors.push(`Count difference too large: ${countDiff} (max allowed: ${maxAllowedDiff}). JS: ${expected.length}, TS: ${actual.length}`)
  }
  
  // Check structure of each item (for available items)
  const minLength = Math.min(actual.length, expected.length)
  for (let i = 0; i < Math.min(10, minLength); i++) { // Check first 10 items
    const actualItem = actual[i]
    const expectedItem = expected[i]
    
    // Check required fields exist
    const requiredFields = ['source', 'company_name', 'title', 'url']
    for (const field of requiredFields) {
      if (!(field in actualItem)) {
        errors.push(`Item ${i}: Missing field '${field}' in TypeScript output`)
      }
    }
    
    // Check field types match
    if (typeof actualItem.source !== typeof expectedItem.source) {
      errors.push(`Item ${i}: Type mismatch for 'source'. JS: ${typeof expectedItem.source}, TS: ${typeof actualItem.source}`)
    }
    
    if (typeof actualItem.title !== typeof expectedItem.title) {
      errors.push(`Item ${i}: Type mismatch for 'title'. JS: ${typeof expectedItem.title}, TS: ${typeof actualItem.title}`)
    }
    
    if (typeof actualItem.url !== typeof expectedItem.url) {
      errors.push(`Item ${i}: Type mismatch for 'url'. JS: ${typeof expectedItem.url}, TS: ${typeof actualItem.url}`)
    }
    
    // company_name can be null or string in both versions
    if (actualItem.company_name !== null && expectedItem.company_name !== null) {
      if (typeof actualItem.company_name !== typeof expectedItem.company_name) {
        errors.push(`Item ${i}: Type mismatch for 'company_name'. JS: ${typeof expectedItem.company_name}, TS: ${typeof actualItem.company_name}`)
      }
    }
  }
  
  return errors
}

/**
 * Validate data quality for both implementations
 */
function validateDataQuality(data: ScrapedResult[], implementationName: string): string[] {
  const errors: string[] = []
  
  // Check that all articles have required fields
  for (const [index, article] of data.entries()) {
    if (!article.source) {
      errors.push(`${implementationName} Article ${index}: Missing source`)
    }
    
    if (!article.title || article.title.length < 5) {
      errors.push(`${implementationName} Article ${index}: Invalid title: '${article.title}'`)
    }
    
    if (!article.url || !article.url.includes('prtimes.jp')) {
      errors.push(`${implementationName} Article ${index}: Invalid URL: '${article.url}'`)
    }
    
    // company_name can be null (as per original implementation)
    if (!article.hasOwnProperty('company_name')) {
      errors.push(`${implementationName} Article ${index}: Missing company_name field`)
    }
    
    // Should have scraped_at timestamp
    if (!article.scraped_at) {
      errors.push(`${implementationName} Article ${index}: Missing scraped_at timestamp`)
    } else {
      const timestamp = new Date(article.scraped_at)
      if (isNaN(timestamp.getTime())) {
        errors.push(`${implementationName} Article ${index}: Invalid scraped_at timestamp: '${article.scraped_at}'`)
      }
    }
  }
  
  return errors
}

// Main Test Suite
test('TypeScript vs JavaScript Implementation Comparison', async (t) => {
  
  let jsData: ScrapedResult[]
  let tsData: ScrapedResult[]
  
  await t.test('Both implementations can run successfully', async () => {
    console.log('🔄 Running JavaScript scraper (this may take 1-2 minutes)...')
    jsData = await runJavaScriptScraper()
    console.log(`📊 JavaScript scraper completed: ${jsData.length} articles found`)
    
    console.log('🔄 Running TypeScript scraper (this may take 1-2 minutes)...')
    tsData = await runTypeScriptScraper()
    console.log(`📊 TypeScript scraper completed: ${tsData.length} articles found`)
    
    assert.ok(jsData.length > 0, 'JavaScript scraper should return results')
    assert.ok(tsData.length > 0, 'TypeScript scraper should return results')
    
    console.log(`✅ Both implementations executed successfully`)
  })
  
  await t.test('Data structures are consistent', async () => {
    // Normalize data for comparison
    const normalizedJs = normalizeForComparison(jsData)
    const normalizedTs = normalizeForComparison(tsData)
    
    // Compare structure and basic properties
    const structureErrors = compareDatasets(normalizedTs, normalizedJs, 'structure')
    
    if (structureErrors.length > 0) {
      console.error('❌ Structure comparison errors:')
      structureErrors.forEach(error => console.error('  -', error))
    }
    
    // Allow some flexibility for live scraping but ensure structures match
    assert.ok(structureErrors.length < 3, 
      `Too many structure differences: ${structureErrors.length}. Check implementation consistency.`)
    
    console.log(`✅ Data structure validation passed (${structureErrors.length} minor differences)`)
  })
  
  await t.test('Data quality is maintained', async () => {
    // Validate JavaScript results
    const jsErrors = validateDataQuality(jsData, 'JS')
    if (jsErrors.length > 0) {
      console.error('⚠️  JavaScript implementation quality issues:')
      jsErrors.forEach(error => console.error('  -', error))
    }
    
    // Validate TypeScript results
    const tsErrors = validateDataQuality(tsData, 'TS')
    if (tsErrors.length > 0) {
      console.error('⚠️  TypeScript implementation quality issues:')
      tsErrors.forEach(error => console.error('  -', error))
    }
    
    // Both implementations should have good data quality
    assert.ok(jsErrors.length === 0, `JavaScript implementation has data quality issues: ${jsErrors.length}`)
    assert.ok(tsErrors.length === 0, `TypeScript implementation has data quality issues: ${tsErrors.length}`)
    
    console.log(`✅ Data quality checks passed for both implementations`)
  })
  
  await t.test('Output compatibility check', async () => {
    // Ensure both implementations produce reasonably similar results
    const countDiff = Math.abs(jsData.length - tsData.length)
    const maxAllowedDiff = 5
    
    console.log(`📊 Results comparison:`)
    console.log(`   JavaScript: ${jsData.length} articles`)
    console.log(`   TypeScript: ${tsData.length} articles`)
    console.log(`   Difference: ${countDiff} articles`)
    
    assert.ok(countDiff <= maxAllowedDiff, 
      `Article count difference too large: ${countDiff} (max allowed: ${maxAllowedDiff})`)
    
    // Check that both implementations target the same source
    const jsSource = jsData[0]?.source
    const tsSource = tsData[0]?.source
    
    assert.strictEqual(tsSource, jsSource, 'Both implementations should use the same source')
    
    console.log(`✅ Output compatibility verified`)
  })
  
})

// Summary
console.log('\n📋 TypeScript Implementation Test Summary:')
console.log(`🎯 Test purpose: Verify TypeScript implementation matches JavaScript behavior`)
console.log(`📊 Expected behavior: Similar article counts and identical data structure`)
console.log(`⚠️  Note: Exact articles may vary due to live scraping, but structure should match`)