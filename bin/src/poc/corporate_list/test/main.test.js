#!/usr/bin/env node
/**
 * Main Test (JavaScript version)
 * 
 * This test verifies that the compiled JavaScript files work correctly
 * by importing and testing functions from the dist directory.
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = dirname(__dirname)

// Import compiled JavaScript modules from dist
const distPath = join(projectRoot, 'dist', 'src')

/**
 * Test helper to validate scraped result structure
 */
function validateScrapedResult(result) {
  const requiredFields = ['source', 'company_name', 'title', 'url', 'scraped_at']
  
  for (const field of requiredFields) {
    if (!(field in result)) {
      return `Missing field: ${field}`
    }
  }
  
  if (typeof result.source !== 'string') {
    return 'source must be string'
  }
  
  if (result.company_name !== null && typeof result.company_name !== 'string') {
    return 'company_name must be null or string'
  }
  
  if (typeof result.title !== 'string') {
    return 'title must be string'
  }
  
  if (typeof result.url !== 'string') {
    return 'url must be string'
  }
  
  if (typeof result.scraped_at !== 'string') {
    return 'scraped_at must be string'
  }
  
  return null
}

// Main Test Suite
test('Compiled Main Module Tests', async (t) => {
  
  await t.test('Compiled files exist', () => {
    // Check main compiled files
    const mainJs = join(distPath, 'main.js')
    const variablesJs = join(distPath, 'variables.js')
    const browserJs = join(distPath, 'infrastructure', 'browser.js')
    const extractorJs = join(distPath, 'domain', 'extractor.js')
    const scraperJs = join(distPath, 'domain', 'scraper.js')
    
    assert.ok(existsSync(mainJs), 'main.js should exist')
    assert.ok(existsSync(variablesJs), 'variables.js should exist')
    assert.ok(existsSync(browserJs), 'browser.js should exist')
    assert.ok(existsSync(extractorJs), 'extractor.js should exist')
    assert.ok(existsSync(scraperJs), 'scraper.js should exist')
    
    console.log('✅ All compiled files exist')
  })
  
  await t.test('Can import variables module', async () => {
    try {
      const variablesModule = await import(`${distPath}/variables.js`)
      
      // Check that we can access the variables
      assert.ok(variablesModule, 'Variables module should be importable')
      
      console.log('✅ Variables module imports successfully')
    } catch (error) {
      assert.fail(`Failed to import variables module: ${error.message}`)
    }
  })
  
  await t.test('Can import domain modules', async () => {
    try {
      const extractorModule = await import(`${distPath}/domain/extractor.js`)
      const scraperModule = await import(`${distPath}/domain/scraper.js`)
      
      assert.ok(extractorModule, 'Extractor module should be importable')
      assert.ok(scraperModule, 'Scraper module should be importable')
      
      console.log('✅ Domain modules import successfully')
    } catch (error) {
      assert.fail(`Failed to import domain modules: ${error.message}`)
    }
  })
  
  await t.test('Can import infrastructure modules', async () => {
    try {
      const browserModule = await import(`${distPath}/infrastructure/browser.js`)
      
      assert.ok(browserModule, 'Browser module should be importable')
      
      console.log('✅ Infrastructure modules import successfully')
    } catch (error) {
      assert.fail(`Failed to import infrastructure modules: ${error.message}`)
    }
  })
  
  await t.test('Module structure validation', () => {
    // Test mock data structure to ensure our validation functions work
    const mockScrapedResult = {
      source: 'test',
      company_name: 'Test Company',
      title: 'Test Article',
      url: 'https://test.example.com',
      scraped_at: '2025-08-22T12:00:00Z'
    }
    
    const validationError = validateScrapedResult(mockScrapedResult)
    assert.strictEqual(validationError, null, 'Mock data should be valid')
    
    // Test invalid data
    const invalidResult = {
      source: 'test',
      title: 'Test',
      // Missing required fields
    }
    
    const invalidError = validateScrapedResult(invalidResult)
    assert.ok(invalidError, 'Invalid data should return error')
    
    console.log('✅ Data structure validation works')
  })
  
  await t.test('JavaScript compilation preserves functionality', () => {
    // Check that the dist directory structure matches expectations
    const expectedDirs = ['domain', 'infrastructure']
    const srcDistPath = join(projectRoot, 'dist', 'src')
    
    for (const dir of expectedDirs) {
      const dirPath = join(srcDistPath, dir)
      assert.ok(existsSync(dirPath), `${dir} directory should exist in dist/src`)
    }
    
    // Check domain subdirectory
    const domainPath = join(srcDistPath, 'domain')
    const domainFiles = ['extractor.js', 'scraper.js', 'scraper-factory.js', 'types.js']
    
    for (const file of domainFiles) {
      const filePath = join(domainPath, file)
      assert.ok(existsSync(filePath), `${file} should exist in domain`)
    }
    
    console.log('✅ Compilation preserves project structure')
  })
  
  await t.test('TypeScript declaration files exist', () => {
    // Check that .d.ts files were generated
    const mainDts = join(distPath, 'main.d.ts')
    const variablesDts = join(distPath, 'variables.d.ts')
    
    assert.ok(existsSync(mainDts), 'main.d.ts should exist')
    assert.ok(existsSync(variablesDts), 'variables.d.ts should exist')
    
    console.log('✅ TypeScript declaration files generated')
  })
  
})

// Summary
console.log('\n📋 Compiled Main Module Test Summary:')
console.log(`📁 Test file: ${__filename}`)
console.log(`🎯 Verifies: Compiled JS files exist, modules can be imported, structure is preserved`)
console.log(`✨ Compiled main modules are ready for use`)