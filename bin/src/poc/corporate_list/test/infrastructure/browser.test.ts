/**
 * Unit tests for BrowserManager infrastructure (TypeScript version)
 * Tests browser lifecycle management and error handling using TypeScript with Bun test
 */

import { test, expect, describe } from 'bun:test'
import { execSync } from 'child_process'
import type { Browser } from 'playwright-core'
import { BrowserManager, BrowserError, createBrowserManager } from '../../src/infrastructure/browser'
import { BROWSER_CONFIG } from '../../src/variables'

// Test configuration similar to production but with shorter timeouts
const testBrowserConfig = {
  ...BROWSER_CONFIG,
  timeout: 10000,
  waitTime: 1000
}

describe('BrowserManager (TypeScript)', () => {

  test('should create BrowserManager instance with factory function', () => {
    const manager = createBrowserManager(testBrowserConfig)
    
    expect(manager).toBeInstanceOf(BrowserManager)
    expect(manager.isLaunched()).toBe(false)
    expect(manager.getBrowser()).toBe(null)
  })

  test('should handle chromium detection correctly', async () => {
    const manager = new BrowserManager(testBrowserConfig)
    
    // Test that chromium path detection works in nix environment
    try {
      const chromiumPath = execSync('which chromium', { encoding: 'utf-8' }).trim()
      expect(chromiumPath.length).toBeGreaterThan(0)
      expect(chromiumPath).toContain('chromium')
    } catch (error) {
      // If chromium is not available, the BrowserManager should throw BrowserError
      try {
        await manager.launch()
        expect(true).toBe(false) // Should not reach here
      } catch (browserError) {
        expect(browserError).toBeInstanceOf(BrowserError)
        expect((browserError as BrowserError).message).toContain('Could not find chromium')
      }
    }
  })

  test('should launch browser with correct configuration', async () => {
    const manager = new BrowserManager(testBrowserConfig)
    let browser: Browser | null = null
    
    try {
      // Test launching browser
      browser = await manager.launch()
      
      expect(browser).toBeDefined()
      expect(manager.isLaunched()).toBe(true)
      expect(manager.getBrowser()).toBe(browser)
      
      // Test that launching again returns same instance
      const browser2 = await manager.launch()
      expect(browser).toBe(browser2)
      
    } catch (error) {
      // If we're not in a nix environment with chromium, skip this test
      if (error instanceof BrowserError && error.message.includes('Could not find chromium')) {
        console.log('⚠️ Chromium not available - skipping browser launch test')
        return
      }
      throw error
    } finally {
      await manager.close()
    }
  })

  test('should handle browser close correctly', async () => {
    const manager = new BrowserManager(testBrowserConfig)
    
    // Test closing when not launched
    await manager.close() // Should not throw
    expect(manager.isLaunched()).toBe(false)
    
    try {
      // Test closing after launch
      await manager.launch()
      expect(manager.isLaunched()).toBe(true)
      
      await manager.close()
      expect(manager.isLaunched()).toBe(false)
      expect(manager.getBrowser()).toBe(null)
      
    } catch (error) {
      // Skip if chromium not available
      if (error instanceof BrowserError && error.message.includes('Could not find chromium')) {
        console.log('⚠️ Chromium not available - skipping browser close test')
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
        expect(error.message).toContain('Failed to launch browser')
        expect(manager.isLaunched()).toBe(false)
        expect(manager.getBrowser()).toBe(null)
      } else {
        // Re-throw if it's not the expected error type
        throw error
      }
    }
  })

  test('should have proper error types and inheritance', () => {
    const error = new BrowserError('Test error')
    
    expect(error).toBeInstanceOf(Error)
    expect(error).toBeInstanceOf(BrowserError)
    expect(error.name).toBe('BrowserError')
    expect(error.message).toBe('Test error')
    
    // Test with cause
    const cause = new Error('Root cause')
    const errorWithCause = new BrowserError('Test error with cause', cause)
    expect(errorWithCause.cause).toBe(cause)
  })

  test('should handle multiple close calls without errors', async () => {
    const manager = new BrowserManager(testBrowserConfig)
    
    try {
      // Launch browser
      await manager.launch()
      
      // Close multiple times - should not throw
      await manager.close()
      await manager.close()
      await manager.close()
      
      expect(manager.isLaunched()).toBe(false)
      
    } catch (error) {
      // Skip if chromium not available
      if (error instanceof BrowserError && error.message.includes('Could not find chromium')) {
        console.log('⚠️ Chromium not available - skipping multiple close test')
        return
      }
      throw error
    }
  })

  test('should import correctly from TypeScript', () => {
    // Test that we can import all needed exports from TypeScript
    expect(typeof BrowserManager).toBe('function')
    expect(typeof BrowserError).toBe('function')
    expect(typeof createBrowserManager).toBe('function')
    
    console.log('✅ Browser module imports correctly from TypeScript')
  })

})

describe('BrowserManager Integration (TypeScript)', () => {

  test('should work with configuration from TypeScript variables', () => {
    const manager = createBrowserManager(BROWSER_CONFIG)
    
    expect(manager).toBeInstanceOf(BrowserManager)
    expect(manager.isLaunched()).toBe(false)
  })

  test('should maintain consistent interface', () => {
    const manager = createBrowserManager(testBrowserConfig)
    
    // Verify interface methods exist
    expect(typeof manager.launch).toBe('function')
    expect(typeof manager.close).toBe('function')
    expect(typeof manager.isLaunched).toBe('function')
    expect(typeof manager.getBrowser).toBe('function')
  })

  test('should maintain configuration compatibility', () => {
    // Test that the TypeScript configuration works with BrowserManager
    expect(typeof BROWSER_CONFIG).toBe('object')
    expect(typeof BROWSER_CONFIG.userAgent).toBe('string')
    expect(typeof BROWSER_CONFIG.timeout).toBe('number')
    expect(Array.isArray(BROWSER_CONFIG.launchArgs)).toBe(true)
    
    const manager = new BrowserManager(BROWSER_CONFIG)
    expect(manager).toBeInstanceOf(BrowserManager)
    
    console.log('✅ Configuration compatibility maintained in TypeScript')
  })

})

console.log('\n📋 Browser Infrastructure Test Summary (TypeScript):')
console.log('🎯 Test purpose: Verify TypeScript browser infrastructure works correctly')
console.log('📊 Coverage: Browser lifecycle, error handling, configuration integration')
console.log('✅ All TypeScript browser functionality should work correctly')