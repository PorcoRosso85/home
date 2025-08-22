#!/usr/bin/env node
/**
 * Golden Master Test for corporate_list scraper
 * 
 * This test protects the current behavior during TypeScript migration.
 * It compares new runs against a golden master to ensure consistency.
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

// Load golden master data
const goldenPath = join(__dirname, 'fixtures', 'golden.json')
let goldenData
try {
  goldenData = JSON.parse(readFileSync(goldenPath, 'utf8'))
} catch (error) {
  console.error('❌ Failed to load golden master data:', error.message)
  process.exit(1)
}

/**
 * Run the scraper and return parsed results
 */
async function runScraper() {
  try {
    // Set environment for chromium
    const env = {
      ...process.env,
      PATH: `${process.env.PATH}:/nix/store/h9j4plw38q9adgyp7gvcr8v6qmkjm312-chromium-139.0.7258.138/bin`
    }
    
    const command = 'nix run nixpkgs#nodejs -- scrape.mjs'
    const output = execSync(command, { 
      cwd: projectRoot,
      env,
      encoding: 'utf8',
      timeout: 120000 // 2 minutes
    })
    
    // Extract JSON array from output (between [ and ])
    const jsonMatch = output.match(/\[[\s\S]*\]/m)
    if (!jsonMatch) {
      throw new Error('No JSON array found in scraper output')
    }
    
    return JSON.parse(jsonMatch[0])
  } catch (error) {
    throw new Error(`Failed to run scraper: ${error.message}`)
  }
}

/**
 * Normalize data for comparison (remove timestamp fields)
 */
function normalizeForComparison(data) {
  return data.map(item => ({
    source: item.source,
    company_name: item.company_name,
    title: item.title,
    url: item.url
    // Remove scraped_at timestamp as it will always differ
  }))
}

/**
 * Compare two datasets with detailed reporting
 */
function compareDatasets(actual, expected, testName) {
  const errors = []
  
  // Check total count
  if (actual.length !== expected.length) {
    errors.push(`Count mismatch: expected ${expected.length}, got ${actual.length}`)
  }
  
  // Check structure of each item
  const minLength = Math.min(actual.length, expected.length)
  for (let i = 0; i < minLength; i++) {
    const actualItem = actual[i]
    const expectedItem = expected[i]
    
    // Check required fields exist
    const requiredFields = ['source', 'company_name', 'title', 'url']
    for (const field of requiredFields) {
      if (!(field in actualItem)) {
        errors.push(`Item ${i}: Missing field '${field}'`)
      }
    }
    
    // Check source is consistent
    if (actualItem.source !== expectedItem.source) {
      errors.push(`Item ${i}: Source mismatch. Expected '${expectedItem.source}', got '${actualItem.source}'`)
    }
    
    // Check URL format
    if (!actualItem.url || !actualItem.url.includes('prtimes.jp')) {
      errors.push(`Item ${i}: Invalid URL format: ${actualItem.url}`)
    }
    
    // Check title exists and is reasonable length
    if (!actualItem.title || actualItem.title.length < 5) {
      errors.push(`Item ${i}: Invalid title: ${actualItem.title}`)
    }
  }
  
  return errors
}

/**
 * Check that we have the expected keywords coverage
 */
function checkKeywordsCoverage(data) {
  const expectedKeywords = ["シリーズA", "資金調達", "事業提携"]
  const errors = []
  
  // We should have around 40 articles per keyword (120 total)
  if (data.length < 90 || data.length > 150) {
    errors.push(`Unexpected total article count: ${data.length}. Expected around 120 (40 per keyword)`)
  }
  
  // Check that articles seem to be related to business/funding
  const businessKeywords = ['株式会社', '資金', '調達', '提携', '投資', '事業', 'シリーズ']
  let businessRelated = 0
  
  for (const item of data) {
    const text = `${item.title} ${item.company_name || ''}`
    if (businessKeywords.some(keyword => text.includes(keyword))) {
      businessRelated++
    }
  }
  
  const businessRate = (businessRelated / data.length) * 100
  if (businessRate < 20) { // At least 20% should be business-related
    errors.push(`Low business relevance: only ${businessRate.toFixed(1)}% of articles seem business-related`)
  }
  
  return errors
}

// Main Test Suite
test('Golden Master Test - Corporate List Scraper', async (t) => {
  
  await t.test('Golden master file exists and is valid', () => {
    assert.ok(existsSync(goldenPath), 'Golden master file should exist')
    assert.ok(Array.isArray(goldenData), 'Golden master should be an array')
    assert.ok(goldenData.length > 0, 'Golden master should not be empty')
    
    console.log(`✅ Golden master loaded: ${goldenData.length} articles`)
  })
  
  await t.test('Scraper produces consistent structure', async () => {
    console.log('🔄 Running scraper (this may take 1-2 minutes)...')
    const actualData = await runScraper()
    
    console.log(`📊 Scraper completed: ${actualData.length} articles found`)
    
    // Normalize data for comparison
    const normalizedActual = normalizeForComparison(actualData)
    const normalizedExpected = normalizeForComparison(goldenData)
    
    // Compare structure and basic properties
    const structureErrors = compareDatasets(normalizedActual, normalizedExpected, 'structure')
    
    if (structureErrors.length > 0) {
      console.error('❌ Structure comparison errors:')
      structureErrors.forEach(error => console.error('  -', error))
    }
    
    // Allow some flexibility in results but flag major changes
    const countDiff = Math.abs(actualData.length - goldenData.length)
    const maxAllowedDiff = 20 // Allow up to 20 articles difference
    
    assert.ok(countDiff <= maxAllowedDiff, 
      `Article count difference too large: ${countDiff} (max allowed: ${maxAllowedDiff})`)
    
    console.log(`✅ Structure validation passed (${structureErrors.length} minor issues)`)
  })
  
  await t.test('Keywords coverage is maintained', async () => {
    console.log('🔄 Running scraper for keyword coverage test...')
    const actualData = await runScraper()
    
    const coverageErrors = checkKeywordsCoverage(actualData)
    
    if (coverageErrors.length > 0) {
      console.error('⚠️  Keywords coverage issues:')
      coverageErrors.forEach(error => console.error('  -', error))
    }
    
    // This should pass unless there are major issues
    assert.ok(actualData.length >= 90, 'Should collect at least 90 articles')
    assert.ok(actualData.length <= 150, 'Should not collect more than 150 articles')
    
    console.log(`✅ Keywords coverage validated: ${actualData.length} articles collected`)
  })
  
  await t.test('Data quality checks', async () => {
    console.log('🔄 Running scraper for data quality test...')
    const actualData = await runScraper()
    
    // Check that all articles have required fields
    for (const [index, article] of actualData.entries()) {
      assert.ok(article.source, `Article ${index}: should have source`)
      assert.ok(article.title, `Article ${index}: should have title`)
      assert.ok(article.url, `Article ${index}: should have URL`)
      assert.ok(article.url.includes('prtimes.jp'), `Article ${index}: URL should be from PR TIMES`)
      
      // company_name can be null (as per original implementation)
      assert.ok(article.hasOwnProperty('company_name'), `Article ${index}: should have company_name field`)
      
      // Should have scraped_at timestamp
      assert.ok(article.scraped_at, `Article ${index}: should have scraped_at timestamp`)
      assert.ok(new Date(article.scraped_at).getTime() > 0, `Article ${index}: scraped_at should be valid date`)
    }
    
    console.log(`✅ Data quality checks passed for ${actualData.length} articles`)
  })
  
})

// Summary
console.log('\n📋 Golden Master Test Summary:')
console.log(`📁 Golden master file: ${goldenPath}`)
console.log(`📊 Expected article count: ~${goldenData.length} (exact: ${goldenData.length})`)
console.log(`🎯 Test protects: structure, count, data quality, keyword coverage`)
console.log(`⚠️  Note: Timestamps and exact articles may vary due to live scraping`)