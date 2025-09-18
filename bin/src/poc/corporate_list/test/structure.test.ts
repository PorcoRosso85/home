/**
 * Structure Test - 外部パッケージ化後の構造確認
 */

import { describe, expect, it } from 'bun:test'
import { existsSync } from 'fs'
import { join } from 'path'

describe('External Package Structure', () => {
  it('スクレイパーが外部パッケージとして存在する', () => {
    const scraperPath = join(process.cwd(), '..', 'scrape_ts')
    expect(existsSync(scraperPath)).toBe(true)
    
    // flake.nixの存在確認
    expect(existsSync(join(scraperPath, 'flake.nix'))).toBe(true)
    
    // パッケージディレクトリの存在確認
    expect(existsSync(join(scraperPath, 'scraper-core'))).toBe(true)
    expect(existsSync(join(scraperPath, 'scraper-prtimes'))).toBe(true)
  })
  
  it('corporate_listがユースケース層として機能する', () => {
    // インフラストラクチャ層の存在確認
    const infraPath = join(process.cwd(), 'src', 'infrastructure')
    expect(existsSync(infraPath)).toBe(true)
    expect(existsSync(join(infraPath, 'scraper-client.ts'))).toBe(true)
    expect(existsSync(join(infraPath, 'browser.ts'))).toBe(true)
    
    // main.tsの存在確認
    expect(existsSync(join(process.cwd(), 'src', 'main.ts'))).toBe(true)
  })
  
  it('インポートパスが正しく設定されている', async () => {
    // scraper-client.tsをインポートしてエラーがないことを確認
    try {
      const module = await import('../src/infrastructure/scraper-client.js')
      expect(module.createPRTimesScraperClient).toBeDefined()
    } catch (error) {
      // インポートエラーの詳細を表示
      console.error('Import error:', error)
      throw error
    }
  })
})