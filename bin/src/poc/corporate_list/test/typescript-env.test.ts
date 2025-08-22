#!/usr/bin/env node
/**
 * TypeScript Environment Test
 * 
 * This test verifies that the TypeScript environment is properly configured
 * for Node.js 22 with ES modules support.
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

// Test ESM imports work with TypeScript
const __filename: string = fileURLToPath(import.meta.url)
const __dirname: string = dirname(__filename)
const projectRoot: string = dirname(__dirname)

// Test interface definition
interface TestConfig {
  name: string
  version: string
  type: string
}

// Test type annotations and modern JS features
const projectConfig: TestConfig = {
  name: 'corporate-list-scraper',
  version: '0.0.1',
  type: 'module'
}

/**
 * Test function with proper TypeScript types
 */
function validateConfig(config: TestConfig): boolean {
  return config.name.length > 0 && 
         config.version.includes('.') && 
         config.type === 'module'
}

/**
 * Async function test with proper typing
 */
async function asyncTest(): Promise<string> {
  return new Promise((resolve) => {
    setTimeout(() => resolve('TypeScript async works!'), 10)
  })
}

// Main Test Suite
test('TypeScript Environment Tests', async (t) => {
  
  await t.test('TypeScript configuration files exist', () => {
    const tsconfigPath = join(projectRoot, 'tsconfig.json')
    const packageJsonPath = join(projectRoot, 'package.json')
    
    assert.ok(existsSync(tsconfigPath), 'tsconfig.json should exist')
    assert.ok(existsSync(packageJsonPath), 'package.json should exist')
    
    // Check tsconfig.json structure
    const tsconfig = JSON.parse(readFileSync(tsconfigPath, 'utf8'))
    assert.ok(tsconfig.compilerOptions, 'tsconfig should have compilerOptions')
    assert.equal(tsconfig.compilerOptions.target, 'ES2022', 'Should target ES2022')
    assert.equal(tsconfig.compilerOptions.module, 'ESNext', 'Should use ESNext modules')
    assert.equal(tsconfig.compilerOptions.strict, true, 'Should have strict mode enabled')
    
    console.log('✅ TypeScript configuration validated')
  })
  
  await t.test('TypeScript types and interfaces work', () => {
    // Test interface usage
    assert.ok(validateConfig(projectConfig), 'Config validation should work')
    
    // Test type inference
    const numbers: number[] = [1, 2, 3, 4, 5]
    const doubled = numbers.map((n: number): number => n * 2)
    assert.deepEqual(doubled, [2, 4, 6, 8, 10], 'Array mapping with types should work')
    
    // Test union types
    const mixedValue: string | number = 'test'
    assert.equal(typeof mixedValue, 'string', 'Union types should work')
    
    console.log('✅ TypeScript types and interfaces working')
  })
  
  await t.test('Modern JavaScript features work with TypeScript', async () => {
    // Test async/await
    const result = await asyncTest()
    assert.equal(result, 'TypeScript async works!', 'Async/await should work')
    
    // Test destructuring with types
    const { name, version }: { name: string; version: string } = projectConfig
    assert.equal(name, 'corporate-list-scraper', 'Destructuring should work')
    assert.ok(version.includes('.'), 'Version should be valid')
    
    // Test optional chaining and nullish coalescing
    const testObj: { deep?: { value?: string } } = { deep: { value: 'test' } }
    const value = testObj?.deep?.value ?? 'default'
    assert.equal(value, 'test', 'Optional chaining should work')
    
    // Test template literals
    const templateTest = `Project: ${name} v${version}`
    assert.ok(templateTest.includes(name), 'Template literals should work')
    
    console.log('✅ Modern JavaScript features working with TypeScript')
  })
  
  await t.test('Node.js built-in modules work with TypeScript', () => {
    // Test that Node.js types are available
    const nodeVersion: string = process.version
    assert.ok(nodeVersion.startsWith('v'), 'Node.js version should be available')
    
    // Test file system operations with types
    const packageJsonExists: boolean = existsSync(join(projectRoot, 'package.json'))
    assert.ok(packageJsonExists, 'File system operations should work')
    
    // Test path operations
    const testPath: string = join(__dirname, 'test-file.txt')
    assert.ok(testPath.includes(__dirname), 'Path operations should work')
    
    console.log('✅ Node.js built-in modules working with TypeScript')
  })
  
  await t.test('ES modules work correctly with TypeScript', () => {
    // Test that import.meta is available
    assert.ok(import.meta.url, 'import.meta.url should be available')
    assert.ok(import.meta.url.startsWith('file://'), 'import.meta.url should be file URL')
    
    // Test that __filename and __dirname work with ES modules
    assert.ok(__filename.endsWith('.ts'), 'Should have correct filename')
    assert.ok(__dirname.includes('test'), 'Should have correct dirname')
    
    console.log('✅ ES modules working correctly with TypeScript')
  })
  
})

// Summary
console.log('\n📋 TypeScript Environment Test Summary:')
console.log(`📁 Test file: ${__filename}`)
console.log(`🎯 Verifies: TypeScript config, types, modern JS, Node.js modules, ES modules`)
console.log(`✨ TypeScript environment is ready for development`)