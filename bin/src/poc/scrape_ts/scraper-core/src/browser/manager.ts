/**
 * Browser管理（関数型実装）
 * 高階関数パターンで依存性注入を実現
 * 
 * @see bin/docs/conventions/dependency_management.md - 高階関数パターン
 * @see bin/docs/conventions/tdd_process.md - 関数型スタイル
 */

import { chromium, type Browser } from 'playwright-core'
import { execSync } from 'child_process'
import { type BrowserConfig, type BrowserManager, DEFAULT_BROWSER_CONFIG } from '../types.js'

/**
 * Chromium実行ファイルのパスを検出する（純粋関数）
 * @returns Chromiumのパス、見つからない場合はnull
 */
export const getChromiumPath = (): string | null => {
  try {
    const path = execSync('which chromium', { encoding: 'utf-8' }).trim()
    console.log('🔧 Using chromium at:', path)
    return path
  } catch (error) {
    console.error('⚠️  Could not find chromium. Run in nix shell.', error)
    return null
  }
}

/**
 * Browser起動の高階関数
 * 設定を受け取り、Browser起動関数を返す
 */
export const createBrowserLauncher = (config: BrowserConfig = DEFAULT_BROWSER_CONFIG) => {
  return async (): Promise<Browser | null> => {
    const chromiumPath = getChromiumPath()
    
    if (!chromiumPath) {
      // エラーを投げずにnullを返す（規約準拠）
      return null
    }

    try {
      const browser = await chromium.launch({
        executablePath: chromiumPath,
        headless: true,
        args: config.launchArgs
      })

      console.log('✅ Browser launched')
      return browser
    } catch (error) {
      console.error('⚠️  Failed to launch browser:', error)
      // エラーを投げずにnullを返す（規約準拠）
      return null
    }
  }
}

/**
 * Browser管理器を作成する高階関数
 * 設定を受け取り、BrowserManagerインスタンスを返す
 */
export const createBrowserManager = (config: BrowserConfig = DEFAULT_BROWSER_CONFIG): BrowserManager => {
  let browser: Browser | null = null
  const launchBrowser = createBrowserLauncher(config)

  return {
    launch: async (): Promise<Browser> => {
      if (browser) {
        console.log('✅ Browser already launched')
        return browser
      }

      const newBrowser = await launchBrowser()
      if (!newBrowser) {
        throw new Error('Failed to launch browser - chromium not found or launch failed')
      }

      browser = newBrowser
      return browser
    },

    close: async (): Promise<void> => {
      if (!browser) {
        return
      }

      try {
        await browser.close()
        console.log('✅ Browser closed')
      } catch (error) {
        console.error('⚠️  Error closing browser:', error instanceof Error ? error.message : String(error))
        // エラーが発生してもクリーンアップは続行
      } finally {
        browser = null
      }
    },

    isLaunched: (): boolean => {
      return browser !== null
    }
  }
}

/**
 * Browser操作の高階関数コンポーザー
 * BrowserManagerを受け取り、操作を実行する関数を返す
 */
export const withBrowser = <T>(
  manager: BrowserManager,
  operation: (browser: Browser) => Promise<T>
) => async (): Promise<T | null> => {
  try {
    const browser = await manager.launch()
    const result = await operation(browser)
    await manager.close()
    return result
  } catch (error) {
    console.error('⚠️  Browser operation failed:', error)
    await manager.close()
    // エラーを投げずにnullを返す（規約準拠）
    return null
  }
}

/**
 * 使用例とテスト用のヘルパー関数
 */
export const createMockBrowser = (): Browser => {
  return {} as Browser
}