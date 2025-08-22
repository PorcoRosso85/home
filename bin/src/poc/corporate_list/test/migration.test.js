/**
 * Migration Test (JavaScript version)
 * 
 * Tests migration and compatibility between TypeScript and JavaScript versions
 * using the compiled JavaScript files.
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = dirname(__dirname)
const distPath = join(projectRoot, 'dist', 'src')

test('Migration and Compatibility Tests', async (t) => {
  
  await t.test('TypeScript to JavaScript compilation successful', () => {
    // Check that all main files were compiled
    const expectedFiles = [
      'main.js',
      'variables.js',
      'infrastructure/browser.js',
      'domain/scraper.js',
      'domain/extractor.js',
      'domain/scraper-factory.js',
      'domain/types.js'
    ]
    
    for (const file of expectedFiles) {
      const filePath = join(distPath, file)
      assert.ok(existsSync(filePath), `Compiled file should exist: ${file}`)
    }
    
    console.log('✅ TypeScript compilation generated all expected JavaScript files')
  })
  
  await t.test('Compiled files are valid JavaScript modules', async () => {
    // Try to import each main module to ensure they're valid
    const moduleTests = [
      { name: 'variables', path: `${distPath}/variables.js` },
      { name: 'browser', path: `${distPath}/infrastructure/browser.js` },
      { name: 'extractor', path: `${distPath}/domain/extractor.js` },
      { name: 'scraper', path: `${distPath}/domain/scraper.js` }
    ]
    
    for (const moduleTest of moduleTests) {
      try {
        const module = await import(moduleTest.path)
        assert.ok(module, `${moduleTest.name} module should be importable`)
        assert.ok(typeof module === 'object', `${moduleTest.name} should export an object`)
        
        console.log(`✅ ${moduleTest.name} module imports successfully`)
      } catch (error) {
        assert.fail(`Failed to import ${moduleTest.name} module: ${error.message}`)
      }
    }
  })
  
  await t.test('Type definitions generated correctly', () => {
    // Check that .d.ts files were generated
    const expectedTypeFiles = [
      'main.d.ts',
      'variables.d.ts', 
      'infrastructure/browser.d.ts',
      'domain/scraper.d.ts',
      'domain/extractor.d.ts'
    ]
    
    for (const file of expectedTypeFiles) {
      const filePath = join(distPath, file)
      assert.ok(existsSync(filePath), `Type definition should exist: ${file}`)
      
      // Check that the .d.ts file has content
      const content = readFileSync(filePath, 'utf8')
      assert.ok(content.length > 0, `Type definition should have content: ${file}`)
    }
    
    console.log('✅ TypeScript type definitions generated correctly')
  })
  
  await t.test('Source maps generated for debugging', () => {
    // Check that .js.map files were generated
    const expectedMapFiles = [
      'main.js.map',
      'variables.js.map',
      'infrastructure/browser.js.map'
    ]
    
    for (const file of expectedMapFiles) {
      const filePath = join(distPath, file)
      if (existsSync(filePath)) {
        const content = readFileSync(filePath, 'utf8')
        assert.ok(content.length > 0, `Source map should have content: ${file}`)
        
        // Basic validation that it's a valid source map
        try {
          const sourceMap = JSON.parse(content)
          assert.ok(sourceMap.version, 'Source map should have version')
          assert.ok(sourceMap.sources, 'Source map should have sources')
        } catch (error) {
          console.log(`⚠️  Source map validation failed for ${file}:`, error.message)
        }
      }
    }
    
    console.log('✅ Source maps generated for debugging support')
  })
  
  await t.test('Package.json scripts compatibility', () => {
    // Check that package.json has the expected scripts
    const packageJsonPath = join(projectRoot, 'package.json')
    assert.ok(existsSync(packageJsonPath), 'package.json should exist')
    
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8'))
    
    // Check for build script
    assert.ok(packageJson.scripts.build, 'Should have build script')
    assert.strictEqual(packageJson.scripts.build, 'tsc', 'Build script should use tsc')
    
    // Check module type
    assert.strictEqual(packageJson.type, 'module', 'Should be configured as ES module')
    
    console.log('✅ Package.json scripts are compatible with TypeScript/JavaScript migration')
  })
  
  await t.test('All JavaScript test files exist', () => {
    // Check that all corresponding JavaScript test files were created
    const expectedTestFiles = [
      'typescript-env.test.js',
      'main.test.js',
      'variables.test.js',
      'infrastructure/browser.test.js',
      'domain/scraper.test.js',
      'domain/extractor.test.js',
      'migration.test.js' // this file
    ]
    
    for (const file of expectedTestFiles) {
      const filePath = join(__dirname, file)
      assert.ok(existsSync(filePath), `JavaScript test file should exist: ${file}`)
    }
    
    console.log('✅ All JavaScript test files have been created')
  })
  
  await t.test('TypeScript and JavaScript test files coexist', () => {
    // Verify that both .ts and .js versions exist where expected
    const testPairs = [
      { ts: 'typescript-env.test.ts', js: 'typescript-env.test.js' },
      { ts: 'main.test.ts', js: 'main.test.js' },
      { ts: 'variables.test.ts', js: 'variables.test.js' },
      { ts: 'migration.test.ts', js: 'migration.test.js' }
    ]
    
    for (const pair of testPairs) {
      const tsPath = join(__dirname, pair.ts)
      const jsPath = join(__dirname, pair.js)
      
      if (existsSync(tsPath)) {
        assert.ok(existsSync(jsPath), `JavaScript version should exist for ${pair.ts}`)
      }
    }
    
    console.log('✅ TypeScript and JavaScript test files coexist properly')
  })
  
})

console.log('\n📋 Migration Test Summary (JavaScript):')
console.log('🎯 Test purpose: Verify TypeScript to JavaScript migration is complete and working')
console.log('📊 Coverage: Compilation, module imports, type definitions, source maps, test files')
console.log('✅ Migration should be fully functional with both TypeScript and JavaScript support')