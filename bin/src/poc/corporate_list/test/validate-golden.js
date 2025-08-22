#!/usr/bin/env node
/**
 * Validate the golden master test setup without running the scraper
 */

import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Check golden master file
const goldenPath = join(__dirname, 'fixtures', 'golden.json')

console.log('🔍 Validating Golden Master Test Setup...')
console.log('=' .repeat(50))

// Test 1: File exists
if (!existsSync(goldenPath)) {
  console.error('❌ Golden master file not found:', goldenPath)
  process.exit(1)
}
console.log('✅ Golden master file exists')

// Test 2: File is valid JSON
let goldenData
try {
  const content = readFileSync(goldenPath, 'utf8')
  goldenData = JSON.parse(content)
} catch (error) {
  console.error('❌ Golden master file is not valid JSON:', error.message)
  process.exit(1)
}
console.log('✅ Golden master file is valid JSON')

// Test 3: Data structure validation
if (!Array.isArray(goldenData)) {
  console.error('❌ Golden master data should be an array')
  process.exit(1)
}
console.log('✅ Golden master data is an array')

if (goldenData.length === 0) {
  console.error('❌ Golden master data is empty')
  process.exit(1)
}
console.log(`✅ Golden master contains ${goldenData.length} articles`)

// Test 4: Sample data structure
const sample = goldenData[0]
const requiredFields = ['source', 'company_name', 'title', 'url', 'scraped_at']

for (const field of requiredFields) {
  if (!(field in sample)) {
    console.error(`❌ Missing required field '${field}' in sample data`)
    process.exit(1)
  }
}
console.log('✅ Sample data has all required fields')

// Test 5: Expected count (should be around 120)
if (goldenData.length < 100 || goldenData.length > 150) {
  console.warn(`⚠️  Unexpected article count: ${goldenData.length} (expected ~120)`)
} else {
  console.log(`✅ Article count is in expected range: ${goldenData.length}`)
}

// Test 6: Check source consistency
const sources = new Set(goldenData.map(item => item.source))
console.log(`✅ Data sources: ${Array.from(sources).join(', ')}`)

// Test 7: Check URL patterns
const urlPatterns = goldenData.slice(0, 5).map(item => item.url)
const validUrls = urlPatterns.every(url => url && url.includes('prtimes.jp'))
if (!validUrls) {
  console.error('❌ Some URLs do not match expected pattern')
  process.exit(1)
}
console.log('✅ URL patterns are consistent')

console.log('\n' + '=' .repeat(50))
console.log('🎉 Golden Master Test Setup Validation PASSED!')
console.log(`📊 Ready to protect ${goldenData.length} articles during TypeScript migration`)

// Show summary statistics
const withCompany = goldenData.filter(item => item.company_name).length
const companyRate = Math.round((withCompany / goldenData.length) * 100)

console.log('\n📈 Golden Master Statistics:')
console.log(`  Total articles: ${goldenData.length}`)
console.log(`  Articles with company names: ${withCompany} (${companyRate}%)`)
console.log(`  Data captured: ${new Date(goldenData[0].scraped_at).toLocaleString()}`)
console.log(`  Sample title: "${goldenData[0].title.substring(0, 50)}..."`)

console.log('\n🛡️  Test Protection Coverage:')
console.log('  ✅ Article count consistency (±20 articles tolerance)')
console.log('  ✅ Data structure validation')
console.log('  ✅ URL format validation') 
console.log('  ✅ Required field presence')
console.log('  ✅ Keywords coverage validation')
console.log('  ✅ Data quality checks')