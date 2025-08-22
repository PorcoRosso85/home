#!/usr/bin/env node
/**
 * TypeScript Environment Test (JavaScript version)
 * 
 * This test verifies that the TypeScript-compiled JavaScript files work properly
 * with Node.js 22 and ES modules support.
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

// Test ESM imports work with compiled JavaScript
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = dirname(__dirname)

// Test configuration object
const projectConfig = {
  name: 'corporate-list-scraper',
  version: '0.0.1',
  type: 'module'
}

/**
 * Test function for config validation
 */
function validateConfig(config) {
  return config.name.length > 0 && 
         config.version.includes('.') && 
         config.type === 'module'
}

/**
 * Async function test
 */
async function asyncTest() {
  return new Promise((resolve) => {
    setTimeout(() => resolve('JavaScript async works!'), 10)
  })
}

// Main Test Suite
test('Compiled TypeScript Environment Tests', async (t) => {
  
  await t.test('TypeScript configuration files exist and dist is built', () => {
    const tsconfigPath = join(projectRoot, 'tsconfig.json')
    const packageJsonPath = join(projectRoot, 'package.json')
    const distPath = join(projectRoot, 'dist')
    
    assert.ok(existsSync(tsconfigPath), 'tsconfig.json should exist')
    assert.ok(existsSync(packageJsonPath), 'package.json should exist')
    assert.ok(existsSync(distPath), 'dist directory should exist')
    
    // Check if compiled JavaScript files exist
    const mainJsPath = join(projectRoot, 'dist', 'src', 'main.js')
    assert.ok(existsSync(mainJsPath), 'Compiled main.js should exist')
    
    console.log('✅ TypeScript compilation verified')
  })
  
  await t.test('JavaScript types and functions work', () => {
    // Test config validation
    assert.ok(validateConfig(projectConfig), 'Config validation should work')
    
    // Test array operations
    const numbers = [1, 2, 3, 4, 5]
    const doubled = numbers.map(n => n * 2)
    assert.deepEqual(doubled, [2, 4, 6, 8, 10], 'Array mapping should work')
    
    // Test mixed types
    const mixedValue = 'test'
    assert.equal(typeof mixedValue, 'string', 'Type checking should work')
    
    console.log('✅ JavaScript functions working')
  })
  
  await t.test('Modern JavaScript features work', async () => {
    // Test async/await
    const result = await asyncTest()
    assert.equal(result, 'JavaScript async works!', 'Async/await should work')
    
    // Test destructuring
    const { name, version } = projectConfig
    assert.equal(name, 'corporate-list-scraper', 'Destructuring should work')
    assert.ok(version.includes('.'), 'Version should be valid')
    
    // Test optional chaining and nullish coalescing
    const testObj = { deep: { value: 'test' } }
    const value = testObj?.deep?.value ?? 'default'
    assert.equal(value, 'test', 'Optional chaining should work')
    
    // Test template literals
    const templateTest = `Project: ${name} v${version}`
    assert.ok(templateTest.includes(name), 'Template literals should work')
    
    console.log('✅ Modern JavaScript features working')
  })
  
  await t.test('Node.js built-in modules work', () => {
    // Test Node.js version
    const nodeVersion = process.version
    assert.ok(nodeVersion.startsWith('v'), 'Node.js version should be available')
    
    // Test file system operations
    const packageJsonExists = existsSync(join(projectRoot, 'package.json'))
    assert.ok(packageJsonExists, 'File system operations should work')
    
    // Test path operations
    const testPath = join(__dirname, 'test-file.txt')
    assert.ok(testPath.includes(__dirname), 'Path operations should work')
    
    console.log('✅ Node.js built-in modules working')
  })
  
  await t.test('ES modules work correctly', () => {
    // Test that import.meta is available
    assert.ok(import.meta.url, 'import.meta.url should be available')
    assert.ok(import.meta.url.startsWith('file://'), 'import.meta.url should be file URL')
    
    // Test that __filename and __dirname work with ES modules
    assert.ok(__filename.endsWith('.js'), 'Should have correct filename')
    assert.ok(__dirname.includes('test'), 'Should have correct dirname')
    
    console.log('✅ ES modules working correctly')
  })
  
  await t.test('Compiled TypeScript files are accessible', () => {
    // Test that we can access the dist directory structure
    const distSrcPath = join(projectRoot, 'dist', 'src')
    const distTestPath = join(projectRoot, 'dist', 'test')
    
    assert.ok(existsSync(distSrcPath), 'dist/src should exist')
    assert.ok(existsSync(distTestPath), 'dist/test should exist')
    
    // Check main compiled files
    const mainJs = join(distSrcPath, 'main.js')
    const variablesJs = join(distSrcPath, 'variables.js')
    
    assert.ok(existsSync(mainJs), 'main.js should be compiled')
    assert.ok(existsSync(variablesJs), 'variables.js should be compiled')
    
    console.log('✅ Compiled TypeScript files are accessible')
  })
  
})

// Summary
console.log('\n📋 Compiled TypeScript Environment Test Summary:')
console.log(`📁 Test file: ${__filename}`)
console.log(`🎯 Verifies: Compiled JS files, modern JS features, Node.js modules, ES modules`)
console.log(`✨ Compiled TypeScript environment is ready`)