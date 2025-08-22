/**
 * Unit tests for BrowserManager infrastructure (JavaScript version)
 * Tests browser lifecycle management and error handling using compiled JS
 */

import { test, describe } from 'node:test'
import { strict as assert } from 'node:assert'
import { execSync } from 'child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = dirname(dirname(__dirname))
const distPath = join(projectRoot, 'dist', 'src')

// Import compiled JavaScript modules
const browserModule = await import(`${distPath}/infrastructure/browser.js`)
const variablesModule = await import(`${distPath}/variables.js`)

const { BrowserManager, BrowserError, createBrowserManager } = browserModule
const { BROWSER_CONFIG } = variablesModule

// Test configuration similar to production but with shorter timeouts
const testBrowserConfig = {
  ...BROWSER_CONFIG,
  timeout: 10000,
  waitTime: 1000
}

describe('BrowserManager (Compiled JavaScript)', () => {

  test('should create BrowserManager instance with factory function', () => {
    const manager = createBrowserManager(testBrowserConfig)
    
    assert.ok(manager instanceof BrowserManager, 'Should create BrowserManager instance')
    assert.strictEqual(manager.isLaunched(), false, 'Should start with browser not launched')
    assert.strictEqual(manager.getBrowser(), null, 'Should return null browser initially')
  })

  test('should handle chromium detection correctly', async () => {
    const manager = new BrowserManager(testBrowserConfig)
    
    // Test that chromium path detection works in nix environment
    try {
      const chromiumPath = execSync('which chromium', { encoding: 'utf-8' }).trim()
      assert.ok(chromiumPath.length > 0, 'Should find chromium executable')
      assert.ok(chromiumPath.includes('chromium'), 'Path should contain chromium')
    } catch (error) {
      // If chromium is not available, the BrowserManager should throw BrowserError
      try {
        await manager.launch()
        assert.fail('Should have thrown BrowserError when chromium not available')
      } catch (browserError) {
        assert.ok(browserError instanceof BrowserError, 'Should throw BrowserError')
        assert.ok(browserError.message.includes('Could not find chromium'), 'Should have meaningful error message')
      }
    }
  })

  test('should launch browser with correct configuration', async (t) => {
    const manager = new BrowserManager(testBrowserConfig)
    
    try {
      // Test launching browser
      const browser = await manager.launch()
      
      assert.ok(browser, 'Should return browser instance')
      assert.strictEqual(manager.isLaunched(), true, 'Should report browser as launched')
      assert.strictEqual(manager.getBrowser(), browser, 'Should return same browser instance')
      
      // Test that launching again returns same instance
      const browser2 = await manager.launch()
      assert.strictEqual(browser, browser2, 'Should return same browser instance on second launch')
      
    } catch (error) {
      // If we're not in a nix environment with chromium, skip this test
      if (error instanceof BrowserError && error.message.includes('Could not find chromium')) {
        t.skip('Chromium not available - skipping browser launch test')
        return
      }
      throw error
    } finally {
      await manager.close()
    }
  })

  test('should handle browser close correctly', async (t) => {
    const manager = new BrowserManager(testBrowserConfig)
    
    // Test closing when not launched
    await manager.close() // Should not throw
    assert.strictEqual(manager.isLaunched(), false, 'Should remain not launched')
    
    try {
      // Test closing after launch
      await manager.launch()
      assert.strictEqual(manager.isLaunched(), true, 'Should be launched')
      
      await manager.close()
      assert.strictEqual(manager.isLaunched(), false, 'Should be closed')
      assert.strictEqual(manager.getBrowser(), null, 'Should return null after close')
      
    } catch (error) {
      // Skip if chromium not available
      if (error instanceof BrowserError && error.message.includes('Could not find chromium')) {
        t.skip('Chromium not available - skipping browser close test')
        return
      }
      throw error
    }
  })

  test('should handle browser launch errors gracefully', async () => {
    // Create manager with invalid configuration to force launch failure
    const invalidConfig = {
      ...testBrowserConfig,
      launchArgs: ['--invalid-arg-that-should-cause-failure', ...testBrowserConfig.launchArgs]
    }
    
    const manager = new BrowserManager(invalidConfig)
    
    try {
      await manager.launch()
      // If launch succeeds despite invalid args, just verify state
      await manager.close()
    } catch (error) {
      // Should throw BrowserError for launch failures
      if (error instanceof BrowserError) {
        assert.ok(error.message.includes('Failed to launch browser'), 'Should have meaningful error message')
        assert.strictEqual(manager.isLaunched(), false, 'Should not be marked as launched on failure')
        assert.strictEqual(manager.getBrowser(), null, 'Should not have browser reference on failure')
      } else {
        // Re-throw if it's not the expected error type
        throw error
      }
    }
  })

  test('should have proper error types and inheritance', () => {
    const error = new BrowserError('Test error')
    
    assert.ok(error instanceof Error, 'BrowserError should extend Error')
    assert.ok(error instanceof BrowserError, 'Should be instance of BrowserError')
    assert.strictEqual(error.name, 'BrowserError', 'Should have correct name')
    assert.strictEqual(error.message, 'Test error', 'Should preserve message')
    
    // Test with cause
    const cause = new Error('Root cause')
    const errorWithCause = new BrowserError('Test error with cause', cause)
    assert.strictEqual(errorWithCause.cause, cause, 'Should preserve cause')
  })

  test('should handle multiple close calls without errors', async (t) => {
    const manager = new BrowserManager(testBrowserConfig)
    
    try {
      // Launch browser
      await manager.launch()
      
      // Close multiple times - should not throw
      await manager.close()
      await manager.close()
      await manager.close()
      
      assert.strictEqual(manager.isLaunched(), false, 'Should remain closed')
      
    } catch (error) {
      // Skip if chromium not available
      if (error instanceof BrowserError && error.message.includes('Could not find chromium')) {
        t.skip('Chromium not available - skipping multiple close test')
        return
      }
      throw error
    }
  })

  test('should import correctly from compiled JavaScript', () => {
    // Test that we can import all needed exports from compiled JS
    assert.ok(typeof BrowserManager === 'function', 'BrowserManager should be importable')
    assert.ok(typeof BrowserError === 'function', 'BrowserError should be importable')
    assert.ok(typeof createBrowserManager === 'function', 'createBrowserManager should be importable')
    
    console.log('✅ Browser module imports correctly from compiled JavaScript')
  })

})

describe('BrowserManager Integration (Compiled JavaScript)', () => {

  test('should work with configuration from compiled variables.js', () => {
    const manager = createBrowserManager(BROWSER_CONFIG)
    
    assert.ok(manager instanceof BrowserManager, 'Should create manager with production config')
    assert.strictEqual(manager.isLaunched(), false, 'Should start not launched')
  })

  test('should maintain consistent interface', () => {
    const manager = createBrowserManager(testBrowserConfig)
    
    // Verify interface methods exist
    assert.ok(typeof manager.launch === 'function', 'Should have launch method')
    assert.ok(typeof manager.close === 'function', 'Should have close method')
    assert.ok(typeof manager.isLaunched === 'function', 'Should have isLaunched method')
    assert.ok(typeof manager.getBrowser === 'function', 'Should have getBrowser method')
  })

  test('should maintain configuration compatibility', () => {
    // Test that the compiled configuration works with BrowserManager
    assert.ok(typeof BROWSER_CONFIG === 'object', 'BROWSER_CONFIG should be available')
    assert.ok(typeof BROWSER_CONFIG.userAgent === 'string', 'userAgent should be string')
    assert.ok(typeof BROWSER_CONFIG.timeout === 'number', 'timeout should be number')
    assert.ok(Array.isArray(BROWSER_CONFIG.launchArgs), 'launchArgs should be array')
    
    const manager = new BrowserManager(BROWSER_CONFIG)
    assert.ok(manager instanceof BrowserManager, 'Should create manager with compiled config')
    
    console.log('✅ Configuration compatibility maintained in compiled JavaScript')
  })

})

console.log('\n📋 Browser Infrastructure Test Summary (JavaScript):')
console.log('🎯 Test purpose: Verify compiled browser infrastructure works correctly')
console.log('📊 Coverage: Browser lifecycle, error handling, configuration integration')
console.log('✅ All compiled browser functionality should work correctly')