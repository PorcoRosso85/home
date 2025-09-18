/**
 * Browser infrastructure layer
 * Manages browser lifecycle and provides centralized browser configuration
 */

import { chromium, Browser } from 'playwright-core'
import { execSync } from 'child_process'
import { type ScraperConfig } from '../variables.js'

/**
 * Browser management interface
 */
export interface IBrowserManager {
  launch(): Promise<Browser>
  close(): Promise<void>
  isLaunched(): boolean
}

/**
 * Error thrown when browser operations fail
 */
export class BrowserError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message)
    this.name = 'BrowserError'
  }
}

/**
 * Browser Manager class for handling browser lifecycle
 * Provides centralized browser initialization, configuration, and cleanup
 */
export class BrowserManager implements IBrowserManager {
  private browser: Browser | null = null
  private readonly config: ScraperConfig['browser']

  constructor(config: ScraperConfig['browser']) {
    this.config = config
  }

  /**
   * Detect chromium executable path using system which command
   * @returns Path to chromium executable
   * @throws {BrowserError} When chromium is not found
   */
  private getChromiumPath(): string {
    try {
      const path = execSync('which chromium', { encoding: 'utf-8' }).trim()
      console.log('🔧 Using chromium at:', path)
      return path
    } catch (error) {
      throw new BrowserError(
        'Could not find chromium. Run in nix shell.',
        error instanceof Error ? error : new Error(String(error))
      )
    }
  }

  /**
   * Launch browser with proper configuration
   * @returns Promise resolving to Browser instance
   * @throws {BrowserError} When browser launch fails
   */
  async launch(): Promise<Browser> {
    if (this.browser) {
      console.log('✅ Browser already launched')
      return this.browser
    }

    try {
      const chromiumPath = this.getChromiumPath()
      
      this.browser = await chromium.launch({
        executablePath: chromiumPath,
        headless: true,
        args: this.config.launchArgs
      })

      console.log('✅ Browser launched')
      return this.browser
    } catch (error) {
      const browserError = new BrowserError(
        'Failed to launch browser',
        error instanceof Error ? error : new Error(String(error))
      )
      
      // Clean up browser reference on failure
      this.browser = null
      throw browserError
    }
  }

  /**
   * Close browser and cleanup resources
   * @returns Promise that resolves when browser is closed
   */
  async close(): Promise<void> {
    if (!this.browser) {
      return
    }

    try {
      await this.browser.close()
      console.log('✅ Browser closed')
    } catch (error) {
      console.error('⚠️  Error closing browser:', error instanceof Error ? error.message : String(error))
      // Continue cleanup even if close fails
    } finally {
      this.browser = null
    }
  }

  /**
   * Check if browser is currently launched
   * @returns true if browser is launched and ready
   */
  isLaunched(): boolean {
    return this.browser !== null
  }

  /**
   * Get the current browser instance
   * @returns Browser instance or null if not launched
   */
  getBrowser(): Browser | null {
    return this.browser
  }
}

/**
 * Factory function to create a configured BrowserManager instance
 * @param config Browser configuration from ScraperConfig
 * @returns New BrowserManager instance
 */
export function createBrowserManager(config: ScraperConfig['browser']): BrowserManager {
  return new BrowserManager(config)
}